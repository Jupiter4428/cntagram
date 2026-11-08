import os
import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.test import TestCase

from django.utils import timezone
from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import DocType, Document, ExamPeriod
from materials.services import bulk_import_documents_from_csv
from materials.tests.base import PDF_BYTES

CSV_HEADER = (
    "file_path,department,batch,course,doc_type,title,"
    "description,exam_period,exam_year_be\n"
)


class BulkImportServiceTests(TestCase):
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
        cls.exam = DocType.objects.create(
            code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM
        )
        cls.midterm = ExamPeriod.objects.create(code="midterm", name_th="กลางภาค")

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

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        self.pdf_filename = "test_sheet.pdf"
        self.pdf_full_path = os.path.join(self.temp_dir, self.pdf_filename)
        with open(self.pdf_full_path, "wb") as f:
            f.write(PDF_BYTES)

    def test_regular_user_cannot_bulk_import(self):
        csv_content = (
            CSV_HEADER
            + f"{self.pdf_filename},CN,21,CN200,summary,สรุปบทที่ 1,คำอธิบาย,,\n"
        )
        with self.assertRaises(ValidationError) as ctx:
            bulk_import_documents_from_csv(
                csv_content=csv_content,
                files_dir=self.temp_dir,
                user=self.regular_user,
                dry_run=False,
            )
        self.assertIn("เฉพาะ Super Admin", str(ctx.exception))

    def test_dry_run_valid_row_does_not_write_db_or_storage(self):
        csv_content = (
            CSV_HEADER
            + f"{self.pdf_filename},CN,21,CN200,summary,สรุปบทที่ 1,คำอธิบาย,,\n"
        )
        summary = bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=True,
        )
        self.assertEqual(summary.total_rows, 1)
        self.assertEqual(summary.imported_count, 1)
        self.assertEqual(summary.skipped_count, 0)
        self.assertEqual(summary.failed_count, 0)
        self.assertEqual(Document.objects.count(), 0)

    def test_real_run_imports_published_document(self):
        csv_content = (
            CSV_HEADER
            + f"{self.pdf_filename},CN,21,CN200,summary,สรุปบทที่ 1,คำอธิบาย,,\n"
        )
        summary = bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=False,
        )
        self.assertEqual(summary.imported_count, 1)
        doc = Document.objects.first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        self.assertEqual(doc.uploader, self.admin_user)
        self.assertEqual(doc.title, "สรุปบทที่ 1")
        self.assertEqual(doc.versions.count(), 1)
        self.assertTrue(default_storage.exists(doc.current_version.storage_path))

    def test_exam_detail_imported_properly(self):
        csv_content = (
            CSV_HEADER
            + f"{self.pdf_filename},CN,21,CN200,exam,"
            "ข้อสอบกลางภาค,ข้อสอบ 2568,midterm,2568\n"
        )
        summary = bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=False,
        )
        self.assertEqual(summary.imported_count, 1)
        doc = Document.objects.first()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        self.assertEqual(doc.exam_detail.exam_period, self.midterm)
        self.assertEqual(doc.exam_detail.exam_year_be, 2568)

    def test_duplicate_file_is_skipped(self):
        csv_content = (
            CSV_HEADER + f"{self.pdf_filename},CN,21,CN200,summary,สรุป 1,,,,\n"
        )
        # Import once
        bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=False,
        )
        self.assertEqual(Document.objects.count(), 1)

        # Import again with different title but same file
        csv_content_2 = (
            CSV_HEADER + f"{self.pdf_filename},CN,21,CN200,summary,สรุป 2,,,,\n"
        )
        summary = bulk_import_documents_from_csv(
            csv_content=csv_content_2,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=False,
        )
        self.assertEqual(summary.imported_count, 0)
        self.assertEqual(summary.skipped_count, 1)
        self.assertIn("ไฟล์ซ้ำ", summary.results[0].message)
        self.assertEqual(Document.objects.count(), 1)

    def test_invalid_rows_reported_and_valid_rows_imported(self):
        csv_content = (
            CSV_HEADER
            + "non_existent.pdf,CN,21,CN200,summary,สรุป 1,,,,\n"
            + f"{self.pdf_filename},CN,99,CN200,summary,สรุป 2,,,,\n"
            + f"{self.pdf_filename},CN,21,CN999,summary,สรุป 3,,,,\n"
            + f"{self.pdf_filename},CN,21,CN200,summary,สรุปถูกต้อง,,,,\n"
        )
        summary = bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=self.temp_dir,
            user=self.admin_user,
            dry_run=False,
        )
        self.assertEqual(summary.total_rows, 4)
        self.assertEqual(summary.failed_count, 3)
        self.assertEqual(summary.imported_count, 1)
        self.assertEqual(Document.objects.count(), 1)
        self.assertEqual(Document.objects.first().title, "สรุปถูกต้อง")
