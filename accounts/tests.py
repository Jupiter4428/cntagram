import time

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .forms import LoginForm
from .models import Role, UserRole
from .services import is_login_rate_limited

User = get_user_model()


class AuthenticationViewsTests(TestCase):
    password = "correct-horse-battery-staple"
    wrong_password = "wrong-password"

    @classmethod
    def setUpTestData(cls):
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

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def post_login(self, password=None, *, client=None, username=None, **extra):
        """POST to the login view as self.user (correct password by default).

        `extra` keys that are valid form data (e.g. `next`) go into the POST body;
        anything uppercase (e.g. REMOTE_ADDR) is passed to the test client.
        """
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

    def test_login_form_extends_django_authentication_form(self):
        self.assertTrue(issubclass(LoginForm, AuthenticationForm))

    def test_guest_can_access_public_pages(self):
        for url_name in ("accounts:home", "accounts:login", "accounts:register"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_guest_is_redirected_from_vault_to_login(self):
        vault_url = reverse("materials:vault")

        response = self.client.get(vault_url)

        expected = f"{reverse('accounts:login')}?next={vault_url}"
        self.assertRedirects(response, expected)

    def test_successful_login_creates_session_and_redirects_home(self):
        response = self.post_login(username=self.user.email.upper())

        self.assertRedirects(response, reverse("accounts:home"))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.assertEqual(self.client.get(reverse("materials:vault")).status_code, 200)

    def test_failed_login_does_not_authenticate_user(self):
        response = self.post_login(self.wrong_password)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(response, "Please enter a correct")

    def test_login_honors_safe_internal_next_url(self):
        response = self.post_login(next=reverse("materials:vault"))

        self.assertRedirects(response, reverse("materials:vault"))

    def test_login_rejects_external_next_url(self):
        response = self.post_login(next="https://attacker.example/phishing")

        self.assertRedirects(response, reverse("accounts:home"))

    def test_logout_requires_post_and_invalidates_session(self):
        self.client.force_login(self.user)
        self.assertIn(SESSION_KEY, self.client.session)

        get_response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(post_response, reverse("accounts:home"))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertRedirects(
            self.client.get(reverse("materials:vault")),
            f"{reverse('accounts:login')}?next={reverse('materials:vault')}",
        )

    def test_logout_is_csrf_protected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 403)
        self.assertIn(SESSION_KEY, csrf_client.session)

    def test_login_is_csrf_protected(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = self.post_login(client=csrf_client)

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, csrf_client.session)

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


class AccountsAdminTests(TestCase):
    """Django admin ของ accounts (TD-3)"""

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )
        cls.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin-password",
            nickname="Admin",
            department=cls.department,
        )
        cls.student = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="student-password",
            nickname="Student",
            department=cls.department,
            pdpa_consent_at=timezone.now(),
        )
        cls.moderator = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลภาค"}
        )[0]

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist_opens_for_every_accounts_model(self):
        for model in ("user", "role", "userrole"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:accounts_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_user_change_page_hides_password_and_shows_student_id_read_only(self):
        response = self.client.get(
            reverse("admin:accounts_user_change", args=[self.student.pk])
        )

        form = response.context["adminform"].form
        self.assertNotIn("password", form.fields)
        self.assertNotContains(response, self.student.password)
        self.assertIn("nickname", form.fields)
        self.assertIn("department", form.fields)
        self.assertNotIn("student_id", form.fields)
        self.assertContains(response, "6610000000")

    def test_user_cannot_be_added_through_admin(self):
        response = self.client.get(reverse("admin:accounts_user_add"))

        self.assertEqual(response.status_code, 403)

    def _make_student_in_new_department(self, n):
        department = Department.objects.create(
            code=f"D{n}", name_th=f"ภาค {n}", name_en=f"Department {n}"
        )
        return User.objects.create_user(
            email=f"66100000{n:02d}@student.tu.ac.th",
            password="student-password",
            nickname=f"Student {n}",
            department=department,
            pdpa_consent_at=timezone.now(),
        )

    def test_user_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            self._make_student_in_new_department(n)

        with self.assertNumQueries(6):
            self.client.get(reverse("admin:accounts_user_changelist"))

    def test_userrole_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            student = self._make_student_in_new_department(n)
            UserRole.objects.create(
                user=student,
                role=self.moderator,
                department=student.department,
                granted_by=self.superuser,
            )

        with self.assertNumQueries(7):
            self.client.get(reverse("admin:accounts_userrole_changelist"))

    def test_admin_rejects_moderator_role_without_department(self):
        response = self.client.post(
            reverse("admin:accounts_userrole_add"),
            {"user": self.student.pk, "role": self.moderator.pk, "department": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("department", response.context["adminform"].form.errors)
        self.assertFalse(UserRole.objects.filter(user=self.student).exists())

    def test_admin_rejects_non_student_email_for_student(self):
        response = self.client.post(
            reverse("admin:accounts_user_change", args=[self.student.pk]),
            {
                "email": "student@gmail.com",
                "nickname": "Student",
                "department": self.department.pk,
                "is_active": "on",
            },
        )

        self.assertIn("email", response.context["adminform"].form.errors)
        self.student.refresh_from_db()
        self.assertEqual(self.student.email, "6610000000@student.tu.ac.th")

    def test_user_change_page_query_count_is_fixed(self):
        with self.assertNumQueries(4):
            self.client.get(reverse("admin:accounts_user_change", args=[self.student.pk]))

    def test_user_cannot_be_deleted_through_admin(self):
        response = self.client.get(
            reverse("admin:accounts_user_delete", args=[self.student.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())
