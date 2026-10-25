import datetime
import time
from pathlib import Path

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import selectors, services
from catalog.models import Batch, Course, Department

from .forms import LoginForm
from .models import Role, UserRole
from .selectors import admin_dashboard
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
        self.assertContains(response, 'href="/static/css/retro.css"')
        self.assertContains(response, 'src="/static/img/cyber-orb.svg"')
        self.assertContains(response, "WELCOME TO CNTAGRAM!")
        self.assertContains(response, "เว็บบอร์ดเด็กวิศวะ!")
        self.assertContains(response, "RECENTLY UPDATED / ILLUSTRATIVE")
        self.assertContains(response, "Decorative only")
        self.assertContains(response, "COMING SOON")
        self.assertContains(response, "A “COSMIC” CONNECTION")
        self.assertContains(response, "404:<br>ความรู้ไม่พบ")
        self.assertContains(response, "category-icon category-icon--notes")
        self.assertContains(response, "category-icon category-icon--sheet")
        self.assertContains(response, "category-icon category-icon--archive")
        self.assertContains(response, "CNTAGRAM</b> ONLINE")
        self.assertContains(response, "BRAIN.EXE</b> RUNNING")
        self.assertContains(response, 'aria-hidden="true"')
        self.assertContains(response, 'class="capsule-link retro-tab is-active"')
        self.assertContains(response, 'class="retro-counter pixel-counter"')
        self.assertContains(response, 'class="retro-badge web-badge')
        self.assertContains(response, 'class="retro-sticker fun-sticker')
        self.assertNotContains(response, "music-widget__controls")
        self.assertNotContains(response, 'button type="button" disabled')
        self.assertNotContains(response, "<audio")
        self.assertContains(response, "ข้อมูลหน้าแรกเป็นตัวอย่าง FE-1")

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

    def test_existing_pages_inherit_retro_base_template(self):
        public_urls = ("accounts:login", "accounts:register")
        for url_name in public_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, 'href="/static/css/retro.css"')

        self.client.force_login(self.user)
        response = self.client.get(reverse("materials:vault"))
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, 'href="/static/css/retro.css"')

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
        stylesheet_path = finders.find("css/retro.css")
        orb_path = finders.find("img/cyber-orb.svg")
        self.assertIsNotNone(stylesheet_path)
        self.assertIsNotNone(orb_path)

        stylesheet = Path(stylesheet_path).read_text(encoding="utf-8")
        expected_tokens = {
            "--cyber-black": "#090911",
            "--tse-red": "#8C191C",
            "--tse-yellow": "#FFD04F",
            "--tse-charcoal": "#58595B",
            "--chrome-silver": "#DDE3EE",
            "--plastic-white": "#F8F9FF",
            "--aero-blue": "#A9D8FF",
            "--bubblegum-pink": "#FF78C8",
            "--acid-lime": "#C7FF5E",
            "--iridescent-purple": "#A88CFF",
            "--midnight-navy": "#111423",
            "--soft-indigo": "#1B1F35",
        }
        for token, value in expected_tokens.items():
            with self.subTest(token=token):
                self.assertIn(f"{token}: {value};", stylesheet)

        for component_class in (
            ".retro-widget",
            ".retro-widget__header",
            ".retro-widget__body",
            ".retro-badge",
            ".retro-sticker",
            ".retro-counter",
            ".retro-tab",
            ".post-entry",
            ".archive-widget",
        ):
            with self.subTest(component_class=component_class):
                self.assertIn(component_class, stylesheet)

        self.assertIn("@keyframes marquee-loop", stylesheet)
        self.assertIn("@keyframes brain-blinkie", stylesheet)
        self.assertIn(".category-icon--notes", stylesheet)
        self.assertIn(".chrome-circuit-heart", stylesheet)
        self.assertIn("@media (prefers-reduced-motion: reduce)", stylesheet)

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
        self.assertTemplateNotUsed(response, "includes/_admin_sidebar.html")

    def test_member_home_uses_the_public_index_without_the_admin_menu(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index.html")
        self.assertTemplateNotUsed(response, "includes/_admin_sidebar.html")
        self.assertContains(response, self.hero)

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


class AdminDashboardSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(code="CN", name_th="คอมพิวเตอร์", name_en="Computer")
        Department.objects.create(code="OLD", name_th="ภาคเก่า", name_en="Old", is_active=False)
        Batch.objects.create(department=cls.cn, number=21)
        Batch.objects.create(department=cls.cn, number=22)
        for code in ("CN101", "CN102", "SC135"):
            Course.objects.create(code=code, name_en=code)
        student, _ = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})
        admin, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        cls.users = []
        for i, role in enumerate((student, student, admin)):
            user = User.objects.create_user(
                email=f"661000000{i}@student.tu.ac.th",
                password="pw",
                nickname=f"User{i}",
                department=cls.cn,
                pdpa_consent_at=timezone.now(),
            )
            UserRole.objects.create(user=user, role=role)
            cls.users.append(user)

    def test_totals_count_active_departments_batches_and_courses(self):
        totals = admin_dashboard()["totals"]

        self.assertEqual(
            (totals["departments"], totals["batches"], totals["courses"]),
            (1, 2, 3),
        )

    def test_role_counts_are_sorted_by_count_with_percent_and_donut_slice(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            dashboard["roles"],
            [
                {"label": "นักศึกษา", "count": 2, "percent": 67, "offset": 0, "end": 67},
                {"label": "ผู้ดูแลระบบ", "count": 1, "percent": 33, "offset": 67, "end": 100},
            ],
        )

    def test_role_counts_count_a_moderator_of_two_departments_once(self):
        moderator, _ = Role.objects.get_or_create(code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลภาค"})
        me = Department.objects.create(code="ME", name_th="เครื่องกล", name_en="Mechanical")
        for department in (self.cn, me):
            UserRole.objects.create(user=self.users[0], role=moderator, department=department)

        roles = admin_dashboard()["roles"]

        self.assertEqual([(r["label"], r["count"]) for r in roles if r["label"] == "ผู้ดูแลภาค"], [("ผู้ดูแลภาค", 1)])

    def test_new_user_counts_by_today_week_month_year_and_all(self):
        def joined(user, *date_parts):
            moment = datetime.datetime(*date_parts, 12, tzinfo=datetime.timezone.utc)
            User.objects.filter(pk=user.pk).update(created_at=moment)

        self.add_users(1)
        joined(self.users[0], 2026, 10, 24)  # วันนี้ (เสาร์)
        joined(self.users[1], 2026, 10, 20)  # สัปดาห์นี้ (เริ่มจันทร์ 19)
        joined(self.users[2], 2026, 10, 2)  # เดือนนี้
        joined(User.objects.get(nickname="Extra0"), 2025, 12, 31)  # ปีก่อน

        dashboard = admin_dashboard(today=datetime.date(2026, 10, 24))

        counts = dashboard["new_users"]
        self.assertEqual(
            (counts["day"], counts["week"], counts["month"], counts["year"]),
            (1, 2, 3, 3),
        )

    def test_all_users_count_goes_up_by_one_per_created_user(self):
        before = admin_dashboard()["new_users"]["all"]

        self.add_users(1)

        self.assertEqual(admin_dashboard()["new_users"]["all"], before + 1)

    def test_all_users_count_does_not_drop_when_a_user_is_deleted(self):
        before = admin_dashboard()["new_users"]["all"]
        UserRole.objects.filter(user=self.users[0]).delete()
        User.objects.filter(pk=self.users[0].pk).delete()

        dashboard = admin_dashboard()

        self.assertEqual(dashboard["new_users"]["all"], before)
        self.assertEqual(dashboard["totals"]["users"], before)

    def add_users(self, count):
        for i in range(count):
            User.objects.create_user(
                email=f"6610{900000 + i}@student.tu.ac.th",
                password=None,
                nickname=f"Extra{i}",
                department=self.cn,
                pdpa_consent_at=timezone.now(),
            )

    def test_users_page_lists_newest_first_with_role_labels_and_upload_count(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            [
                (user.nickname, [r.role.name_th for r in user.user_roles.all()], user.upload_count)
                for user in dashboard["users_page"]
            ],
            [("User2", ["ผู้ดูแลระบบ"], 0), ("User1", ["นักศึกษา"], 0), ("User0", ["นักศึกษา"], 0)],
        )

    def test_users_are_split_into_pages_of_seven(self):
        self.add_users(6)

        users_page = admin_dashboard(page=2)["users_page"]

        self.assertEqual(users_page.paginator.num_pages, 2)
        self.assertEqual([user.nickname for user in users_page], ["User1", "User0"])

    def test_out_of_range_page_shows_the_last_page(self):
        self.add_users(6)

        users_page = admin_dashboard(page="99")["users_page"]

        self.assertEqual(users_page.number, 2)

    def test_page_numbers_show_six_pages_then_an_ellipsis_and_the_last(self):
        self.add_users(88)  # 91 คน = 13 หน้า

        users_page = admin_dashboard(page=1)["users_page"]

        self.assertEqual(
            [str(n) for n in users_page.elided_range],
            ["1", "2", "3", "4", "5", "6", "…", "13"],
        )

    def test_department_overview_lists_active_departments_with_user_and_batch_counts(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            [(d.code, d.user_count, d.batch_count) for d in dashboard["departments"]],
            [("CN", 3, 2)],
        )

    def test_dashboard_runs_a_fixed_number_of_queries(self):
        with self.assertNumQueries(9):
            dashboard = admin_dashboard()
            for user in dashboard["users_page"]:
                [r.role.name_th for r in user.user_roles.all()]


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

    def test_moderator_cannot_moderate_other_departments(self):
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
        messages_list = list(response.context["messages"])
        self.assertTrue(any("อยู่แล้ว" in str(m) for m in messages_list))

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
