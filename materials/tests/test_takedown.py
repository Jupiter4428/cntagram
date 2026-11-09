from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import TakedownRequest


class PublicTakedownTests(TestCase):
    def setUp(self):
        self.url = reverse("materials:public_takedown")
        self.payload = {
            "claimant_name": "Teacher",
            "contact_email": "teacher@example.com",
            "content_identifier": "CN201 PDF",
            "reason": "มีปัญหาด้านลิขสิทธิ์",
            "rights_confirmed": "on",
        }

    def test_guest_can_submit_without_login_and_receives_reference(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        request = TakedownRequest.objects.get()
        self.assertContains(response, str(request.reference))

    def test_invalid_form_does_not_create_request(self):
        data = dict(self.payload, rights_confirmed="")
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TakedownRequest.objects.count(), 0)

    @override_settings(REGISTER_RATE_LIMIT_ATTEMPTS=1)
    def test_rate_limit_returns_429(self):
        self.client.post(self.url, self.payload)
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 429)
