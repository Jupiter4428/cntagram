import time
from unittest import mock

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .forms import LoginForm, RegisterForm
from .models import Role, UserRole
from .services import is_login_rate_limited, register_user

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


VALID_PASSWORD = "Cn331-Strong-Passw0rd"


class RegistrationTestMixin:
    """ข้อมูลตั้งต้นและ payload ที่ถูกต้องสำหรับทดสอบการสมัครสมาชิก"""

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )
        cls.inactive_department = Department.objects.create(
            code="OLD",
            name_th="ภาคที่ปิดแล้ว",
            name_en="Closed Department",
            is_active=False,
        )

    def payload(self, **overrides):
        data = {
            "email": "6610612345@student.tu.ac.th",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
            "nickname": "Ploy",
            "department": str(self.department.pk),
            "pdpa_consent": "on",
        }
        data.update(overrides)
        return {k: v for k, v in data.items() if v is not None}


class RegisterFormTests(RegistrationTestMixin, TestCase):
    def assertFieldError(self, data, field):
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(field, form.errors)
        return form

    def test_valid_data_normalizes_email(self):
        form = RegisterForm(data=self.payload(email="  6610612345@Student.TU.ac.th "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "6610612345@student.tu.ac.th")

    def test_rejects_non_student_domain(self):
        for email in ("6610612345@gmail.com", "6610612345@tu.ac.th"):
            with self.subTest(email=email):
                self.assertFieldError(self.payload(email=email), "email")

    def test_rejects_local_part_that_is_not_10_digits(self):
        for email in (
            "661061234@student.tu.ac.th",
            "66106123456@student.tu.ac.th",
            "66106abcde@student.tu.ac.th",
            "๖๖๑๐๖๑๒๓๔๕@student.tu.ac.th",
        ):
            with self.subTest(email=email):
                self.assertFieldError(self.payload(email=email), "email")

    def test_rejects_faculty_code_other_than_10(self):
        form = self.assertFieldError(
            self.payload(email="6620612345@student.tu.ac.th"), "email"
        )
        self.assertIn("คณะวิศวกรรมศาสตร์", form.errors["email"][0])

    def test_rejects_duplicate_email(self):
        register_user(
            email="6610612345@student.tu.ac.th",
            password=VALID_PASSWORD,
            nickname="First",
            department=self.department,
            pdpa_consent_at=timezone.now(),
        )
        self.assertFieldError(self.payload(), "email")

    def test_rejects_reserved_nickname(self):
        for nickname in ("admin", "Ad-Min", "MODERATOR", "แอดมิน"):
            with self.subTest(nickname=nickname):
                self.assertFieldError(self.payload(nickname=nickname), "nickname")

    def test_requires_pdpa_consent(self):
        form = self.assertFieldError(self.payload(pdpa_consent=None), "pdpa_consent")
        self.assertIn("PDPA", form.errors["pdpa_consent"][0])

    def test_rejects_password_mismatch(self):
        self.assertFieldError(
            self.payload(password_confirm="Something-Else-123"), "password_confirm"
        )

    def test_rejects_weak_password(self):
        self.assertFieldError(
            self.payload(password="12345678", password_confirm="12345678"), "password"
        )

    def test_department_choices_only_include_active_departments(self):
        queryset = RegisterForm().fields["department"].queryset
        self.assertIn(self.department, queryset)
        self.assertNotIn(self.inactive_department, queryset)
        self.assertFieldError(
            self.payload(department=str(self.inactive_department.pk)), "department"
        )

    def test_invalid_fields_get_bootstrap_invalid_class(self):
        form = self.assertFieldError(self.payload(nickname="admin"), "nickname")
        self.assertIn("is-invalid", form.fields["nickname"].widget.attrs["class"])
        self.assertNotIn("is-invalid", form.fields["email"].widget.attrs["class"])


class RegisterUserServiceTests(RegistrationTestMixin, TestCase):
    def register(self, **overrides):
        kwargs = {
            "email": "6610612345@student.tu.ac.th",
            "password": VALID_PASSWORD,
            "nickname": "Ploy",
            "department": self.department,
            "pdpa_consent_at": timezone.now(),
        }
        kwargs.update(overrides)
        return register_user(**kwargs)

    def test_creates_user_with_student_id_and_hashed_password(self):
        consent_at = timezone.now()
        user = self.register(pdpa_consent_at=consent_at)

        self.assertEqual(user.student_id, "6610612345")
        self.assertEqual(user.department, self.department)
        self.assertEqual(user.pdpa_consent_at, consent_at)
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.assertNotEqual(user.password, VALID_PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_creates_student_role_when_missing(self):
        self.assertFalse(Role.objects.filter(code=Role.STUDENT).exists())

        user = self.register()

        role_codes = list(user.user_roles.values_list("role__code", flat=True))
        self.assertEqual(role_codes, [Role.STUDENT])

    def test_reuses_existing_student_role(self):
        role = Role.objects.create(code=Role.STUDENT, name_th="นักศึกษา")

        user = self.register()

        self.assertEqual(Role.objects.filter(code=Role.STUDENT).count(), 1)
        self.assertTrue(UserRole.objects.filter(user=user, role=role).exists())

    def test_rolls_back_user_when_role_assignment_fails(self):
        with mock.patch.object(
            UserRole.objects, "create", side_effect=IntegrityError("boom")
        ):
            with self.assertRaises(IntegrityError):
                self.register()

        self.assertFalse(User.objects.filter(email="6610612345@student.tu.ac.th").exists())


class RegisterViewTests(RegistrationTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("accounts:register")

    def test_get_renders_form_with_csrf_token(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertIsInstance(response.context["form"], RegisterForm)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, self.department.code)
        self.assertNotContains(response, self.inactive_department.name_th)

    def test_successful_registration_redirects_to_login_with_message(self):
        response = self.client.post(self.url, self.payload(), follow=True)

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "สมัครสมาชิกสำเร็จ")
        user = User.objects.get(email="6610612345@student.tu.ac.th")
        self.assertEqual(user.student_id, "6610612345")
        self.assertEqual(user.nickname, "Ploy")
        self.assertIsNotNone(user.pdpa_consent_at)
        self.assertTrue(user.user_roles.filter(role__code=Role.STUDENT).exists())
        # สมัครแล้วไม่ล็อกอินให้อัตโนมัติ ต้องไปล็อกอินเอง
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_registered_user_can_log_in(self):
        self.client.post(self.url, self.payload())

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "6610612345@student.tu.ac.th", "password": VALID_PASSWORD},
        )

        self.assertRedirects(response, reverse("accounts:home"))

    def assertRegistrationRejected(self, data, field):
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(field, response.context["form"].errors)
        self.assertFalse(User.objects.exists())
        self.assertFalse(UserRole.objects.exists())
        return response

    def test_rejects_invalid_email_domain(self):
        self.assertRegistrationRejected(
            self.payload(email="6610612345@gmail.com"), "email"
        )

    def test_rejects_non_engineering_faculty(self):
        response = self.assertRegistrationRejected(
            self.payload(email="6602612345@student.tu.ac.th"), "email"
        )
        self.assertContains(response, "is-invalid")

    def test_rejects_reserved_nickname(self):
        self.assertRegistrationRejected(self.payload(nickname="Admin"), "nickname")

    def test_rejects_missing_pdpa_consent(self):
        self.assertRegistrationRejected(self.payload(pdpa_consent=None), "pdpa_consent")

    def test_empty_post_shows_errors(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_authenticated_user_is_redirected_home(self):
        user = register_user(
            email="6610600000@student.tu.ac.th",
            password=VALID_PASSWORD,
            nickname="Existing",
            department=self.department,
            pdpa_consent_at=timezone.now(),
        )
        self.client.force_login(user)

        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                response = method(self.url)
                self.assertRedirects(response, reverse("accounts:home"))

    def test_registration_is_csrf_protected(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.exists())
