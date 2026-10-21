import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from ..forms import SearchForm
from ..models import Document, DocType
from .base import SearchTestCase

User = get_user_model()

TEST_MEDIA_ROOT = tempfile.mkdtemp()
PDF_BYTES = b"%PDF-1.4 fake sheet"


class VaultViewTests(SearchTestCase):
    def setUp(self):
        self.client.force_login(self.uploader)

    def test_guest_is_redirected_to_login(self):
        self.client.logout()
        url = reverse("materials:vault")

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_without_a_query_shows_the_empty_form_and_no_results(self):
        response = self.client.get(reverse("materials:vault"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/vault.html")
        self.assertIsInstance(response.context["form"], SearchForm)
        self.assertFalse(response.context["form"].is_bound)
        self.assertIsNone(response.context["documents"])
        self.assertNotContains(response, "ผลการค้นหา")

    def test_shows_published_results_from_every_batch_on_one_page(self):
        expected = [self.make_document(self.cn200[n], title=f"ชีท CN{n}") for n in (21, 22, 23)]
        self.make_document(self.cn200[21], title="ยังรออนุมัติ", status="pending")
        self.make_document(self.cn200[22], title="ถูกซ่อนไว้", status="hidden")

        response = self.client.get(reverse("materials:vault"), {"course_code": "cn200"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/vault.html")
        self.assertEqual(list(response.context["documents"]), expected)
        for n in (21, 22, 23):
            self.assertContains(response, f"ชีท CN{n}")
        self.assertNotContains(response, "ยังรออนุมัติ")
        self.assertNotContains(response, "ถูกซ่อนไว้")

    def test_course_without_published_documents_says_nothing_was_found(self):
        self.make_document(self.cn200[21], title="ยังรออนุมัติ", status="pending")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertEqual(list(response.context["documents"]), [])
        self.assertContains(response, "ไม่พบเอกสาร")

    def test_filters_from_the_query_string_narrow_the_results(self):
        cn22_exam = self.make_document(self.cn200[22], title="ข้อสอบ CN22", doc_type=self.exam)
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

        self.assertEqual(list(response.context["documents"]), [cn22_exam])
        self.assertContains(response, "ข้อสอบ CN22")
        self.assertNotContains(response, "ชีทสรุป CN22")
        self.assertNotContains(response, "ข้อสอบ CN21")

    def test_batch_from_another_department_shows_the_error(self):
        ce = self.make_department()

        response = self.client.get(
            reverse("materials:vault"),
            {"course_code": "CN200", "department": ce.pk, "batch": self.batches[22].pk},
        )

        self.assertIsNone(response.context["documents"])
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


class DocumentDetailViewTests(SearchTestCase):
    def test_published_document_page_embeds_the_pdf_preview(self):
        document = self.make_document(self.cn200[22], title="ชีท CN22")
        self.client.force_login(self.uploader)

        response = self.client.get(reverse("materials:document_detail", args=[document.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/document_detail.html")
        self.assertEqual(response.context["document"], document)
        preview_url = reverse("materials:document_preview", args=[document.pk])
        self.assertContains(response, f'<iframe src="{preview_url}"')

    def test_unpublished_document_is_404(self):
        self.client.force_login(self.uploader)
        for status in ("pending", "rejected", "hidden"):
            with self.subTest(status=status):
                document = self.make_document(self.cn200[21], title=status, status=status)

                response = self.client.get(
                    reverse("materials:document_detail", args=[document.pk])
                )

                self.assertEqual(response.status_code, 404)

    def test_guest_is_redirected_to_login(self):
        document = self.make_document(self.cn200[21], title="ชีท")
        url = reverse("materials:document_detail", args=[document.pk])

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentPreviewViewTests(SearchTestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def make_document_with_file(self, *, status="published", storage_path=None):
        document = self.make_document(self.cn200[21], title="ชีท", status=status)
        if storage_path is None:
            storage_path = default_storage.save(
                f"vault/CN/21/CN200/summary/{document.pk}.pdf", ContentFile(PDF_BYTES)
            )
        document.add_version(
            storage_path=storage_path,
            original_name="cn200-midterm.pdf",
            size_bytes=len(PDF_BYTES),
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
        self.assertEqual(b"".join(response.streaming_content), PDF_BYTES)

    def test_unpublished_document_is_404(self):
        self.client.force_login(self.uploader)
        for status in ("pending", "rejected", "hidden"):
            with self.subTest(status=status):
                document = self.make_document_with_file(status=status)

                response = self.preview(document)

                self.assertEqual(response.status_code, 404)

    def test_document_without_a_version_is_404(self):
        document = self.make_document(self.cn200[21], title="ไม่มีไฟล์")
        self.client.force_login(self.uploader)

        response = self.preview(document)

        self.assertEqual(response.status_code, 404)

    def test_version_whose_file_is_missing_from_storage_is_404(self):
        document = self.make_document_with_file(storage_path="vault/never-saved.pdf")
        self.client.force_login(self.uploader)

        response = self.preview(document)

        self.assertEqual(response.status_code, 404)

    def test_guest_is_redirected_to_login(self):
        document = self.make_document_with_file()
        url = reverse("materials:document_preview", args=[document.pk])

        response = self.client.get(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")


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
