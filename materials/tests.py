import shutil
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from .forms import SearchForm
from .models import DocType, Document
from .selectors import search_documents


class SearchFixtureMixin:
    """CN21-CN23 เรียน CN200 ทุกรุ่น และ CN22 มี CN201 ด้วย"""

    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.uploader = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="correct-horse-battery-staple",
            nickname="Uploader",
            department=cls.cn,
            pdpa_consent_at=timezone.now(),
        )
        cls.summary = DocType.objects.create(
            code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE
        )
        cls.exam = DocType.objects.create(
            code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM
        )
        cn200 = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        cn201 = Course.objects.create(code="CN201", name_en="Data Structures")
        cls.batches = {
            n: Batch.objects.create(department=cls.cn, number=n) for n in (21, 22, 23)
        }
        cls.cn200 = {
            n: BatchCourse.objects.create(batch=batch, course=cn200)
            for n, batch in cls.batches.items()
        }
        cls.cn201_cn22 = BatchCourse.objects.create(
            batch=cls.batches[22], course=cn201
        )

    @classmethod
    def make_document(cls, batch_course, *, title, doc_type=None, status="published"):
        return Document.objects.create(
            batch_course=batch_course,
            doc_type=doc_type or cls.summary,
            uploader=cls.uploader,
            title=title,
            description="-",
            status=status,
        )


class SearchDocumentsTests(SearchFixtureMixin, TestCase):
    def test_returns_published_documents_of_the_course_from_every_batch(self):
        expected = {
            self.make_document(self.cn200[n], title=f"CN200 CN{n}").pk
            for n in (21, 22, 23)
        }
        self.make_document(self.cn200[21], title="pending", status="pending")
        self.make_document(self.cn200[22], title="hidden", status="hidden")
        self.make_document(self.cn201_cn22, title="other course")

        result = search_documents(course_code="cn200")

        self.assertEqual({doc.pk for doc in result}, expected)

    def test_filters_by_department_batch_and_doc_type(self):
        cn22_exam = self.make_document(
            self.cn200[22], title="CN22 exam", doc_type=self.exam
        )
        self.make_document(self.cn200[22], title="CN22 summary")
        self.make_document(self.cn200[21], title="CN21 exam", doc_type=self.exam)
        ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )
        ce_batch = Batch.objects.create(department=ce, number=22)
        ce_cn200 = BatchCourse.objects.create(
            batch=ce_batch, course=self.cn200[22].course
        )
        self.make_document(ce_cn200, title="CE22 exam", doc_type=self.exam)

        result = search_documents(
            course_code="CN200",
            department=self.cn,
            batch=self.batches[22],
            doc_type=self.exam,
        )
        self.assertEqual([doc.pk for doc in result], [cn22_exam.pk])

        by_department = search_documents(course_code="CN200", department=ce)
        self.assertEqual([doc.title for doc in by_department], ["CE22 exam"])

    def test_result_rows_load_in_a_single_query(self):
        for n in (21, 22, 23, 23):
            self.make_document(self.cn200[n], title=f"CN200 CN{n}")

        with self.assertNumQueries(1):
            for doc in search_documents(course_code="CN200"):
                (
                    doc.batch_course.batch.code,
                    doc.batch_course.course.display_name,
                    doc.doc_type.name_th,
                    doc.uploader.nickname,
                )


