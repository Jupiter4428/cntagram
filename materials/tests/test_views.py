from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from ..models import Document, DocType
from .base import UploadTestCase, pdf_file

User = get_user_model()


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
        self.assertTemplateUsed(response, "materials/upload.html")
        self.assertEqual(response.context["department"], self.cn)
        self.assertEqual(list(response.context["batches"]), [self.cn21])

    def test_successful_upload_saves_pending_document_and_redirects(self):
        response = self.post()

        self.assertRedirects(response, reverse("materials:upload_done"))
        self.assertEqual(Document.objects.get().status, Document.Status.PENDING)

    def test_upload_done_page_says_waiting_for_approval(self):
        response = self.client.get(reverse("materials:upload_done"))

        self.assertTemplateUsed(response, "materials/upload_done.html")
        self.assertContains(response, "รออนุมัติ")

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
