import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from ..forms import SearchForm
from ..models import Document, DocType
from .base import SearchTestCase, UploadTestCase, pdf_file, stored_file_count

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

    def test_invalid_search_shows_the_error_without_the_start_hint(self):
        response = self.client.get(reverse("materials:vault"), {"course_code": ""})

        self.assertContains(response, "This field is required")
        self.assertNotContains(response, "กรอกรหัสวิชา เช่น CN200")

    def test_escapes_document_titles(self):
        self.make_document(self.cn200[21], title="<script>alert(1)</script>")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_results_link_to_the_document_page(self):
        document = self.make_document(self.cn200[21], title="ชีท CN21")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertContains(response, reverse("materials:document_detail", args=[document.pk]))

    def test_results_use_the_shared_document_meta_partial(self):
        self.make_document(self.cn200[21], title="ชีท CN21")

        response = self.client.get(reverse("materials:vault"), {"course_code": "CN200"})

        self.assertTemplateUsed(response, "materials/_document_meta.html")


class DocumentDetailViewTests(SearchTestCase):
    def test_document_page_uses_the_shared_document_meta_partial(self):
        document = self.make_document(self.cn200[22], title="ชีท CN22")
        self.client.force_login(self.uploader)

        response = self.client.get(reverse("materials:document_detail", args=[document.pk]))

        self.assertTemplateUsed(response, "materials/_document_meta.html")

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

    def test_navbar_links_to_upload_page(self):
        response = self.client.get(reverse("materials:vault"))

        self.assertContains(response, f'href="{reverse("materials:upload")}"')

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

    def test_model_error_outside_form_fields_is_shown_not_500(self):
        """รหัสภาคมี zero-width space (U+200B) ที่ระบบไฟล์รับ แต่ DocumentVersion ปฏิเสธ storage_path

        error key storage_path ไม่ใช่ช่องในฟอร์ม จึงต้องแสดงเป็น non-field error
        """
        dept = Department.objects.create(code="C​N", name_th="ภาครหัสผิด", name_en="Bad code")
        batch = Batch.objects.create(department=dept, number=21)
        batch_course = BatchCourse.objects.create(batch=batch, course=self.cn21_cn200.course)
        self.student.department = dept
        self.student.save()
        files_before = stored_file_count()

        response = self.post(batch_course=batch_course.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].non_field_errors(), ["Unsafe storage_path."])
        self.assertFalse(Document.objects.exists())
        self.assertEqual(stored_file_count(), files_before)

    def test_error_without_field_names_is_shown_not_500(self):
        """storage (ระบบภายนอก) ปฏิเสธไฟล์ด้วย ValidationError ที่ไม่มีชื่อช่อง"""
        error = ValidationError("Storage rejected the file.")
        with mock.patch("materials.services.default_storage.save", side_effect=error):
            response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].non_field_errors(), ["Storage rejected the file."])
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
