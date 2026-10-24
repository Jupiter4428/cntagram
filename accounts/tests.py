import time
from pathlib import Path

from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from .forms import LoginForm
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
