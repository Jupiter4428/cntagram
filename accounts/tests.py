import time

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from . import selectors, services
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

    def test_login_page_keeps_next_from_query_string(self):
        vault_url = reverse("materials:vault")

        response = self.client.get(f"{reverse('accounts:login')}?next={vault_url}")

        self.assertContains(response, f'name="next" value="{vault_url}"')

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


class ModeratorManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()
        cls.role_super_admin, _ = Role.objects.get_or_create(
            code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"}
        )
        cls.role_moderator, _ = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )
        cls.role_student, _ = Role.objects.get_or_create(
            code=Role.STUDENT, defaults={"name_th": "นักศึกษา"}
        )

        cls.dept_cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.dept_ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )
        cls.dept_me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )

        cls.admin = User.objects.create_user(
            email="6510610099@student.tu.ac.th",
            password="password123",
            nickname="admin",
            department=cls.dept_cn,
            is_superuser=True,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.admin, role=cls.role_super_admin)

        cls.user_momo = User.objects.create_user(
            email="6510610001@student.tu.ac.th",
            password="password123",
            nickname="momo",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.user_momo, role=cls.role_student)

        cls.user_nana = User.objects.create_user(
            email="6510610002@student.tu.ac.th",
            password="password123",
            nickname="nana",
            department=cls.dept_ce,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.user_nana, role=cls.role_student)

    def test_assign_and_remove_moderator_many_to_many(self):
        ur1 = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        ur2 = services.assign_moderator(
            user=self.user_momo, department=self.dept_ce, granted_by=self.admin
        )

        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_ce)
        )

        services.remove_moderator(user_role=ur1)
        self.assertFalse(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_ce)
        )

    def test_department_can_have_many_moderators(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        services.assign_moderator(
            user=self.user_nana, department=self.dept_cn, granted_by=self.admin
        )

        moderators = selectors.moderator_list().filter(department=self.dept_cn)
        self.assertEqual(
            {m.user for m in moderators}, {self.user_momo, self.user_nana}
        )

    def test_is_moderator_of_department_is_scoped_to_assigned_department(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertFalse(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_me)
        )

    def test_cannot_assign_duplicate_moderator(self):
        ur = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.assertEqual(ur.granted_by, self.admin)

        with self.assertRaises(ValidationError):
            services.assign_moderator(
                user=self.user_momo, department=self.dept_cn, granted_by=self.admin
            )

    def test_super_admin_can_get_manage_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:moderator_manage"))
        self.assertEqual(response.status_code, 200)

    def test_assign_moderator_via_view(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:moderator_manage"),
            {"user": self.user_momo.pk, "department": self.dept_cn.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        ur = UserRole.objects.get(
            user=self.user_momo, department=self.dept_cn, role=self.role_moderator
        )
        self.assertEqual(ur.granted_by, self.admin)
        self.assertIsNotNone(ur.granted_at)

    def test_assign_duplicate_moderator_via_view_shows_error(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        initial_count = UserRole.objects.count()

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:moderator_manage"),
            {"user": self.user_momo.pk, "department": self.dept_cn.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserRole.objects.count(), initial_count)
        self.assertContains(response, "อยู่แล้ว")

    def test_remove_moderator_via_view(self):
        ur = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.client.force_login(self.admin)

        get_res = self.client.get(reverse("accounts:moderator_remove", args=[ur.pk]))
        self.assertEqual(get_res.status_code, 405)

        post_res = self.client.post(
            reverse("accounts:moderator_remove", args=[ur.pk]), follow=True
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertFalse(UserRole.objects.filter(pk=ur.pk).exists())

    def test_non_super_admin_cannot_remove_moderator(self):
        ur = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.client.force_login(self.user_momo)

        response = self.client.post(reverse("accounts:moderator_remove", args=[ur.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(UserRole.objects.filter(pk=ur.pk).exists())

    def test_remove_view_rejects_non_moderator_role(self):
        admin_role = UserRole.objects.get(user=self.admin, role=self.role_super_admin)
        self.client.force_login(self.admin)

        response = self.client.post(reverse("accounts:moderator_remove", args=[admin_role.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(UserRole.objects.filter(pk=admin_role.pk).exists())

    def test_non_super_admin_cannot_open_or_post_manage_page(self):
        services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)
        self.client.force_login(self.user_momo)
        url = reverse("accounts:moderator_manage")

        self.assertEqual(self.client.get(url).status_code, 403)
        response = self.client.post(url, {"user": self.user_nana.pk, "department": self.dept_ce.pk})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(UserRole.objects.filter(user=self.user_nana, role=self.role_moderator).exists())

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("accounts:moderator_manage"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_moderator_list_queries_prevent_n_plus_one(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        services.assign_moderator(
            user=self.user_nana, department=self.dept_ce, granted_by=self.admin
        )
        with self.assertNumQueries(1):
            for m in selectors.moderator_list():
                _ = (m.user.email, m.department.code, m.granted_by.email)
