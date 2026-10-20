import time

from django.contrib.auth import SESSION_KEY
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .forms import LoginForm
from .models import User
from .services import is_login_rate_limited


class AuthenticationViewsTests(TestCase):
    password = "correct-horse-battery-staple"

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
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email.upper(), "password": self.password},
        )

        self.assertRedirects(response, reverse("accounts:home"))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.user.pk))
        self.assertEqual(self.client.get(reverse("materials:vault")).status_code, 200)

    def test_failed_login_does_not_authenticate_user(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(response, "Please enter a correct")

    def test_login_honors_safe_internal_next_url(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.email,
                "password": self.password,
                "next": reverse("materials:vault"),
            },
        )

        self.assertRedirects(response, reverse("materials:vault"))

    def test_login_rejects_external_next_url(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.email,
                "password": self.password,
                "next": "https://attacker.example/phishing",
            },
        )

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

        response = csrf_client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": self.password},
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SESSION_KEY, csrf_client.session)

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=3,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=120,
    )
    def test_repeated_failures_temporarily_rate_limit_login(self):
        login_url = reverse("accounts:login")
        credentials = {"username": self.user.email, "password": "wrong-password"}
        for _ in range(3):
            response = self.client.post(login_url, credentials, REMOTE_ADDR="192.0.2.1")
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            login_url,
            {"username": self.user.email, "password": self.password},
            REMOTE_ADDR="192.0.2.1",
        )

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
        login_url = reverse("accounts:login")
        credentials = {"username": self.user.email, "password": "wrong-password"}
        for _ in range(3):
            self.client.post(login_url, credentials, REMOTE_ADDR="192.0.2.1")

        response = self.client.post(
            login_url,
            {"username": self.user.email, "password": self.password},
            REMOTE_ADDR="192.0.2.2",
        )

        self.assertRedirects(response, reverse("accounts:home"))

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=3)
    def test_successful_login_clears_previous_failures(self):
        login_url = reverse("accounts:login")
        client_ip = "192.0.2.1"
        credentials = {"username": self.user.email, "password": "wrong-password"}
        for _ in range(2):
            self.client.post(login_url, credentials, REMOTE_ADDR=client_ip)

        self.client.post(
            login_url,
            {"username": self.user.email, "password": self.password},
            REMOTE_ADDR=client_ip,
        )

        self.assertFalse(
            is_login_rate_limited(identifier=self.user.email, client_ip=client_ip)
        )

    @override_settings(
        LOGIN_RATE_LIMIT_ATTEMPTS=1,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=1,
    )
    def test_rate_limit_expires_after_temporary_window(self):
        login_url = reverse("accounts:login")
        client_ip = "192.0.2.1"
        self.client.post(
            login_url,
            {"username": self.user.email, "password": "wrong-password"},
            REMOTE_ADDR=client_ip,
        )
        blocked_response = self.client.post(
            login_url,
            {"username": self.user.email, "password": self.password},
            REMOTE_ADDR=client_ip,
        )
        self.assertEqual(blocked_response.status_code, 429)

        time.sleep(1.1)
        response = self.client.post(
            login_url,
            {"username": self.user.email, "password": self.password},
            REMOTE_ADDR=client_ip,
        )

        self.assertRedirects(response, reverse("accounts:home"))


# ==============================================================================
# US-10: Moderator Management Tests (วางต่อท้ายล่างสุด)
# ==============================================================================
from accounts import selectors, services
from accounts.models import Role, UserRole
from catalog.models import Department
from django.core.exceptions import ValidationError


class ModeratorManagementTests(TestCase):

  def setUp(self):
    self.client = Client()
    self.now = timezone.now()

    self.role_super_admin, _ = Role.objects.get_or_create(
        code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"}
    )
    self.role_moderator, _ = Role.objects.get_or_create(
        code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
    )
    self.role_student, _ = Role.objects.get_or_create(
        code=Role.STUDENT, defaults={"name_th": "นักศึกษา"}
    )

    self.dept_cn = Department.objects.create(
        code="CN",
        name_th="วิศวกรรมคอมพิวเตอร์",
        name_en="Computer Engineering",
    )
    self.dept_ce = Department.objects.create(
        code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
    )
    self.dept_me = Department.objects.create(
        code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
    )

    # Super Admin (ใช้อีเมลนักศึกษาไม่ซ้ำกัน)
    self.admin = User.objects.create_user(
        email="6510610099@student.tu.ac.th",
        password="password123",
        nickname="admin",
        department=self.dept_cn,
        is_superuser=True,
        pdpa_consent_at=self.now,
    )
    UserRole.objects.create(user=self.admin, role=self.role_super_admin)

    # ผู้ใช้ทั่วไป
    self.user_momo = User.objects.create_user(
        email="6510610001@student.tu.ac.th",
        password="password123",
        nickname="momo",
        department=self.dept_cn,
        pdpa_consent_at=self.now,
    )
    UserRole.objects.create(user=self.user_momo, role=self.role_student)

  def test_assign_and_remove_moderator_many_to_many(self):
    """AC: ผูก user กับหลายภาควิชาได้ (M:N) และถอดถอนได้"""
    ur1 = services.assign_moderator(
        user=self.user_momo, department=self.dept_cn, granted_by=self.admin
    )
    ur2 = services.assign_moderator(
        user=self.user_momo, department=self.dept_ce, granted_by=self.admin
    )

    self.assertTrue(
        selectors.is_moderator_of_department(self.user_momo, self.dept_cn)
    )
    self.assertTrue(
        selectors.is_moderator_of_department(self.user_momo, self.dept_ce)
    )

    services.remove_moderator(user_role=ur1)
    self.assertFalse(
        selectors.is_moderator_of_department(self.user_momo, self.dept_cn)
    )
    self.assertTrue(
        selectors.is_moderator_of_department(self.user_momo, self.dept_ce)
    )

  def test_moderator_cannot_moderate_other_departments(self):
    """AC: Moderator ภาคหนึ่ง ไม่มีสิทธิ์จัดการภาคอื่น"""
    services.assign_moderator(
        user=self.user_momo, department=self.dept_cn, granted_by=self.admin
    )

    self.assertTrue(
        selectors.is_moderator_of_department(self.user_momo, self.dept_cn)
    )
    self.assertFalse(
        selectors.is_moderator_of_department(self.user_momo, self.dept_me)
    )

  def test_cannot_assign_duplicate_moderator(self):
    """AC: แต่งตั้งซ้ำ (user + ภาคเดิม) ไม่ได้ และบันทึก granted_by ถูกต้อง"""
    ur = services.assign_moderator(
        user=self.user_momo, department=self.dept_cn, granted_by=self.admin
    )
    self.assertEqual(ur.granted_by, self.admin)

    with self.assertRaises(ValidationError):
      services.assign_moderator(
          user=self.user_momo, department=self.dept_cn, granted_by=self.admin
      )

  def test_non_super_admin_gets_403(self):
    """Security: ผู้ใช้ที่ไม่ใช่ Super Admin เข้าหน้านี้ต้องได้ 403 Forbidden"""
    self.client.force_login(self.user_momo)
    response = self.client.get(reverse("accounts:moderator_manage"))
    self.assertEqual(response.status_code, 403)