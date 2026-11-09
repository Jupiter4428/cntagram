from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class BrandAssetsContractTests(SimpleTestCase):
    def test_brand_static_assets_exist_on_disk(self):
        static_img = Path(settings.BASE_DIR) / "static" / "img"
        expected_files = [
            "favicon.ico",
            "favicon-16x16.png",
            "favicon-32x32.png",
            "logo.png",
            "cntagram-button-88x31.png",
        ]
        for filename in expected_files:
            file_path = static_img / filename
            self.assertTrue(
                file_path.is_file(), f"Expected static asset missing: {filename}"
            )
            self.assertGreater(
                file_path.stat().st_size, 0, f"Static asset is empty: {filename}"
            )

    def test_base_template_includes_favicons(self):
        template = (Path(settings.BASE_DIR) / "templates/base.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("favicon.ico", template)
        self.assertIn("favicon-32x32.png", template)
        self.assertIn("favicon-16x16.png", template)

    def test_base_template_includes_site_brand_logo(self):
        template = (Path(settings.BASE_DIR) / "templates/base.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("site-brand__logo", template)
        self.assertIn("img/logo", template)

    def test_footer_includes_retro_88x31_button(self):
        footer_template = (
            Path(settings.BASE_DIR) / "templates/includes/_footer.html"
        ).read_text(encoding="utf-8")
        self.assertIn("cntagram-button-88x31.png", footer_template)
