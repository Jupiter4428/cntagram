import time

from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from ..services import is_login_rate_limited
from .base import ThrottleTestCase

User = get_user_model()


class LoginThrottleTests(ThrottleTestCase):
    password = "correct-horse-battery-staple"
    wrong_password = "wrong-password"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        department = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )
        cls.user = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password=cls.password,
            nickname="Tester",
            department=department,
            pdpa_consent_at=timezone.now(),
        )

    def post_login(self, password=None, *, client=None, username=None, **extra):
        data = {
            "username": username or self.user.email,
            "password": self.password if password is None else password,
        }
        request_kwargs = {}
        for key, value in extra.items():
            (request_kwargs if key.isupper() else data)[key] = value
        return (client or self.client).post(
            reverse("accounts:login"), data, **request_kwargs
        )

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=3,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_repeated_failures_temporarily_rate_limit_login(self):
        for _ in range(3):
            response = self.post_login(self.wrong_password, REMOTE_ADDR="192.0.2.1")
            self.assertEqual(response.status_code, 200)

        response = self.post_login(REMOTE_ADDR="192.0.2.1")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "120")
        self.assertContains(
            response,
            "Too many failed login attempts",
            status_code=429,
        )
        self.assertNotIn(SESSION_KEY, self.client.session)

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3)
    def test_rate_limit_is_scoped_by_client_ip(self):
        for _ in range(3):
            self.post_login(self.wrong_password, REMOTE_ADDR="192.0.2.1")

        response = self.post_login(REMOTE_ADDR="192.0.2.2")

        self.assertRedirects(response, reverse("accounts:home"))

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3)
    def test_successful_login_clears_previous_failures(self):
        client_ip = "192.0.2.1"
        for _ in range(2):
            self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)

        self.post_login(REMOTE_ADDR=client_ip)

        self.assertFalse(
            is_login_rate_limited(identifier=self.user.email, client_ip=client_ip)
        )

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=1,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=1,
    )
    def test_rate_limit_expires_after_temporary_window(self):
        client_ip = "192.0.2.1"
        self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)
        blocked_response = self.post_login(REMOTE_ADDR=client_ip)
        self.assertEqual(blocked_response.status_code, 429)

        time.sleep(1.1)
        response = self.post_login(REMOTE_ADDR=client_ip)

        self.assertRedirects(response, reverse("accounts:home"))


class RegisterThrottleTests(ThrottleTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("accounts:register")

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=2, REGISTER_RATE_LIMIT_WINDOW_SECONDS=90)
    def test_blocks_post_after_quota_with_retry_after(self):
        for _ in range(2):
            self.assertEqual(self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10").status_code, 200)
        response = self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "90")
        self.assertContains(response, "ส่งคำขอสมัครสมาชิกบ่อยเกินไป", status_code=429)

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=1)
    def test_limit_is_per_ip_and_does_not_trust_forwarded_for(self):
        self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10")
        blocked = self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10", HTTP_X_FORWARDED_FOR="192.0.2.20")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.20").status_code, 200)

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=1)
    def test_get_does_not_use_post_quota(self):
        self.client.post(self.url, {})
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {}).status_code, 429)
