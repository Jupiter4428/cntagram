from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .. import services
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

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=5,
        LOGIN_RATE_LIMIT_IP_ATTEMPTS=6,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_password_spraying_from_single_ip_is_rate_limited(self):
        client_ip = "198.51.100.1"
        # IP เดียวลองผิดกับ 6 บัญชีที่ต่างกัน
        # (ครั้งละ 1 ครั้ง ไม่ถึงเพดานต่อบัญชี 5 ครั้ง)
        for i in range(6):
            username = f"66100000{i:02d}@student.tu.ac.th"
            response = self.post_login(
                self.wrong_password, username=username, REMOTE_ADDR=client_ip
            )
            self.assertEqual(response.status_code, 200)

        # ครั้งที่ 7 จาก IP เดิมโดนบล็อกด้วย 429 ไม่ว่าจะลองบัญชีใดก็ตาม
        response = self.post_login(
            self.wrong_password,
            username="6610000099@student.tu.ac.th",
            REMOTE_ADDR=client_ip,
        )
        self.assertEqual(response.status_code, 429)

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=3,
        LOGIN_RATE_LIMIT_IP_ATTEMPTS=20,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_single_account_attacked_from_multiple_ips_is_rate_limited(self):
        # บัญชีเดียวโดนลองผิดจาก 3 IP ต่างกัน (IP ละ 1 ครั้ง) จนครบ 3 ครั้ง
        for i in range(3):
            ip = f"198.51.100.{i + 1}"
            response = self.post_login(self.wrong_password, REMOTE_ADDR=ip)
            self.assertEqual(response.status_code, 200)

        # ครั้งถัดไปบนบัญชีนี้จากอีก IP หนึ่งก็ต้องโดนบล็อก
        response = self.post_login(REMOTE_ADDR="198.51.100.99")
        self.assertEqual(response.status_code, 429)

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=5,
        LOGIN_RATE_LIMIT_IP_ATTEMPTS=20,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_successful_login_clears_account_failures(self):
        client_ip = "198.51.100.5"
        for _ in range(3):
            self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)

        # login สำเร็จด้วยรหัสถูกต้อง
        login_res = self.post_login(self.password, REMOTE_ADDR=client_ip)
        self.assertRedirects(login_res, reverse("accounts:home"))

        # ตัวนับของบัญชีถูกล้างแล้ว (ลองจาก IP อื่นต้องไม่โดน rate limit ของบัญชี)
        self.assertFalse(
            is_login_rate_limited(identifier=self.user.email, client_ip="198.51.100.99")
        )

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=5,
        LOGIN_RATE_LIMIT_IP_ATTEMPTS=4,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_successful_login_preserves_ip_failures(self):
        client_ip = "198.51.100.5"
        for _ in range(3):
            self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)

        # login สำเร็จด้วยรหัสถูกต้อง
        login_res = self.post_login(self.password, REMOTE_ADDR=client_ip)
        self.assertRedirects(login_res, reverse("accounts:home"))

        # แต่ตัวนับของ IP ยังไม่ถูกล้าง (สะสมไว้ 3 ครั้ง)
        # ออกจากระบบก่อนเพื่อทดสอบการ login ครั้งถัดไป
        self.client.logout()

        # ลองผิดอีกเพียง 1 ครั้ง IP จะแตะเพดาน 4 ครั้งทันที
        self.post_login(
            self.wrong_password,
            username="other@student.tu.ac.th",
            REMOTE_ADDR=client_ip,
        )
        blocked_res = self.post_login(self.password, REMOTE_ADDR=client_ip)
        self.assertEqual(blocked_res.status_code, 429)

    def test_correct_password_still_logs_in_until_ip_bucket_is_full(self):
        client_ip = "198.51.100.9"
        for i in range(settings.LOGIN_RATE_LIMIT_IP_ATTEMPTS - 1):
            services.record_login_failure(
                identifier=f"spray{i}@student.tu.ac.th", client_ip=client_ip
            )
        ok = self.post_login(self.password, REMOTE_ADDR=client_ip)
        self.assertRedirects(ok, reverse("accounts:home"))

    def test_ip_rate_limit_resets_across_fixed_windows(self):
        client_ip = "198.51.100.10"
        with patch("accounts.services._login_window_index", return_value=100):
            for i in range(settings.LOGIN_RATE_LIMIT_IP_ATTEMPTS):
                services.record_login_failure(
                    identifier=f"w1_{i}@student.tu.ac.th", client_ip=client_ip
                )
            self.assertTrue(
                services.is_login_rate_limited(
                    identifier="user@student.tu.ac.th", client_ip=client_ip
                )
            )

        with patch("accounts.services._login_window_index", return_value=101):
            self.assertFalse(
                services.is_login_rate_limited(
                    identifier="user@student.tu.ac.th", client_ip=client_ip
                )
            )

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3, LOGIN_RATE_LIMIT_IP_ATTEMPTS=20)
    def test_locked_account_does_not_block_other_accounts(self):
        other_user = User.objects.create_user(
            email="6610000002@student.tu.ac.th",
            password=self.password,
            nickname="OtherTester",
            department=self.user.department,
            pdpa_consent_at=timezone.now(),
        )
        for _ in range(3):
            self.post_login(self.wrong_password, REMOTE_ADDR="192.0.2.1")

        response = self.post_login(
            password=self.password, username=other_user.email, REMOTE_ADDR="192.0.2.2"
        )
        self.assertRedirects(response, reverse("accounts:home"))

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3)
    def test_rate_limit_ignores_spoofed_forwarded_for_header(self):
        for i in range(3):
            self.post_login(
                self.wrong_password,
                REMOTE_ADDR="192.0.2.1",
                HTTP_X_FORWARDED_FOR=f"10.0.0.{i}",
            )

        response = self.post_login(
            REMOTE_ADDR="192.0.2.1",
            HTTP_X_FORWARDED_FOR="10.0.0.99",
        )

        self.assertEqual(response.status_code, 429)

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3)
    def test_successful_login_clears_previous_failures(self):
        client_ip = "192.0.2.1"
        for _ in range(2):
            self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)

        self.post_login(REMOTE_ADDR=client_ip)

        self.assertFalse(
            is_login_rate_limited(identifier=self.user.email, client_ip=client_ip)
        )

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=1)
    def test_rate_limit_expires_after_temporary_window(self):
        client_ip = "192.0.2.1"
        with patch("accounts.services._login_window_index", return_value=100):
            self.post_login(self.wrong_password, REMOTE_ADDR=client_ip)
            blocked_response = self.post_login(REMOTE_ADDR=client_ip)
            self.assertEqual(blocked_response.status_code, 429)

        with patch("accounts.services._login_window_index", return_value=101):
            response = self.post_login(REMOTE_ADDR=client_ip)
        self.assertRedirects(response, reverse("accounts:home"))


