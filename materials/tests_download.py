"""US-8: protected file access and download statistics."""
import hashlib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import DocType, Document, DownloadLog


User = get_user_model()


class ProtectedDownloadTests(TestCase):
    def setUp(self):
        department = Department.objects.create(
            code="CN", name_th="Computer Engineering", name_en="Computer Engineering"
        )
        self.user = User.objects.create_user(
            email="6810610002@student.tu.ac.th", password="password123",
            nickname="download_tester", department=department,
            pdpa_consent_at=timezone.now(),
        )
        batch = Batch.objects.create(department=department, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        batch_course = BatchCourse.objects.create(batch=batch, course=course)
        doc_type = DocType.objects.create(code="summary", name_th="Summary", vault="lecture")
        self.document = Document.objects.create(
            batch_course=batch_course, doc_type=doc_type, uploader=self.user,
            title="Sample PDF", description="Test", status="published",
        )
        self.url = reverse("materials:document_download", args=[self.document.pk])

    def test_guest_cannot_download(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_pending_cannot_download(self):
        self.document.status = "pending"
        self.document.save(update_fields=["status"])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_missing_file_does_not_increment(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_success_increments_once_and_downloads_attachment(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            with override_settings(MEDIA_ROOT=temp):
                content = b"%PDF-1.4\n% test pdf\n"
                path = default_storage.save("us8-test.pdf", ContentFile(content))
                self.document.add_version(
                    storage_path=path, original_name="sample.pdf",
                    size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                )
                self.client.force_login(self.user)
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("attachment", response["Content-Disposition"])
                self.assertEqual(b"".join(response.streaming_content), content)
                self.assertEqual(DownloadLog.objects.filter(document=self.document).count(), 1)
                detail = self.client.get(reverse("materials:document_detail", args=[self.document.pk]))
                self.assertContains(detail, "ดาวน์โหลดแล้ว 1 ครั้ง")

    def test_guest_detail_does_not_download_or_log(self):
        detail_url = reverse("materials:document_detail", args=[self.document.pk])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_missing_storage_file_does_not_log(self):
        self.document.add_version(
            storage_path="missing-us8-file.pdf", original_name="missing.pdf",
            size_bytes=10, sha256="0" * 64,
        )
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_repeated_downloads_log_each_request_and_refresh_count(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            with override_settings(MEDIA_ROOT=temp):
                content = b"%PDF-1.4\n% repeated downloads\n"
                path = default_storage.save("us8-repeat.pdf", ContentFile(content))
                self.document.add_version(
                    storage_path=path, original_name="repeat.pdf",
                    size_bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                )
                self.client.force_login(self.user)
                for count in (1, 2):
                    response = self.client.get(self.url)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response["Cache-Control"], "private, no-store")
                    self.assertEqual(b"".join(response.streaming_content), content)
                    self.assertEqual(DownloadLog.objects.filter(document=self.document).count(), count)
                    detail = self.client.get(reverse("materials:document_detail", args=[self.document.pk]))
                    self.assertContains(detail, f"ดาวน์โหลดแล้ว {count} ครั้ง")
