"""Tests for the read-only production readiness helper."""

import unittest

from scripts.check_production_readiness import check


class ProductionReadinessTests(unittest.TestCase):
    def setUp(self):
        self.env = {
            "DEBUG": "False",
            "SECRET_KEY": "a" * 64,
            "ALLOWED_HOSTS": "cntagram-h195.onrender.com",
            "DATABASE_URL": "postgresql://user:password@localhost/db",
            "CSRF_TRUSTED_ORIGINS": "https://cntagram-h195.onrender.com",
            "MEDIA_ROOT": "/var/data/media",
        }

    def test_complete_configuration_passes(self):
        self.assertEqual(check(self.env), [])

    def test_missing_and_unsafe_configuration_fails(self):
        self.assertGreaterEqual(len(check({})), 6)
        bad = dict(self.env, DEBUG="True", ALLOWED_HOSTS="*")
        self.assertTrue(any("DEBUG" in item for item in check(bad)))
        self.assertTrue(any("ALLOWED_HOSTS" in item for item in check(bad)))

    def test_insecure_csrf_origin_is_rejected(self):
        bad = dict(self.env, CSRF_TRUSTED_ORIGINS="http://example.com")
        self.assertTrue(any("CSRF" in item for item in check(bad)))


if __name__ == "__main__":
    unittest.main()
