from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(WHITENOISE_USE_FINDERS=True)
class BgmStaticAudioTests(TestCase):
    def test_range_request_returns_partial_content(self):
        response = self.client.get(
            "/static/audio/singular_bao_bao.mp3", HTTP_RANGE="bytes=0-1023"
        )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Type"], "audio/mpeg")
        self.assertEqual(response["Content-Length"], "1024")
        self.assertTrue(response["Content-Range"].startswith("bytes 0-1023/"))

    def test_nonexistent_audio_returns_404(self):
        response = self.client.get("/static/audio/not_found.mp3")

        self.assertEqual(response.status_code, 404)

    def test_wav_mimetype_is_served_as_audio_wav(self):
        response = self.client.get("/static/audio/tse_cyber_campus.wav")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "audio/wav")

    def test_home_page_renders_music_widget_with_static_urls(self):
        response = self.client.get(reverse("accounts:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="bgm-playlist"')
        self.assertContains(response, 'data-src="/static/audio/singular_bao_bao.mp3"')
        self.assertNotContains(response, '"/audio/')
        self.assertContains(response, 'id="bgm-audio"')
        self.assertContains(response, 'id="bgm-play-pause"')
        self.assertContains(response, 'id="bgm-mute"')
        self.assertContains(response, 'id="bgm-seekbar"')
        self.assertContains(response, 'id="bgm-tracklist"')

    def test_bgm_player_js_served_and_secures_against_xss(self):
        response = self.client.get("/static/js/bgm_player.js")

        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode("utf-8")
        # Ensure template literal string interpolation is not assigned to innerHTML
        self.assertNotRegex(content, r"innerHTML\s*=\s*`[^`]*\$\{")
        self.assertIn("btn.append(", content)
        # Ensure play and pause event listeners exist for external controls
        self.assertIn('audio.addEventListener("play"', content)
        self.assertIn('audio.addEventListener("pause"', content)
        # Ensure track numbering pads correctly without `[0${...}]`
        self.assertIn('(currentTrackIndex + 1).toString().padStart(2, "0")', content)
        self.assertNotIn("`[0${", content)
        # Ensure updateMuteButton sets aria-label
        self.assertIn('muteBtn.setAttribute("aria-label"', content)
