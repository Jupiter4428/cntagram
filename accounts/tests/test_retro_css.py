from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class RetroCssContractTests(SimpleTestCase):
    def setUp(self):
        self.css = (Path(settings.BASE_DIR) / "static/css/retro.css").read_text(
            encoding="utf-8"
        )

    def test_retro_css_has_single_root_and_no_layered_legacy_passes(self):
        self.assertEqual(self.css.count(":root {"), 1)
        self.assertNotIn("Round 3", self.css)
        self.assertNotIn("Authentic old-web pass", self.css)
        self.assertNotIn("Final polish", self.css)

    def test_retro_css_does_not_hide_horizontal_overflow_on_body(self):
        self.assertNotIn("overflow-x: hidden", self.css)

    def test_bootstrap_overrides_are_scoped_to_site_frame(self):
        forbidden_starts = (
            ".btn-",
            ".table ",
            ".table>",
            ".form-control",
            ".form-select",
            ".alert",
            ".display-6",
            ":focus-visible",
            "::selection",
        )
        unscoped = []
        for number, raw_line in enumerate(self.css.splitlines(), start=1):
            line = raw_line.strip()
            if line.startswith(forbidden_starts):
                unscoped.append(f"{number}: {line}")
        self.assertEqual(unscoped, [])

    def test_primary_layout_uses_bootstrap_grid(self):
        template = (Path(settings.BASE_DIR) / "templates/base.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('class="row g-2"', template)
        self.assertIn("col-12 col-md-9", template)
        self.assertIn("col-12 col-md-3", template)
