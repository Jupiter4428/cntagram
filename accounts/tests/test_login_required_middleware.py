"""Regression tests for centralized guest access control (Issue #45)."""

from types import ModuleType

from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import URLResolver, get_resolver, include, path, reverse

from accounts import urls as accounts_urls


def _patterns(patterns, prefix=""):
    for p in patterns:
        if isinstance(p, URLResolver):
            yield from _patterns(p.url_patterns, prefix + str(p.pattern))
        else:
            yield prefix + str(p.pattern), p.callback


class LoginRequiredMiddlewareTests(TestCase):
    def test_only_expected_pages_are_public(self):
        public = {
            route
            for route, view in _patterns(get_resolver().url_patterns)
            if not route.startswith("admin/")
            and not getattr(view, "login_required", True)
        }
        self.assertEqual(public, {"", "login/", "logout/", "register/", "poll/vote/"})

    def test_public_pages_are_accessible_to_guests(self):
        for name in ("accounts:home", "accounts:register", "accounts:login"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_all_private_routes_redirect_guests(self):
        private_urls = (
            ("accounts:moderator_manage", ()),
            ("accounts:moderator_remove", (1,)),
            ("catalog:department_list", ()),
            ("catalog:department_create", ()),
            ("catalog:department_update", (1,)),
            ("catalog:department_delete", (1,)),
            ("catalog:batch_list", ()),
            ("catalog:batch_create", ()),
            ("catalog:batch_delete", (1,)),
            ("catalog:batch_course_manage", (1,)),
            ("catalog:batch_course_remove", (1, 1)),
            ("catalog:course_list", ()),
            ("catalog:course_create", ()),
            ("materials:vault", ()),
            ("materials:document_detail", (1,)),
            ("materials:document_preview", (1,)),
            ("materials:document_download", (1,)),
            ("materials:upload", ()),
            ("materials:upload_done", ()),
            ("materials:upload_course_options", (1,)),
            ("materials:approval_queue", ()),
            ("materials:approval_review", (1,)),
            ("materials:approval_preview", (1,)),
        )
        for name, args in private_urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                self.assertRedirects(
                    self.client.get(url),
                    f"{reverse('accounts:login')}?next={url}",
                )

    def test_guest_logout_redirects_home(self):
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:home"))

    def test_guest_logout_without_csrf_token_is_forbidden(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 403)

    def test_admin_index_redirects_guest_to_admin_login(self):
        url = reverse("admin:index")
        self.assertRedirects(
            self.client.get(url), f"{reverse('admin:login')}?next={url}"
        )

    def test_admin_login_remains_accessible(self):
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 200)

    def test_new_view_without_decorator_is_private_by_default(self):
        def private_view(request):
            return HttpResponse("private")

        module = ModuleType("issue45_test_urls")
        module.urlpatterns = [
            path("private/", private_view),
            path(
                "",
                include((accounts_urls.urlpatterns, "accounts"), namespace="accounts"),
            ),
        ]
        with override_settings(ROOT_URLCONF=module):
            response = self.client.get("/private/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login") + "?next="))
