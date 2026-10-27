import time

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .. import services
from ..forms import RegisterForm
from ..models import Role, UserRole
from ..services import is_login_rate_limited
from .base import ModeratorTestMixin, RegistrationTestMixin, VALID_PASSWORD

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

    def test_home_renders_reusable_retro_layout(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "includes/_navbar.html")
        self.assertTemplateUsed(response, "includes/_sidebar.html")
        self.assertTemplateUsed(response, "includes/_footer.html")
        self.assertTemplateUsed(response, "includes/_marquee.html")
        self.assertTemplateUsed(response, "includes/_music_player.html")
        self.assertTemplateUsed(response, "includes/_visitor_counter.html")
        self.assertTemplateUsed(response, "includes/_badges.html")
        self.assertTemplateUsed(response, "includes/_archive.html")
        self.assertTemplateUsed(response, "includes/_stickers.html")
        self.assertTemplateUsed(response, "includes/_digital_ephemera.html")

    def test_home_renders_blog_style_demo_content_without_fake_routes(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, 'class="post-entry"', count=2)
        self.assertContains(response, "สมุดบันทึกชุมชน — โพสต์ตัวอย่าง")
        self.assertContains(response, "DEMO POST · ไม่มีหน้ารายละเอียด")
        self.assertContains(response, "Community Archive")
        self.assertContains(response, "ปีการศึกษา 2569")
        self.assertContains(response, "ภาคเรียนที่ 1")
        self.assertContains(response, "รายการนี้ใช้สาธิต navigation เท่านั้น")
        self.assertNotContains(response, 'href="#"')

    def test_old_web_demo_widgets_are_accessible_and_non_functional(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, 'class="retro-marquee"')
        self.assertContains(response, 'tabindex="0"')
        self.assertContains(response, 'aria-hidden="true">WELCOME TO CNTAGRAM!')
        self.assertContains(response, "Decorative UI only")
        self.assertContains(response, "ไม่ใช่ยอดผู้เข้าชมจริง")
        self.assertContains(response, "88×31-inspired decorative badges · DEMO")
        self.assertContains(response, 'class="retro-widget music-widget compact-disclosure"')
        self.assertContains(response, 'class="retro-widget counter-widget compact-disclosure"')
        self.assertContains(response, "Web Badge Collection")
        self.assertNotContains(response, "<script")
        self.assertNotContains(response, "<audio")

    def test_guest_navigation_only_shows_public_account_actions(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, f'href="{reverse("accounts:login")}"')
        self.assertContains(response, f'href="{reverse("accounts:register")}"')
        self.assertNotContains(response, f'href="{reverse("materials:vault")}"')
        self.assertNotContains(response, f'action="{reverse("accounts:logout")}"')

    def test_authenticated_navigation_keeps_vault_and_post_logout(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, self.user.nickname)
        self.assertContains(response, f'href="{reverse("materials:vault")}"')
        self.assertContains(response, 'form method="post"')
        self.assertContains(response, f'action="{reverse("accounts:logout")}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_login_page_inherits_retro_base_template(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, 'href="/static/css/retro.css"')

    def test_register_page_inherits_retro_base_template(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, 'href="/static/css/retro.css"')

    def test_vault_page_inherits_retro_base_template(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("materials:vault"))
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, 'href="/static/css/retro.css"')

    def test_vault_shared_layout_has_no_demo_content(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("materials:vault"))

        self.assertNotContains(response, "DEMO")
        for template in (
            "includes/_archive.html",
            "includes/_music_player.html",
            "includes/_visitor_counter.html",
            "includes/_badges.html",
        ):
            self.assertTemplateNotUsed(response, template)

    def test_auth_pages_use_focused_help_sidebar(self):
        for url_name in ("accounts:login", "accounts:register"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertTemplateUsed(response, "auth_base.html")
                self.assertTemplateUsed(response, "includes/_auth_help.html")
                self.assertContains(response, 'class="site-layout container-xl site-layout--auth"')
                self.assertContains(response, "Member Help")
                self.assertContains(response, "กลับหน้าแรก")
                self.assertNotContains(response, "Community Archive")
                self.assertNotContains(response, "BGM Player")
                self.assertNotContains(response, "Visitor Counter")

    def test_retro_stylesheet_is_discoverable(self):
        self.assertIsNotNone(finders.find("css/retro.css"))
        self.assertIsNotNone(finders.find("img/cyber-orb.svg"))

    def test_guest_can_access_public_pages(self):
        for url_name in ("accounts:home", "accounts:login", "accounts:register"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    hero = 'class="cyber-hero welcome-board"'

    def create_super_admin(self):
        role, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        admin = User.objects.create_user(
            email="6610000001@student.tu.ac.th",
            password=None,
            nickname="Admin",
            department=self.user.department,
            pdpa_consent_at=timezone.now(),
        )
        UserRole.objects.create(user=admin, role=role)
        return admin

    def test_guest_home_uses_the_public_index(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index.html")
        self.assertTemplateNotUsed(response, "accounts/index_admin.html")
        self.assertTemplateNotUsed(response, "includes/_admin_sidebar.html")

    def test_member_home_uses_the_public_index_without_the_admin_menu(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index.html")
        self.assertTemplateNotUsed(response, "accounts/index_admin.html")
        self.assertTemplateNotUsed(response, "includes/_admin_sidebar.html")
        self.assertContains(response, self.hero)

    def test_moderator_home_does_not_show_the_dashboard_or_other_users_details(self):
        role, _ = Role.objects.get_or_create(code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลภาค"})
        moderator = User.objects.create_user(
            email="6610000002@student.tu.ac.th",
            password=None,
            nickname="Mod",
            department=self.user.department,
            pdpa_consent_at=timezone.now(),
        )
        UserRole.objects.create(user=moderator, role=role, department=self.user.department)
        self.client.force_login(moderator)

        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index.html")
        self.assertTemplateNotUsed(response, "accounts/index_admin.html")
        self.assertNotContains(response, self.user.email)

    def test_super_admin_home_with_an_invalid_page_shows_the_first_page(self):
        self.client.force_login(self.create_super_admin())

        response = self.client.get(reverse("accounts:home"), {"page": "abc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dashboard"]["users_page"].number, 1)

    def test_super_admin_home_uses_the_admin_dashboard(self):
        self.client.force_login(self.create_super_admin())

        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index_admin.html")
        self.assertTemplateUsed(response, "includes/_admin_sidebar.html")
        self.assertTemplateNotUsed(response, "accounts/index.html")
        self.assertNotContains(response, self.hero)
        self.assertContains(
            response,
            f'<a class="retro-widget glass-module admin-stat admin-stat--amber" href="{reverse("materials:vault")}">',
        )
        self.assertContains(response, "ไฟล์ที่อัปโหลดทั้งหมด")
        self.assertContains(response, "ไฟล์ที่อัปโหลดรายเดือน")
        self.assertContains(response, 'class="admin-new-users"')
        self.assertContains(response, reverse("catalog:department_list"))

    def test_admin_home_pages_users_and_shows_each_user_in_a_popup(self):
        admin = self.create_super_admin()
        for i in range(7):
            User.objects.create_user(
                email=f"661000020{i}@student.tu.ac.th",
                password=self.password,
                nickname=f"Extra{i}",
                department=self.user.department,
                pdpa_consent_at=timezone.now(),
            )
        self.client.force_login(admin)

        response = self.client.get(reverse("accounts:home"), {"page": 2})

        self.assertEqual(response.context["dashboard"]["users_page"].number, 2)
        self.assertContains(response, 'href="?page=1#recent-users"')
        self.assertContains(response, 'popovertarget="user-%d"' % self.user.pk)
        self.assertContains(response, self.user.email)

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


class RegisterViewTests(RegistrationTestMixin, TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("accounts:register")

    def tearDown(self):
        cache.clear()

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


class RegisterThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("accounts:register")

    def tearDown(self):
        cache.clear()

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


class ModeratorViewTests(ModeratorTestMixin, TestCase):
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
