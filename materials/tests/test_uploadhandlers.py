from django.core.files.uploadhandler import SkipFile
from django.test import RequestFactory, TestCase

from catalog.models import SystemSetting

from ..uploadhandlers import MaxSizeUploadHandler


class MaxSizeUploadHandlerTests(TestCase):
    def setUp(self):
        SystemSetting.objects.create(key=SystemSetting.MAX_UPLOAD_MB, value="1")
        self.request = RequestFactory().post("/")
        self.handler = MaxSizeUploadHandler(self.request)
        self.handler.new_file("file", "sheet.pdf", "application/pdf", None)

    def test_chunk_within_the_limit_is_passed_on(self):
        chunk = b"0" * 1_048_576

        self.assertEqual(self.handler.receive_data_chunk(chunk, 0), chunk)
        self.assertFalse(getattr(self.request, "upload_too_large", False))

    def test_chunk_past_the_limit_skips_the_file_and_flags_the_request(self):
        with self.assertRaises(SkipFile):
            self.handler.receive_data_chunk(b"0" * 65_536, 1_048_576 - 65_535)

        self.assertTrue(self.request.upload_too_large)