class RegisterThrottleTests(ThrottleTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("accounts:register")

    @override_settings(
        REGISTER_RATE_LIMIT_ATTEMPTS=2, REGISTER_RATE_LIMIT_WINDOW_SECONDS=90
    )
    def test_register_quota_resets_at_fixed_window_boundary(self):
        ip = "192.0.2.77"
        with patch("accounts.services._register_window_index", return_value=100):
            for _ in range(2):
                self.assertEqual(
                    self.client.post(self.url, {}, REMOTE_ADDR=ip).status_code, 200
                )
            self.assertEqual(
                self.client.post(self.url, {}, REMOTE_ADDR=ip).status_code, 429
            )
        with patch("accounts.services._register_window_index", return_value=101):
            self.assertEqual(
                self.client.post(self.url, {}, REMOTE_ADDR=ip).status_code, 200
            )
            self.assertEqual(
                self.client.post(self.url, {}, REMOTE_ADDR=ip).status_code, 200
            )
            self.assertEqual(
                self.client.post(self.url, {}, REMOTE_ADDR=ip).status_code, 429
            )

    @override_settings(
        REGISTER_RATE_LIMIT_ATTEMPTS=2, REGISTER_RATE_LIMIT_WINDOW_SECONDS=90
    )
    def test_blocks_post_after_quota_with_retry_after(self):
        for _ in range(2):
            self.assertEqual(
                self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10").status_code,
                200,
            )
        response = self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "90")
        self.assertContains(response, "ส่งคำขอสมัครสมาชิกบ่อยเกินไป", status_code=429)

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=1)
    def test_limit_is_per_ip_and_does_not_trust_forwarded_for(self):
        self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.10")
        blocked = self.client.post(
            self.url, {}, REMOTE_ADDR="192.0.2.10", HTTP_X_FORWARDED_FOR="192.0.2.20"
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(
            self.client.post(self.url, {}, REMOTE_ADDR="192.0.2.20").status_code, 200
        )

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=1)
    def test_get_does_not_use_post_quota(self):
        self.client.post(self.url, {})
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.post(self.url, {}).status_code, 429)
