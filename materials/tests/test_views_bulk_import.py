import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import DocType, Document
from materials.tests.base import PDF_BYTES

CSV_HEADER = (
    "file_path,department,batch,course,doc_type,title,"
    "description,exam_period,exam_year_be\n"
)


class BulkImportViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.batch21 = Batch.objects.create(department=cls.dept, number=21)
        cls.course = Course.objects.create(code="CN200", name_en="Discrete Math")
        cls.batch_course = BatchCourse.objects.create(
            batch=cls.batch21, course=cls.course
        )

        cls.summary = DocType.objects.create(
            code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE
        )

        from django.contrib.auth import get_user_model

        User = get_user_model()
        cls.admin_role, _ = Role.objects.get_or_create(
            code="super_admin", defaults={"name_th": "ผู้ดูแลระบบสูงสุด"}
        )
        cls.admin_user = User.objects.create_user(
            email="6510610001@student.tu.ac.th",
            password="admin-password-123",
            nickname="Admin",
            department=cls.dept,
            pdpa_consent_at=timezone.now(),
        )
        UserRole.objects.create(user=cls.admin_user, role=cls.admin_role)

        cls.regular_user = User.objects.create_user(
            email="6510610002@student.tu.ac.th",
            password="user-password-123",
            nickname="NormalUser",
            department=cls.dept,
            pdpa_consent_at=timezone.now(),
        )

        cls.url = reverse("materials:bulk_import")

    def _create_zip_file(self, files_dict):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in files_dict.items():
                zf.writestr(fname, content)
        bio.seek(0)
        return bio.getvalue()

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_regular_user_forbidden(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_super_admin_get_renders_form(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/bulk_import.html")

    def test_super_admin_dry_run_post(self):
        self.client.force_login(self.admin_user)
        csv_row = "sheet.pdf,CN,21,CN200,summary,ชีทสรุป 1,,,,\n"
        csv_bytes = (CSV_HEADER + csv_row).encode("utf-8")
        zip_bytes = self._create_zip_file({"sheet.pdf": PDF_BYTES})

        csv_file = SimpleUploadedFile("data.csv", csv_bytes, content_type="text/csv")
        zip_file = SimpleUploadedFile(
            "files.zip", zip_bytes, content_type="application/zip"
        )

        response = self.client.post(
            self.url,
            {
                "csv_file": csv_file,
                "zip_file": zip_file,
                "dry_run": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/bulk_import.html")
        self.assertTrue(response.context["has_run"])
        self.assertTrue(response.context["dry_run"])
        summary = response.context["summary"]
        self.assertEqual(summary.total_rows, 1)
        self.assertEqual(summary.imported_count, 1)
        self.assertEqual(Document.objects.count(), 0)

    def test_super_admin_real_run_post(self):
        self.client.force_login(self.admin_user)
        csv_row = "sheet.pdf,CN,21,CN200,summary,ชีทสรุป 1,,,,\n"
        csv_bytes = (CSV_HEADER + csv_row).encode("utf-8")
        zip_bytes = self._create_zip_file({"sheet.pdf": PDF_BYTES})

        csv_file = SimpleUploadedFile("data.csv", csv_bytes, content_type="text/csv")
        zip_file = SimpleUploadedFile(
            "files.zip", zip_bytes, content_type="application/zip"
        )

        response = self.client.post(
            self.url,
            {
                "csv_file": csv_file,
                "zip_file": zip_file,
                # dry_run unchecked
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/bulk_import.html")
        self.assertTrue(response.context["has_run"])
        self.assertFalse(response.context["dry_run"])
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.title, "ชีทสรุป 1")
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
