"""Regression tests for centralized guest access control (Issue #45)."""

from django.test import TestCase, override_settings
from django.urls import reverse


class LoginRequiredMiddlewareTests(TestCase):
    def test_public_pages_are_accessible_to_guests(self):
        for name in ("accounts:home", "accounts:register", "accounts:login"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_private_pages_redirect_guests_to_login(self):
        login_url = reverse("accounts:login")
        for name in (
            "materials:vault", "materials:upload", "materials:approval_queue",
            "catalog:batch_list", "catalog:course_list", "accounts:moderator_manage",
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(login_url + "?next="))

    def test_admin_login_remains_accessible(self):
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 200)

    def test_new_view_without_decorator_is_private_by_default(self):
        from django.http import HttpResponse
        from django.urls import include, path
        from types import ModuleType
        from accounts import urls as accounts_urls

        def private_view(request):
            return HttpResponse("private")

        module = ModuleType("issue45_test_urls")
        module.urlpatterns = [
            path("private/", private_view),
            path("", include((accounts_urls.urlpatterns, "accounts"), namespace="accounts")),
        ]
        with override_settings(ROOT_URLCONF=module):
            response = self.client.get("/private/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login") + "?next="))
