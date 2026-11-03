from django.test import TestCase
from django.urls import reverse


class AudioStreamingTests(TestCase):
    def test_serve_audio_full_stream(self):
        """GET request without Range header returns full audio file with 200 OK and Accept-Ranges header."""
        url = reverse("accounts:audio_stream", kwargs={"filename": "singular_bao_bao.mp3"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Type"], "audio/mpeg")
        self.assertTrue(int(response["Content-Length"]) > 0)

    def test_serve_audio_partial_range_stream(self):
        """GET request with Range header returns 206 Partial Content with correct Content-Range and length."""
        url = reverse("accounts:audio_stream", kwargs={"filename": "singular_bao_bao.mp3"})
        response = self.client.get(url, HTTP_RANGE="bytes=0-1023")

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(response["Content-Length"], "1024")
        self.assertTrue(response["Content-Range"].startswith("bytes 0-1023/"))

    def test_serve_audio_invalid_range_returns_416(self):
        """GET request with out-of-bounds Range header returns 416 Range Not Satisfiable."""
        url = reverse("accounts:audio_stream", kwargs={"filename": "singular_bao_bao.mp3"})
        response = self.client.get(url, HTTP_RANGE="bytes=99999999-99999999")

        self.assertEqual(response.status_code, 416)
        self.assertTrue(response["Content-Range"].startswith("bytes */"))

    def test_serve_audio_not_found(self):
        """GET request for a non-existent audio file returns 404."""
        url = reverse("accounts:audio_stream", kwargs={"filename": "non_existent_track.mp3"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_serve_audio_directory_traversal_blocked(self):
        """Directory traversal attempts are rejected with 404."""
        url = reverse("accounts:audio_stream", kwargs={"filename": "../views.py"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

