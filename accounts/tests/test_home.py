from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from ..models import Role, UserRole

User = get_user_model()


class HomeViewTests(TestCase):
    password = "correct-horse-battery-staple"
    hero = 'class="cyber-hero welcome-board"'

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
