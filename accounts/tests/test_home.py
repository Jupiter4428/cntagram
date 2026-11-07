from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .. import services
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

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)

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
        self.assertContains(response, "สมุดบันทึกและประกาศชุมชน")
        self.assertContains(response, "ประกาศปักหมุด")
        self.assertNotContains(response, "DEMO POST")
        self.assertContains(response, "Community Archive")
        self.assertContains(response, "ปีการศึกษา 2569")
        self.assertContains(response, "ภาคเรียนที่ 1")
        self.assertContains(response, "คลิกที่รายวิชาเพื่อค้นหาชีทและข้อสอบเก่าในคลัง")
        self.assertNotContains(response, 'href="#"')

    def test_old_web_demo_widgets_are_accessible_and_safe(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, 'class="retro-marquee"')
        self.assertContains(response, 'tabindex="0"')
        self.assertContains(response, 'aria-hidden="true">WELCOME TO CNTAGRAM!')
        self.assertContains(response, "สถิติยอดผู้เข้าชมสะสมแบบเรียลไทม์")
        self.assertNotContains(response, "ไม่ใช่ยอดผู้เข้าชมจริง")
        self.assertContains(response, "88×31-inspired retro badges · TSE Community")
        self.assertNotContains(response, "badges · DEMO")
        self.assertContains(response, 'class="retro-widget counter-widget compact-disclosure"')
        self.assertContains(response, "Web Badge Collection")

    def test_bgm_player_renders_controls_audio_and_script(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, 'class="retro-widget music-widget compact-disclosure"')
        self.assertContains(response, '<audio id="bgm-audio"')
        self.assertContains(response, 'id="bgm-seekbar"')
        self.assertContains(response, 'id="bgm-play-pause"')
        self.assertContains(response, 'id="bgm-prev"')
        self.assertContains(response, 'id="bgm-next"')
        self.assertContains(response, 'id="bgm-toggle-list"')
        self.assertContains(response, 'id="bgm-tracklist"')
        self.assertContains(response, 'src="/static/js/bgm_player.js"')
        self.assertContains(response, '<audio id="bgm-audio" preload="metadata"></audio>')

    def test_bgm_player_static_assets_are_discoverable(self):
        self.assertIsNotNone(finders.find("js/bgm_player.js"))
        self.assertIsNotNone(finders.find("audio/tse_cyber_campus.wav"))
        self.assertIsNotNone(finders.find("audio/midnight_study_lofi.wav"))
        self.assertIsNotNone(finders.find("audio/final_exam_rush.wav"))

    def test_guest_navigation_only_shows_public_account_actions(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, f'href="{reverse("accounts:login")}"')
        self.assertContains(response, f'href="{reverse("accounts:register")}"')
        self.assertContains(response, "เมนูชุมชน")
        self.assertContains(response, "สมัครสมาชิกใหม่")
        self.assertNotContains(response, f'href="{reverse("materials:vault")}"')
        self.assertNotContains(response, f'action="{reverse("accounts:logout")}"')

    def test_authenticated_navigation_keeps_vault_and_post_logout(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:home"))

        self.assertContains(response, self.user.nickname)
        self.assertContains(response, f'href="{reverse("materials:vault")}"')
        self.assertContains(response, f'href="{reverse("materials:vault")}?query=CN101"')
        self.assertContains(response, f'href="{reverse("materials:upload")}"')
        self.assertContains(response, "เมนูชุมชน")
        self.assertContains(response, "อัปโหลดชีทใหม่")
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
        self.assertIsNotNone(finders.find("js/home_widgets.js"))

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
        self.assertContains(response, 'src="/static/js/home_widgets.js"')

    def test_member_home_uses_the_public_index_without_the_admin_menu(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:home"))

        self.assertTemplateUsed(response, "accounts/index.html")
        self.assertTemplateNotUsed(response, "accounts/index_admin.html")
        self.assertTemplateNotUsed(response, "includes/_admin_sidebar.html")
        for url_name in ("catalog:department_list", "catalog:batch_list", "catalog:course_list"):
            with self.subTest(url_name=url_name):
                self.assertNotContains(response, reverse(url_name))
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
        self.assertContains(response, reverse("catalog:batch_list"))
        self.assertContains(response, reverse("catalog:course_list"))

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

    def test_guest_home_runs_no_document_queries(self):
        with self.assertNumQueries(0):
            self.client.get(reverse("accounts:home"))

    def test_record_home_visit_increments_and_zero_pads_counter(self):
        first = services.record_home_visit()
        second = services.record_home_visit()

        self.assertEqual(first, "000039")
        self.assertEqual(second, "000040")

    def test_home_visitor_counter_is_open_and_increments_on_each_visit(self):
        first_response = self.client.get(reverse("accounts:home"))
        second_response = self.client.get(reverse("accounts:home"))

        self.assertContains(
            first_response,
            '<details class="retro-widget counter-widget compact-disclosure" open>',
        )
        self.assertContains(
            first_response,
            "<span>0</span><span>0</span><span>0</span><span>0</span><span>3</span><span>9</span>",
        )
        self.assertContains(
            second_response,
            "<span>0</span><span>0</span><span>0</span><span>0</span><span>4</span><span>0</span>",
        )

    def test_poll_services_record_vote_and_calculate_percentages(self):
        initial = services.get_weekly_poll()
        self.assertEqual(initial["total"], 0)
        self.assertEqual(len(initial["choices"]), 3)

        success, updated = services.record_poll_vote(choice_key="math")
        self.assertTrue(success)
        self.assertEqual(updated["total"], 1)
        math_choice = next(c for c in updated["choices"] if c["key"] == "math")
        self.assertEqual(math_choice["votes"], 1)
        self.assertEqual(math_choice["percent"], 100)

        # Invalid choice rejected
        invalid_success, _ = services.record_poll_vote(choice_key="nonexistent")
        self.assertFalse(invalid_success)

        services.record_poll_vote(choice_key="dsa")
        poll = services.get_weekly_poll()
        self.assertEqual(poll["total"], 2)
        math_c = next(c for c in poll["choices"] if c["key"] == "math")
        dsa_c = next(c for c in poll["choices"] if c["key"] == "dsa")
        self.assertEqual(math_c["percent"], 50)
        self.assertEqual(dsa_c["percent"], 50)

    def test_poll_vote_view_post_records_vote_and_redirects(self):
        response = self.client.post(reverse("accounts:poll_vote"), {"choice": "math"})
        self.assertRedirects(response, reverse("accounts:home"))

        # Verify home page renders results when voted
        home_resp = self.client.get(reverse("accounts:home"))
        self.assertContains(home_resp, "ผลโหวตทั้งหมด 1 เสียง")
        self.assertContains(home_resp, "Engineering Math / Calculus")
        self.assertContains(home_resp, "100%")

        # Verify ?poll_view=form allows viewing choices with back link
        form_resp = self.client.get(reverse("accounts:home") + "?poll_view=form")
        self.assertContains(form_resp, "กลับไปดูผลโหวต")
        self.assertContains(form_resp, 'name="choice"')

    def test_shoutbox_services_add_and_retrieve_messages(self):
        initial = services.get_shoutbox_messages()
        self.assertTrue(len(initial) > 0)

        services.add_shoutbox_message(author="Tester", text="สวัสดีชาววิศวะ!")
        updated = services.get_shoutbox_messages()
        self.assertEqual(updated[-1]["author"], "Tester")
        self.assertEqual(updated[-1]["text"], "สวัสดีชาววิศวะ!")

    def test_shoutbox_post_view_requires_authentication(self):
        response = self.client.post(reverse("accounts:shoutbox_post"), {"message": "ลองพิมพ์"})
        # Anonymous user redirected to login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse("accounts:login") in response.url)

        self.client.force_login(self.user)
        auth_response = self.client.post(reverse("accounts:shoutbox_post"), {"message": "ยินดีที่ได้รู้จักครับ"})
        self.assertRedirects(auth_response, reverse("accounts:home"))

        home_resp = self.client.get(reverse("accounts:home"))
        self.assertContains(home_resp, self.user.nickname)
        self.assertContains(home_resp, "ยินดีที่ได้รู้จักครับ")

    def test_poll_vote_ajax_returns_json_and_records_vote(self):
        response = self.client.post(
            reverse("accounts:poll_vote"),
            {"choice": "circuit"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["has_voted"])
        self.assertEqual(data["poll"]["total"], 1)
        circuit = next(c for c in data["poll"]["choices"] if c["key"] == "circuit")
        self.assertEqual(circuit["votes"], 1)

    def test_shoutbox_post_ajax_returns_json_with_messages(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("accounts:shoutbox_post"),
            {"message": "ข้อความ AJAX ไม่รีเฟรช"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["messages"][-1]["text"], "ข้อความ AJAX ไม่รีเฟรช")
        self.assertIn(self.user.nickname, data["messages"][-1]["author"])




