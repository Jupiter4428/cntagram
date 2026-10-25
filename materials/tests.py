from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import Document, DocType, DocumentVersion, ExamDetail, ExamPeriod

User = get_user_model()


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


class MaterialsAdminTests(TestCase):
    """Django admin ของ materials (TD-3)"""

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin-password",
            nickname="Admin",
            department=cls.department,
        )
        cls.doc_type = DocType.objects.get_or_create(
            code="summary", defaults={"name_th": "สรุป", "vault": DocType.Vault.LECTURE}
        )[0]
        cls.document = cls._make_document(1)

    @classmethod
    def _make_document(cls, n):
        batch = Batch.objects.create(department=cls.department, number=n)
        course = Course.objects.create(code=f"CN{n}00", name_en=f"Course {n}")
        return Document.objects.create(
            batch_course=BatchCourse.objects.create(batch=batch, course=course),
            doc_type=cls.doc_type,
            uploader=User.objects.create_user(
                email=f"66100000{n:02d}@student.tu.ac.th",
                password="student-password",
                nickname=f"Student {n}",
                department=cls.department,
                pdpa_consent_at=timezone.now(),
            ),
            title=f"Summary {n}",
            description="-",
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist_opens_for_every_materials_model(self):
        for model in ("doctype", "examperiod", "document"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:materials_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_document_change_page_has_exam_detail_and_version_inlines(self):
        response = self.client.get(
            reverse("admin:materials_document_change", args=[self.document.pk])
        )

        inline_models = {
            inline.formset.model for inline in response.context["inline_admin_formsets"]
        }
        self.assertEqual(inline_models, {ExamDetail, DocumentVersion})

    def test_document_changelist_has_no_n_plus_1(self):
        self._make_document(2)
        self._make_document(3)

        with self.assertNumQueries(6):
            self.client.get(reverse("admin:materials_document_changelist"))

    def _post_new_document(self, doc_type, *, with_exam_detail):
        exam_period = ExamPeriod.objects.get_or_create(
            code="midterm", defaults={"name_th": "กลางภาค"}
        )[0]
        data = {
            "batch_course": self.document.batch_course_id,
            "doc_type": doc_type.pk if doc_type else "",
            "uploader": self.document.uploader_id,
            "title": "New document",
            "description": "-",
            "status": Document.Status.PENDING,
            "exam_detail-TOTAL_FORMS": "1",
            "exam_detail-INITIAL_FORMS": "0",
            "versions-TOTAL_FORMS": "0",
            "versions-INITIAL_FORMS": "0",
        }
        if with_exam_detail:
            data["exam_detail-0-exam_period"] = exam_period.pk
            data["exam_detail-0-exam_year_be"] = "2568"
        return self.client.post(reverse("admin:materials_document_add"), data)

    def test_admin_rejects_exam_detail_on_new_lecture_document(self):
        response = self._post_new_document(self.doc_type, with_exam_detail=True)

        self.assertContains(response, "exam_detail is only allowed for exam documents")
        self.assertFalse(Document.objects.filter(title="New document").exists())

    def test_admin_adds_lecture_document_without_exam_detail(self):
        response = self._post_new_document(self.doc_type, with_exam_detail=False)

        self.assertRedirects(response, reverse("admin:materials_document_changelist"))
        self.assertTrue(Document.objects.filter(title="New document").exists())

    def test_admin_adds_exam_document_with_exam_detail(self):
        exam_type = DocType.objects.get_or_create(
            code="exam", defaults={"name_th": "ข้อสอบ", "vault": DocType.Vault.EXAM}
        )[0]

        response = self._post_new_document(exam_type, with_exam_detail=True)

        self.assertRedirects(response, reverse("admin:materials_document_changelist"))
        self.assertTrue(
            ExamDetail.objects.filter(document__title="New document", exam_year_be=2568).exists()
        )

    def test_admin_shows_form_error_when_doc_type_is_missing(self):
        response = self._post_new_document(None, with_exam_detail=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("doc_type", response.context["adminform"].form.errors)
