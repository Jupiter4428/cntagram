import hashlib
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage

from catalog.models import SystemSetting

from ..models import Document
from ..services import upload_document
from .base import PDF_BYTES, UploadTestCase, pdf_file, stored_file_count


class UploadDocumentServiceTests(UploadTestCase):
    def upload(self, **overrides):
        kwargs = {
            "uploader": self.student,
            "batch_course": self.cn21_cn200,
            "doc_type": self.summary,
            "title": "สรุป CN200 บทที่ 1",
            "description": "ครบทุกหัวข้อ",
            "file": pdf_file(),
        }
        kwargs.update(overrides)
        return upload_document(**kwargs)

    def test_upload_stores_pdf_as_pending_document_with_first_version(self):
        document = self.upload()

        self.assertEqual(document.status, Document.Status.PENDING)
        self.assertEqual(document.uploader, self.student)
        version = document.current_version
        self.assertEqual(version.version_no, 1)
        self.assertEqual(version.original_name, "cn200-midterm.pdf")
        self.assertEqual(version.size_bytes, len(PDF_BYTES))
        self.assertEqual(version.sha256, hashlib.sha256(PDF_BYTES).hexdigest())
        self.assertRegex(
            version.storage_path, r"^vault/CN/21/CN200/summary/[0-9a-f]{32}\.pdf$"
        )
        with default_storage.open(version.storage_path, "rb") as stored:
            self.assertEqual(stored.read(), PDF_BYTES)

    def test_docx_file_is_rejected(self):
        docx = pdf_file(
            b"PK\x03\x04 fake docx",
            name="sheet.docx",
            content_type="application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document",
        )

        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=docx)

        self.assertEqual(ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"])
        self.assertFalse(Document.objects.exists())

    def test_exe_renamed_to_pdf_is_rejected_by_magic_bytes(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(b"MZ\x90\x00 fake exe", name="sheet.pdf"))

        self.assertEqual(ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"])
        self.assertFalse(Document.objects.exists())

    def test_pdf_bytes_with_non_pdf_mime_type_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(content_type="text/plain"))

        self.assertEqual(ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"])
        self.assertFalse(Document.objects.exists())

    def test_file_larger_than_max_upload_setting_is_rejected(self):
        SystemSetting.objects.filter(pk="max_upload_mb").update(value="1")
        too_big = PDF_BYTES + b"0" * 1_048_576
        files_before = stored_file_count()

        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(too_big))

        self.assertEqual(ctx.exception.message_dict["file"], ["ไฟล์ต้องมีขนาดไม่เกิน 1 MB"])
        self.assertFalse(Document.objects.exists())
        self.assertEqual(stored_file_count(), files_before)

    def test_exam_without_period_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(doc_type=self.exam, exam_year_be=2568)

        self.assertEqual(set(ctx.exception.message_dict), {"exam_period"})
        self.assertFalse(Document.objects.exists())

    def test_exam_without_year_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(doc_type=self.exam, exam_period=self.midterm)

        self.assertEqual(set(ctx.exception.message_dict), {"exam_year_be"})
        self.assertFalse(Document.objects.exists())

    def test_exam_without_period_and_year_reports_both_fields(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(doc_type=self.exam)

        self.assertEqual(set(ctx.exception.message_dict), {"exam_period", "exam_year_be"})
        self.assertFalse(Document.objects.exists())

    def test_exam_upload_records_exam_period_and_year(self):
        document = self.upload(
            doc_type=self.exam, exam_period=self.midterm, exam_year_be=2568
        )

        self.assertEqual(document.exam_detail.exam_period, self.midterm)
        self.assertEqual(document.exam_detail.exam_year_be, 2568)

    def test_stored_file_is_removed_when_database_write_fails(self):
        """ปี พ.ศ. นอกช่วงทำให้ ExamDetail.full_clean() ล้มหลังเก็บไฟล์และสร้าง Document แล้ว"""
        files_before = stored_file_count()

        with self.assertRaises(ValidationError):
            self.upload(doc_type=self.exam, exam_period=self.midterm, exam_year_be=1999)

        self.assertEqual(stored_file_count(), files_before)
        self.assertFalse(Document.objects.exists())

    def test_database_error_is_raised_even_when_file_cleanup_fails(self):
        with mock.patch.object(
            default_storage, "delete", side_effect=OSError("storage unavailable")
        ):
            with self.assertRaises(ValidationError) as ctx, self.assertLogs(
                "materials.services", "ERROR"
            ):
                self.upload(
                    doc_type=self.exam, exam_period=self.midterm, exam_year_be=1999
                )

        self.assertIn("exam_year_be", ctx.exception.message_dict)
        self.assertFalse(Document.objects.exists())

    def test_upload_into_another_department_is_denied(self):
        with self.assertRaises(PermissionDenied):
            self.upload(batch_course=self.me21_cn200)

        self.assertFalse(Document.objects.exists())
