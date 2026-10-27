from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse


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
