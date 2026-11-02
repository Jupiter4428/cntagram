from django.test import TestCase

from catalog.models import SystemSetting

from ..models import max_upload_bytes, max_upload_mb


class UploadLimitTests(TestCase):
    def test_limit_defaults_to_50_mb_when_setting_is_missing(self):
        self.assertEqual(max_upload_mb(), 50)
        self.assertEqual(max_upload_bytes(), 52_428_800)

    def test_limit_set_above_the_db_ceiling_is_capped_at_50_mb(self):
        SystemSetting.objects.create(key=SystemSetting.MAX_UPLOAD_MB, value="100")

        self.assertEqual(max_upload_mb(), 50)
        self.assertEqual(max_upload_bytes(), 52_428_800)

    def test_limit_set_to_zero_falls_back_to_50_mb(self):
        SystemSetting.objects.create(key=SystemSetting.MAX_UPLOAD_MB, value="0")

        self.assertEqual(max_upload_mb(), 50)

    def test_limit_below_the_ceiling_comes_from_the_setting(self):
        SystemSetting.objects.create(key=SystemSetting.MAX_UPLOAD_MB, value="20")

        self.assertEqual(max_upload_mb(), 20)
        self.assertEqual(max_upload_bytes(), 20_971_520)