class SearchFormTests(SearchFixtureMixin, TestCase):
    def test_blank_course_code_is_invalid(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                form = SearchForm({"course_code": value})
                self.assertFalse(form.is_valid())
                self.assertIn("course_code", form.errors)

    def test_batch_from_another_department_is_invalid(self):
        ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )

        form = SearchForm(
            {"course_code": "CN200", "department": ce.pk, "batch": self.batches[22].pk}
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["batch"], ["รุ่น CN22 ไม่ได้อยู่ในภาค CE"])

    def test_batch_of_inactive_department_is_not_selectable(self):
        ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering", is_active=False
        )
        ce22 = Batch.objects.create(department=ce, number=22)

        form = SearchForm({"course_code": "CN200", "batch": ce22.pk})

        self.assertFalse(form.is_valid())
        self.assertIn("batch", form.errors)

    def test_filters_are_optional_and_feed_the_selector(self):
        form = SearchForm({"course_code": "cn200"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data,
            {"course_code": "cn200", "department": None, "batch": None, "doc_type": None},
        )

        form = SearchForm(
            {
                "course_code": "CN200",
                "department": self.cn.pk,
                "batch": self.batches[22].pk,
                "doc_type": self.exam.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["department"], self.cn)
        self.assertEqual(form.cleaned_data["batch"], self.batches[22])
        self.assertEqual(form.cleaned_data["doc_type"], self.exam)


class SearchViewTests(SearchFixtureMixin, TestCase):
    def setUp(self):
        self.client.force_login(self.uploader)

    def test_shows_published_results_from_every_batch_on_one_page(self):
        for n in (21, 22, 23):
            self.make_document(self.cn200[n], title=f"ชีท CN{n}")
        self.make_document(self.cn200[21], title="ยังรออนุมัติ", status="pending")
        self.make_document(self.cn200[22], title="ถูกซ่อนไว้", status="hidden")

        response = self.client.get(reverse("materials:vault"), {"course_code": "cn200"})

        self.assertEqual(response.status_code, 200)
        for n in (21, 22, 23):
            self.assertContains(response, f"ชีท CN{n}")
            self.assertContains(response, f"CN{n}")
        self.assertNotContains(response, "ยังรออนุมัติ")
        self.assertNotContains(response, "ถูกซ่อนไว้")

    def test_filters_from_the_query_string_narrow_the_results(self):
        self.make_document(self.cn200[22], title="ข้อสอบ CN22", doc_type=self.exam)
        self.make_document(self.cn200[22], title="ชีทสรุป CN22")
        self.make_document(self.cn200[21], title="ข้อสอบ CN21", doc_type=self.exam)

        response = self.client.get(
            reverse("materials:vault"),
            {
                "course_code": "CN200",
                "department": self.cn.pk,
                "batch": self.batches[22].pk,
                "doc_type": self.exam.pk,
            },
        )

        self.assertContains(response, "ข้อสอบ CN22")
        self.assertNotContains(response, "ชีทสรุป CN22")
        self.assertNotContains(response, "ข้อสอบ CN21")

    def test_batch_from_another_department_shows_the_error(self):
        ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )

        response = self.client.get(
            reverse("materials:vault"),
            {"course_code": "CN200", "department": ce.pk, "batch": self.batches[22].pk},
        )

        self.assertContains(response, "รุ่น CN22 ไม่ได้อยู่ในภาค CE")
        self.assertNotContains(response, "ผลการค้นหา")

    def test_escapes_document_titles(self):
        self.make_document(self.cn200[21], title="<script>alert(1)</script>")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_results_link_to_the_document_page(self):
        document = self.make_document(self.cn200[21], title="ชีท CN21")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertContains(response, reverse("materials:document_detail", args=[document.pk]))


class DocumentDetailViewTests(SearchFixtureMixin, TestCase):
    def test_published_document_page_embeds_the_pdf_preview(self):
        document = self.make_document(self.cn200[22], title="ชีท CN22")
        self.client.force_login(self.uploader)

        response = self.client.get(reverse("materials:document_detail", args=[document.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ชีท CN22")
        preview_url = reverse("materials:document_preview", args=[document.pk])
        self.assertContains(response, f'<iframe src="{preview_url}"')

    def test_unpublished_document_is_404(self):
        self.client.force_login(self.uploader)
        for status in ("pending", "rejected", "hidden"):
            with self.subTest(status=status):
                document = self.make_document(self.cn200[21], title=status, status=status)
                url = reverse("materials:document_detail", args=[document.pk])
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_guest_is_redirected_to_login(self):
        document = self.make_document(self.cn200[21], title="ชีท")
        url = reverse("materials:document_detail", args=[document.pk])

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentPreviewViewTests(SearchFixtureMixin, TestCase):
    pdf_bytes = b"%PDF-1.4 fake sheet"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def make_document_with_file(self, *, status="published"):
        document = self.make_document(self.cn200[21], title="ชีท", status=status)
        storage_path = f"vault/CN/21/CN200/summary/{document.pk}.pdf"
        default_storage.save(storage_path, ContentFile(self.pdf_bytes))
        document.add_version(
            storage_path=storage_path,
            original_name="cn200-midterm.pdf",
            size_bytes=len(self.pdf_bytes),
            sha256="0" * 64,
        )
        return document

    def preview(self, document):
        return self.client.get(reverse("materials:document_preview", args=[document.pk]))

    def test_streams_published_pdf_inline_and_allows_same_origin_iframe(self):
        document = self.make_document_with_file()
        self.client.force_login(self.uploader)

        response = self.preview(document)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response["Content-Disposition"].startswith("inline"))
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(b"".join(response.streaming_content), self.pdf_bytes)

    def test_unpublished_document_is_404(self):
        self.client.force_login(self.uploader)
        for status in ("pending", "rejected", "hidden"):
            with self.subTest(status=status):
                document = self.make_document_with_file(status=status)
                self.assertEqual(self.preview(document).status_code, 404)

    def test_document_without_file_is_404(self):
        document = self.make_document(self.cn200[21], title="ไม่มีไฟล์")
        self.client.force_login(self.uploader)

        self.assertEqual(self.preview(document).status_code, 404)

    def test_guest_is_redirected_to_login(self):
        document = self.make_document_with_file()

        response = self.preview(document)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("accounts:login")))


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
