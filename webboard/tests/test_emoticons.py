"""Unit tests for MSN emoticons and external GIF rendering."""

from django.test import SimpleTestCase
from webboard.emoticons import get_msn_emoticons_list, render_webboard_content


class EmoticonsAndGifRenderingTests(SimpleTestCase):
    """Test safe parsing of MSN emoticons and external GIF embeds."""

    def test_get_msn_emoticons_list_contains_expected_codes(self):
        """Curated emoticon list contains common MSN codes."""
        emoticons = get_msn_emoticons_list()
        self.assertGreaterEqual(len(emoticons), 15)
        codes = [item["code"] for item in emoticons]
        for expected in [":)", ":D", ";)", "(L)", "(F)", ":@"]:
            with self.subTest(code=expected):
                self.assertIn(expected, codes)

    def test_render_empty_or_none(self):
        """Rendering empty or falsy text returns empty string."""
        self.assertEqual(render_webboard_content(""), "")
        self.assertEqual(render_webboard_content(None), "")

    def test_xss_protection_escapes_script_tags(self):
        """Raw script tags and unsafe HTML attributes are escaped."""
        raw = '<script>alert("hacked")</script> <img onerror="evil()">'
        rendered = render_webboard_content(raw)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn('onerror="evil()"', rendered)

    def test_msn_emoticon_replacement(self):
        """MSN codes are replaced with responsive SVG icon elements."""
        raw = "Hello :) how are you? :D I love this (L)"
        rendered = render_webboard_content(raw)
        self.assertIn('class="msn-icon msn-smile"', rendered)
        self.assertIn('class="msn-icon msn-laugh"', rendered)
        self.assertIn('class="msn-icon msn-heart"', rendered)

    def test_bbcode_img_replacement(self):
        """BBCode [img]https://...[/img] tags render safe responsive img elements."""
        raw = "Check this GIF: [img]https://media.giphy.com/media/cool.gif[/img]"
        rendered = render_webboard_content(raw)
        self.assertIn('<div class="webboard-embed-box">', rendered)
        self.assertIn('src="https://media.giphy.com/media/cool.gif"', rendered)
        self.assertIn('class="webboard-embed-img"', rendered)

    def test_bare_gif_url_replacement(self):
        """Direct bare HTTPS image URLs are converted to responsive embeds."""
        raw = "Here is an external meme: https://example.com/cat_party.gif enjoy!"
        rendered = render_webboard_content(raw)
        self.assertIn('<div class="webboard-embed-box">', rendered)
        self.assertIn('src="https://example.com/cat_party.gif"', rendered)

    def test_linebreaks_conversion(self):
        """Newlines are converted to HTML linebreaks."""
        raw = "First line\nSecond line\r\nThird line"
        rendered = render_webboard_content(raw)
        self.assertIn("<br>", rendered)

    def test_http_and_complex_query_params_images(self):
        """HTTP protocol and image URLs with complex query parameters are supported."""
        raw = (
            "Check [img]http://example.com/test.png?size=large&v=1.2[/img] "
            "and bare http://cdn.test.com/anim.gif?token=xyz123"
        )
        rendered = render_webboard_content(raw)
        self.assertIn(
            'src="http://example.com/test.png?size=large&amp;v=1.2"', rendered
        )
        self.assertIn('src="http://cdn.test.com/anim.gif?token=xyz123"', rendered)

    def test_templatetags_direct_call(self):
        """Webboard template tags return formatted content and emoticon list."""
        from webboard.templatetags.webboard_tags import (
            format_webboard,
            get_msn_emoticons,
        )

        self.assertIn("<br>", format_webboard("a\nb"))
        self.assertGreater(len(get_msn_emoticons()), 10)

    def test_prevent_false_positive_emoticon_replacement_in_words_and_urls(self):
        """Codes like (c), (r), (p), and URLs do not turn into emoticons."""
        raw = (
            "Section (c) and item (r) and paragraph (p) are normal text. "
            "Also check copyright (c) 2026, registered (r), and paragraph (p). "
            "Sub-word parts such as :Dabc, abc:D, test:), Word(H) should not convert. "
            "Visit https://example.com/:D/view?file=(H)&ref=(c) and "
            "http://example.com/path/(p)/test. "
            "Real emoticons :) and :D and (H) must still convert."
        )
        rendered = render_webboard_content(raw)

        # Normal parenthesized words/letters should be preserved
        self.assertIn("Section (c)", rendered)
        self.assertIn("item (r)", rendered)
        self.assertIn("paragraph (p)", rendered)
        self.assertIn("(c) 2026", rendered)

        # Sub-word strings should be preserved
        self.assertIn(":Dabc", rendered)
        self.assertIn("abc:D", rendered)
        self.assertIn("test:)", rendered)
        self.assertIn("Word(H)", rendered)

        # URLs should preserve query parameters and paths without emoticon SVGs
        self.assertIn("https://example.com/:D/view?file=(H)&amp;ref=(c)", rendered)
        self.assertIn("http://example.com/path/(p)/test", rendered)

        # Legitimate emoticons with proper boundaries should still be converted
        self.assertIn('class="msn-icon msn-smile"', rendered)
        self.assertIn('class="msn-icon msn-laugh"', rendered)
        self.assertIn('class="msn-icon msn-cool"', rendered)
