import hashlib
import os
import shutil
import tempfile
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department, SystemSetting

from .models import DocType, Document, ExamPeriod
from .services import upload_document

User = get_user_model()

PDF_BYTES = b"%PDF-1.4\n% fake sheet\n%%EOF\n"


def pdf_file(content=PDF_BYTES, *, name="cn200-midterm.pdf", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


TEST_MEDIA_ROOT = tempfile.mkdtemp()


def stored_file_count():
    return sum(len(files) for _, _, files in os.walk(TEST_MEDIA_ROOT))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class UploadTestCase(TestCase):
    """ภาค CN มีรุ่น CN21 เรียน CN200 และภาค ME มีรุ่น ME21 เรียน CN200 เช่นกัน"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_materials", stdout=StringIO())
        cls.summary = DocType.objects.get(code="summary")
        cls.exam = DocType.objects.get(code="exam")
        cls.midterm = ExamPeriod.objects.get(code="midterm")
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        cls.cn21 = Batch.objects.create(department=cls.cn, number=21)
        cls.me21 = Batch.objects.create(department=cls.me, number=21)
        cls.cn21_cn200 = BatchCourse.objects.create(batch=cls.cn21, course=course)
        cls.me21_cn200 = BatchCourse.objects.create(batch=cls.me21, course=course)
        cls.student = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="correct-horse-battery-staple",
            nickname="Ton",
            department=cls.cn,
            pdpa_consent_at=timezone.now(),
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


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

    def test_non_pdf_file_is_rejected_by_mime_type_and_magic_bytes(self):
        cases = {
            "docx": pdf_file(
                b"PK\x03\x04 fake docx",
                name="sheet.docx",
                content_type="application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            ),
            "renamed exe": pdf_file(b"MZ\x90\x00 fake exe", name="sheet.pdf"),
            "pdf bytes, wrong mime": pdf_file(content_type="text/plain"),
        }
        for label, file in cases.items():
            with self.subTest(label), self.assertRaises(ValidationError) as ctx:
                self.upload(file=file)
            self.assertIn("file", ctx.exception.message_dict)
        self.assertFalse(Document.objects.exists())

    def test_file_larger_than_max_upload_setting_is_rejected(self):
        SystemSetting.objects.filter(pk="max_upload_mb").update(value="1")
        too_big = PDF_BYTES + b"0" * (1024 * 1024)
        files_before = stored_file_count()

        with self.assertRaises(ValidationError) as ctx:
            self.upload(file=pdf_file(too_big))

        self.assertEqual(ctx.exception.message_dict["file"], ["ไฟล์ต้องมีขนาดไม่เกิน 1 MB"])
        self.assertFalse(Document.objects.exists())
        self.assertEqual(stored_file_count(), files_before)

    def test_exam_without_period_or_year_is_rejected(self):
        cases = {
            "no period": {"exam_year_be": 2568},
            "no year": {"exam_period": self.midterm},
            "neither": {},
        }
        for label, exam_fields in cases.items():
            with self.subTest(label), self.assertRaises(ValidationError):
                self.upload(doc_type=self.exam, **exam_fields)
        self.assertFalse(Document.objects.exists())

    def test_exam_upload_records_exam_period_and_year(self):
        document = self.upload(
            doc_type=self.exam, exam_period=self.midterm, exam_year_be=2568
        )

        self.assertEqual(document.exam_detail.exam_period, self.midterm)
        self.assertEqual(document.exam_detail.exam_year_be, 2568)

    def test_stored_file_is_removed_when_database_write_fails(self):
        files_before = stored_file_count()

        with mock.patch.object(Document, "add_version", side_effect=RuntimeError("db down")):
            with self.assertRaises(RuntimeError):
                self.upload()

        self.assertEqual(stored_file_count(), files_before)
        self.assertFalse(Document.objects.exists())

    def test_upload_into_another_department_is_denied(self):
        with self.assertRaises(PermissionDenied):
            self.upload(batch_course=self.me21_cn200)
        self.assertFalse(Document.objects.exists())


class SeedMaterialsCommandTests(TestCase):
    def seed(self):
        call_command("seed_materials", stdout=StringIO())

    def test_seeds_doc_types_exam_periods_and_settings(self):
        self.seed()

        self.assertEqual(
            dict(DocType.objects.values_list("code", "vault")),
            {
                "summary": "lecture",
                "slide": "lecture",
                "cheatsheet": "lecture",
                "exam": "exam",
            },
        )
        self.assertEqual(
            set(ExamPeriod.objects.values_list("code", flat=True)), {"midterm", "final"}
        )
        self.assertEqual(SystemSetting.get_int("max_upload_mb"), 50)
        self.assertEqual(SystemSetting.get_int("legacy_batch_max"), 23)

    def test_rerun_does_not_duplicate_or_overwrite_admin_changes(self):
        self.seed()
        SystemSetting.objects.filter(pk="max_upload_mb").update(value="20")

        self.seed()

        self.assertEqual(DocType.objects.count(), 4)
        self.assertEqual(ExamPeriod.objects.count(), 2)
        self.assertEqual(SystemSetting.get_int("max_upload_mb"), 20)


class UploadViewTests(UploadTestCase):
    def setUp(self):
        self.client.force_login(self.student)

    def post(self, **overrides):
        data = {
            "batch_course": self.cn21_cn200.pk,
            "doc_type": self.summary.pk,
            "title": "สรุป CN200",
            "description": "บทที่ 1-3",
            "file": pdf_file(),
            "disclaimer": "on",
        }
        data.update(overrides)
        return self.client.post(reverse("materials:upload"), data)

    def test_guest_is_redirected_to_login(self):
        self.client.logout()
        url = reverse("materials:upload")

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_form_locks_department_and_lists_only_its_batches(self):
        response = self.client.get(reverse("materials:upload"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["department"], self.cn)
        self.assertEqual(list(response.context["batches"]), [self.cn21])

    def test_successful_upload_is_pending_and_shows_waiting_page(self):
        response = self.post()

        self.assertRedirects(response, reverse("materials:upload_done"))
        self.assertEqual(Document.objects.get().status, Document.Status.PENDING)
        self.assertContains(self.client.get(response["Location"]), "รออนุมัติ")

    def test_upload_without_disclaimer_is_rejected(self):
        response = self.post(disclaimer="")

        self.assertEqual(response.status_code, 200)
        self.assertIn("disclaimer", response.context["form"].errors)
        self.assertFalse(Document.objects.exists())

    def test_tampered_request_into_another_department_is_403(self):
        response = self.post(batch_course=self.me21_cn200.pk)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Document.objects.exists())

    def test_exam_without_year_shows_field_error(self):
        response = self.post(doc_type=self.exam.pk, exam_period=self.midterm.pk)

        self.assertEqual(response.status_code, 200)
        self.assertIn("exam_year_be", response.context["form"].errors)
        self.assertFalse(Document.objects.exists())

    def test_model_error_outside_form_fields_is_shown_not_500(self):
        error = ValidationError({"size_bytes": "File is larger than 50 MB"})
        with mock.patch("materials.views.upload_document", side_effect=error):
            response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].non_field_errors(), ["File is larger than 50 MB"]
        )

    def test_form_page_query_count_does_not_grow_with_batches(self):
        for number in range(22, 27):
            Batch.objects.create(department=self.cn, number=number)

        with self.assertNumQueries(6):
            self.client.get(reverse("materials:upload"))

    def test_non_pdf_shows_file_error(self):
        response = self.post(file=pdf_file(b"PK\x03\x04", name="sheet.docx"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].errors["file"], ["รับเฉพาะไฟล์ PDF เท่านั้น"])


class UploadCourseOptionsViewTests(UploadTestCase):
    def setUp(self):
        self.client.force_login(self.student)

    def test_lists_courses_of_a_batch_in_own_department(self):
        response = self.client.get(
            reverse("materials:upload_course_options", args=[self.cn21.pk])
        )

        self.assertEqual(
            response.json(),
            {
                "courses": [
                    {
                        "id": self.cn21_cn200.pk,
                        "code": "CN200",
                        "name": "Discrete Mathematics",
                    }
                ]
            },
        )

    def test_course_options_query_count_does_not_grow_with_courses(self):
        for code in ("CN201", "CN202", "CN203"):
            BatchCourse.objects.create(
                batch=self.cn21, course=Course.objects.create(code=code, name_en=code)
            )

        with self.assertNumQueries(4):
            self.client.get(
                reverse("materials:upload_course_options", args=[self.cn21.pk])
            )

    def test_batch_of_another_department_is_403(self):
        response = self.client.get(
            reverse("materials:upload_course_options", args=[self.me21.pk])
        )

        self.assertEqual(response.status_code, 403)


class BatchCourseWithDocumentsTests(TestCase):
    def test_cannot_remove_course_that_has_documents(self):
        """ถอดวิชาออกจากรุ่นไม่ได้ ถ้ามีเอกสารอัปโหลดอยู่ในวิชานั้นแล้ว (US-4)"""
        dept = Department.objects.create(code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering")
        admin = User.objects.create_user(
            email="6810610002@student.tu.ac.th",
            password="password123",
            nickname="admin_test",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        role, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        UserRole.objects.create(user=admin, role=role)
        batch = Batch.objects.create(department=dept, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        batch_course = BatchCourse.objects.create(batch=batch, course=course)
        doc_type = DocType.objects.create(code="summary", name_th="สรุป", vault=DocType.Vault.LECTURE)
        Document.objects.create(
            batch_course=batch_course, doc_type=doc_type, uploader=admin, title="สรุปบทที่ 1", description="-"
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse("catalog:batch_course_remove", args=[batch.pk, batch_course.pk]),
            follow=True,
        )

        self.assertTrue(BatchCourse.objects.filter(pk=batch_course.pk).exists())
        self.assertContains(response, "ถอดวิชา CN200 ไม่ได้ เพราะมีเอกสารอัปโหลดอยู่ในวิชานี้แล้ว")
