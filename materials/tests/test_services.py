import hashlib
from unittest import mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone

from accounts.models import User
from catalog.models import SystemSetting

from ..models import Document, DownloadLog
from ..services import (
    add_document_version,
    delete_document,
    hide_document,
    record_download,
    update_document_info,
    upload_document,
)
from .base import (
    PDF_BYTES,
    ApprovalBaseTestCase,
    SearchTestCase,
    UploadTestCase,
    pdf_file,
    stored_file_count,
)


class RecordDownloadServiceTests(SearchTestCase):
    def test_record_download_creates_log_for_document_and_user(self):
        document = self.make_document(self.cn200[21], title="Download service test")
        log = record_download(document=document, user=self.uploader)
        self.assertEqual(log.document, document)
        self.assertEqual(log.user, self.uploader)
        self.assertEqual(DownloadLog.objects.filter(document=document).count(), 1)


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

        self.assertEqual(
            ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"]
        )
        self.assertFalse(Document.objects.exists())

    def test_exe_renamed_to_pdf_is_rejected_by_magic_bytes(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(b"MZ\x90\x00 fake exe", name="sheet.pdf"))

        self.assertEqual(
            ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"]
        )
        self.assertFalse(Document.objects.exists())

    def test_pdf_bytes_with_non_pdf_mime_type_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(content_type="text/plain"))

        self.assertEqual(
            ctx.exception.message_dict["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"]
        )
        self.assertFalse(Document.objects.exists())

    def test_file_larger_than_max_upload_setting_is_rejected(self):
        SystemSetting.objects.filter(pk="max_upload_mb").update(value="1")
        too_big = PDF_BYTES + b"0" * 1_048_576
        files_before = stored_file_count()

        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(too_big))

        self.assertEqual(
            ctx.exception.message_dict["file"], ["ไฟล์ต้องมีขนาดไม่เกิน 1 MB"]
        )
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

        self.assertEqual(
            set(ctx.exception.message_dict), {"exam_period", "exam_year_be"}
        )
        self.assertFalse(Document.objects.exists())

    def test_exam_upload_records_exam_period_and_year(self):
        document = self.upload(
            doc_type=self.exam, exam_period=self.midterm, exam_year_be=2568
        )

        self.assertEqual(document.exam_detail.exam_period, self.midterm)
        self.assertEqual(document.exam_detail.exam_year_be, 2568)

    def test_stored_file_is_removed_when_database_write_fails(self):
        """ปี พ.ศ. นอกช่วงทำให้ ExamDetail.full_clean() ล้มหลังเก็บไฟล์และสร้าง Document แล้ว"""  # noqa: E501
        files_before = stored_file_count()

        with self.assertRaises(ValidationError):
            self.upload(doc_type=self.exam, exam_period=self.midterm, exam_year_be=1999)

        self.assertEqual(stored_file_count(), files_before)
        self.assertFalse(Document.objects.exists())

    def test_database_error_is_raised_even_when_file_cleanup_fails(self):
        with mock.patch.object(
            default_storage, "delete", side_effect=OSError("storage unavailable")
        ):
            with (
                self.assertRaises(ValidationError) as ctx,
                self.assertLogs("materials.services", "ERROR"),
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


class HideDocumentServiceTests(ApprovalBaseTestCase):
    def setUp(self):
        super().setUp()
        self.doc_cn = self.create_document(
            batch_course=self.bc_cn,
            status=Document.Status.PUBLISHED,
        )
        self.doc_me = self.create_document(
            batch_course=self.bc_me,
            status=Document.Status.PUBLISHED,
        )

    def test_super_admin_can_hide_published_document_with_reason(self):
        doc = hide_document(
            document=self.doc_cn,
            user=self.super_admin,
            reason="พบการละเมิดลิขสิทธิ์เนื้อหา",
        )
        self.doc_cn.refresh_from_db()
        self.assertEqual(self.doc_cn.status, Document.Status.HIDDEN)
        self.assertEqual(doc.status, Document.Status.HIDDEN)

    def test_moderator_can_hide_own_department_document(self):
        hide_document(
            document=self.doc_cn,
            user=self.mod_cn,
            reason="ข้อสอบเก่าไม่อนุญาตให้เผยแพร่",
        )
        self.doc_cn.refresh_from_db()
        self.assertEqual(self.doc_cn.status, Document.Status.HIDDEN)

    def test_moderator_cannot_hide_other_department_document(self):
        with self.assertRaises(PermissionDenied):
            hide_document(
                document=self.doc_me,
                user=self.mod_cn,
                reason="ข้ามภาควิชา",
            )
        self.doc_me.refresh_from_db()
        self.assertEqual(self.doc_me.status, Document.Status.PUBLISHED)

    def test_normal_student_cannot_hide_document(self):
        with self.assertRaises(PermissionDenied):
            hide_document(
                document=self.doc_cn,
                user=self.normal_student,
                reason="อยากซ่อน",
            )
        self.doc_cn.refresh_from_db()
        self.assertEqual(self.doc_cn.status, Document.Status.PUBLISHED)

    def test_hiding_without_reason_fails_validation(self):
        for empty_reason in ("", "   ", None):
            with self.assertRaises(ValidationError):
                hide_document(
                    document=self.doc_cn,
                    user=self.super_admin,
                    reason=empty_reason,
                )
            self.doc_cn.refresh_from_db()
            self.assertEqual(self.doc_cn.status, Document.Status.PUBLISHED)

    def test_cannot_hide_non_published_document(self):
        pending_doc = self.create_document(
            batch_course=self.bc_cn,
            status=Document.Status.PENDING,
        )
        with self.assertRaises(ValidationError):
            hide_document(
                document=pending_doc,
                user=self.super_admin,
                reason="ยังไม่อนุมัติแต่สั่งซ่อน",
            )
        pending_doc.refresh_from_db()
        self.assertEqual(pending_doc.status, Document.Status.PENDING)


class UpdateDocumentInfoServiceTests(UploadTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="other-password",
            nickname="Other",
            department=self.cn,
            pdpa_consent_at=timezone.now(),
        )
        self.document = upload_document(
            uploader=self.student,
            batch_course=self.cn21_cn200,
            doc_type=self.summary,
            title="สรุป CN200 บทที่ 1",
            description="ครบทุกหัวข้อ",
            file=pdf_file(),
        )

    def test_owner_can_update_document_info(self):
        updated = update_document_info(
            document=self.document,
            actor=self.student,
            title="สรุป CN200 บทที่ 1-2 (ฉบับแก้ไข)",
            description="แก้สูตรหน้า 3 แล้ว",
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.title, "สรุป CN200 บทที่ 1-2 (ฉบับแก้ไข)")
        self.assertEqual(self.document.description, "แก้สูตรหน้า 3 แล้ว")
        self.assertEqual(updated.pk, self.document.pk)

    def test_non_owner_cannot_update_document_info(self):
        with self.assertRaises(PermissionDenied):
            update_document_info(
                document=self.document,
                actor=self.other_user,
                title="พยายามแก้ชื่อ",
                description="คำอธิบายใหม่",
            )
        self.document.refresh_from_db()
        self.assertEqual(self.document.title, "สรุป CN200 บทที่ 1")

    def test_empty_title_fails_validation(self):
        for bad_title in ("", "   ", None):
            with self.subTest(title=bad_title):
                with self.assertRaises(ValidationError):
                    update_document_info(
                        document=self.document,
                        actor=self.student,
                        title=bad_title,
                        description="คำอธิบาย",
                    )
        self.document.refresh_from_db()
        self.assertEqual(self.document.title, "สรุป CN200 บทที่ 1")


class AddDocumentVersionServiceTests(UploadTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="other-password",
            nickname="Other",
            department=self.cn,
            pdpa_consent_at=timezone.now(),
        )
        self.document = upload_document(
            uploader=self.student,
            batch_course=self.cn21_cn200,
            doc_type=self.summary,
            title="สรุป CN200 บทที่ 1",
            description="ครบทุกหัวข้อ",
            file=pdf_file(),
        )

    def test_owner_can_upload_new_version(self):
        new_pdf = pdf_file(
            name="cn200-v2.pdf",
            content=b"%PDF-1.4\nNew version content\n%%EOF",
        )
        version = add_document_version(
            document=self.document,
            actor=self.student,
            file=new_pdf,
        )
        self.assertEqual(version.version_no, 2)
        self.assertEqual(version.original_name, "cn200-v2.pdf")
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_version.version_no, 2)
        with default_storage.open(version.storage_path, "rb") as stored:
            self.assertEqual(
                stored.read(), b"%PDF-1.4\nNew version content\n%%EOF"
            )

    def test_non_owner_cannot_upload_new_version(self):
        new_pdf = pdf_file(
            name="cn200-hacked.pdf",
            content=b"%PDF-1.4\nHacked\n%%EOF",
        )
        with self.assertRaises(PermissionDenied):
            add_document_version(
                document=self.document,
                actor=self.other_user,
                file=new_pdf,
            )
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_version.version_no, 1)

    def test_invalid_pdf_is_rejected(self):
        bad_file = pdf_file(
            name="not-a-pdf.docx",
            content=b"not a real pdf content",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )
        with self.assertRaises(ValidationError):
            add_document_version(
                document=self.document,
                actor=self.student,
                file=bad_file,
            )
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_version.version_no, 1)

    def test_duplicate_pdf_in_vault_is_rejected(self):
        duplicate_pdf = pdf_file()
        with self.assertRaises(ValidationError):
            add_document_version(
                document=self.document,
                actor=self.student,
                file=duplicate_pdf,
            )
        self.document.refresh_from_db()
        self.assertEqual(self.document.current_version.version_no, 1)


class DeleteDocumentServiceTests(UploadTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="other-password",
            nickname="Other",
            department=self.cn,
            pdpa_consent_at=timezone.now(),
        )
        self.document = upload_document(
            uploader=self.student,
            batch_course=self.cn21_cn200,
            doc_type=self.summary,
            title="สรุป CN200 บทที่ 1",
            description="ครบทุกหัวข้อ",
            file=pdf_file(),
        )

    def test_owner_can_delete_document_and_files(self):
        storage_path = self.document.current_version.storage_path
        self.assertTrue(default_storage.exists(storage_path))

        delete_document(
            document=self.document,
            actor=self.student,
        )

        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())
        self.assertFalse(default_storage.exists(storage_path))

    def test_non_owner_cannot_delete_document(self):
        with self.assertRaises(PermissionDenied):
            delete_document(
                document=self.document,
                actor=self.other_user,
            )
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())
