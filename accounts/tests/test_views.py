from django.contrib.auth import SESSION_KEY, get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .. import services
from ..forms import RegisterForm
from ..models import Role, UserRole
from .base import ModeratorTestCase, RegistrationTestCase, VALID_PASSWORD

User = get_user_model()


class LoginViewTests(TestCase):
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


class RegisterViewTests(RegistrationTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
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
        before = timezone.now()
        response = self.client.post(self.url, self.payload(), follow=True)
        after = timezone.now()

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "สมัครสมาชิกสำเร็จ")
        user = User.objects.get(email="6610612345@student.tu.ac.th")
        self.assertEqual(user.student_id, "6610612345")
        self.assertEqual(user.entry_year, 66)
        self.assertEqual(user.nickname, "Ploy")
        self.assertIsNotNone(user.pdpa_consent_at)
        self.assertTrue(before <= user.pdpa_consent_at <= after)
        self.assertTrue(user.user_roles.filter(role__code=Role.STUDENT).exists())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_registered_user_can_log_in(self):
        self.register()

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
        response = self.assertRegistrationRejected(self.payload(nickname="Admin"), "nickname")
        self.assertIn("ชื่อเล่นนี้ถูกสงวนไว้ กรุณาใช้ชื่ออื่น", response.context["form"].errors["nickname"][0])

    def test_rejects_duplicate_email(self):
        self.register(nickname="First")
        response = self.client.post(self.url, self.payload(email="6610612345@student.tu.ac.th"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertIn("อีเมลนี้ถูกใช้สมัครแล้ว", response.context["form"].errors["email"])

    def test_rejects_missing_pdpa_consent(self):
        self.assertRegistrationRejected(self.payload(pdpa_consent=None), "pdpa_consent")

    def test_empty_post_shows_errors(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_authenticated_user_get_is_redirected_home(self):
        self.client.force_login(self.register())

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("accounts:home"))

    def test_authenticated_user_post_is_redirected_home(self):
        self.client.force_login(self.register())

        response = self.client.post(self.url, self.payload(email="6610600000@student.tu.ac.th"))

        self.assertRedirects(response, reverse("accounts:home"))
        self.assertEqual(User.objects.count(), 1)

    def test_registration_is_csrf_protected(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.exists())


class ModeratorViewTests(ModeratorTestCase):
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
