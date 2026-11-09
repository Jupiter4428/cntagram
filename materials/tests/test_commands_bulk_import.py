import io
import os
import shutil
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import DocType, Document, ExamPeriod
from materials.tests.base import PDF_BYTES

CSV_HEADER = (
    "file_path,department,batch,course,doc_type,title,"
    "description,exam_period,exam_year_be\n"
)


class ImportDocumentsCommandTests(TestCase):
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

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        self.pdf_filename = "sheet.pdf"
        self.pdf_full_path = os.path.join(self.temp_dir, self.pdf_filename)
        with open(self.pdf_full_path, "wb") as f:
            f.write(PDF_BYTES)

        self.csv_path = os.path.join(self.temp_dir, "import.csv")
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write(
                CSV_HEADER
                + f"{self.pdf_filename},CN,21,CN200,summary,CN200 สรุป,ละเอียด,,\n"
            )

    def test_command_requires_existing_csv(self):
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "import_documents",
                "not_found.csv",
                files_dir=self.temp_dir,
                user_email=self.admin_user.email,
            )
        self.assertIn("ไม่พบไฟล์ CSV", str(ctx.exception))

    def test_command_requires_super_admin_user(self):
        with self.assertRaises(CommandError) as ctx:
            call_command(
                "import_documents",
                self.csv_path,
                files_dir=self.temp_dir,
                user_email="nonexistent@student.tu.ac.th",
            )
        self.assertIn("ไม่พบผู้ใช้", str(ctx.exception))

    def test_command_dry_run(self):
        out = io.StringIO()
        call_command(
            "import_documents",
            self.csv_path,
            files_dir=self.temp_dir,
            user_email=self.admin_user.email,
            dry_run=True,
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("ผ่าน 1 แถว", output)
        self.assertEqual(Document.objects.count(), 0)

    def test_command_real_run(self):
        out = io.StringIO()
        call_command(
            "import_documents",
            self.csv_path,
            files_dir=self.temp_dir,
            user_email=self.admin_user.email,
            dry_run=False,
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn("นำเข้าสำเร็จ 1 แถว", output)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.title, "CN200 สรุป")
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
