from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import SimpleTestCase, override_settings


class DeployCheckTests(SimpleTestCase):
    @override_settings(DEBUG=False, SECRET_KEY="django-insecure-" + "x" * 50)
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
