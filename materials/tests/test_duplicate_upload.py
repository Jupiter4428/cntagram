from django.core.exceptions import ValidationError

from ..models import Document, DocumentVersion
from ..services import upload_document
from .base import PDF_BYTES, UploadTestCase, pdf_file, stored_file_count


class DuplicateUploadTests(UploadTestCase):
    def upload(self, content=PDF_BYTES):
        return upload_document(
            uploader=self.student,
            batch_course=self.cn21_cn200,
            doc_type=self.summary,
            title="CN200 notes",
            description="",
            file=pdf_file(content),
        )

    def test_pending_duplicate_is_rejected_without_storage_or_db_changes(self):
        self.upload()
        before = stored_file_count()
        with self.assertRaises(ValidationError) as ctx:
            self.upload()
        self.assertEqual(
            ctx.exception.message_dict["file"], ["ไฟล์นี้มีอยู่ในคลังแล้ว"]
        )
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(DocumentVersion.objects.count(), 1)
        self.assertEqual(stored_file_count(), before)

    def test_published_duplicate_is_rejected(self):
        doc = self.upload()
        doc.status = Document.Status.PUBLISHED
        doc.save(update_fields=["status"])
        before = stored_file_count()
        with self.assertRaises(ValidationError):
            self.upload()
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(DocumentVersion.objects.count(), 1)
        self.assertEqual(stored_file_count(), before)

    def test_rejected_duplicate_is_allowed(self):
        doc = self.upload()
        doc.status = Document.Status.REJECTED
        doc.save(update_fields=["status"])
        new_doc = self.upload()
        self.assertNotEqual(doc.pk, new_doc.pk)
        self.assertEqual(Document.objects.count(), 2)

    def test_hidden_duplicate_is_allowed(self):
        doc = self.upload()
        doc.status = Document.Status.HIDDEN
        doc.save(update_fields=["status"])
        new_doc = self.upload()
        self.assertNotEqual(doc.pk, new_doc.pk)
        self.assertEqual(Document.objects.count(), 2)

    def test_different_file_is_allowed(self):
        self.upload()
        other = self.upload(PDF_BYTES + b"extra content")
        self.assertEqual(other.status, Document.Status.PENDING)
        self.assertEqual(Document.objects.count(), 2)
