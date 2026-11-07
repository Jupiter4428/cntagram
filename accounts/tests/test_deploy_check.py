from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import SimpleTestCase, override_settings

PROD_SECURITY_OVERRIDES = {
    "DEBUG": False,
    "SECURE_SSL_REDIRECT": True,
    "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https"),
    "SESSION_COOKIE_SECURE": True,
    "CSRF_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SECURE_HSTS_SECONDS": 3600,
    "SECURE_HSTS_INCLUDE_SUBDOMAINS": True,
    "X_FRAME_OPTIONS": "DENY",
    "MAILERS": {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        }
    },
}


class DeployCheckTests(SimpleTestCase):
    @override_settings(
        **PROD_SECURITY_OVERRIDES,
        SECRET_KEY="django-insecure-" + "x" * 50,
    )
    def test_deploy_check_fails_on_insecure_secret_key(self):
        """Verifies check --deploy fails on insecure key.

        Uses fail-level WARNING to assert deploy failure.
        """
        with self.assertRaises(SystemCheckError):
            call_command(
                "check",
                "--deploy",
                "--fail-level",
                "WARNING",
            )

    @override_settings(
        **PROD_SECURITY_OVERRIDES,
        SECRET_KEY="p" * 50 + "-strong-production-secret-key-1234567890",
    )
    def test_deploy_check_passes_with_production_settings(self):
        """Verifies check --deploy passes with production settings."""
        call_command(
            "check",
            "--deploy",
            "--fail-level",
            "WARNING",
        )
