from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.models import Batch

from ..forms import SearchForm, UploadForm
from .base import SearchTestCase, UploadTestCase


class SearchFormTests(SearchTestCase):
    def test_blank_course_code_is_invalid_and_shows_thai_error(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                form = SearchForm({"course_code": value})
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors["course_code"], ["กรุณาระบุรหัสวิชา"])

    def test_course_code_too_long_shows_thai_error_message(self):
        form = SearchForm({"course_code": "X" * 11})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["course_code"], ["รหัสวิชาต้องไม่เกิน 10 ตัวอักษร"])

    def test_unknown_filter_choices_show_thai_error_messages(self):
        form = SearchForm(
            {
                "course_code": "CN200",
                "department": "99999",
                "batch": "99999",
                "doc_type": "99999",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["department"], ["ภาควิชาที่เลือกไม่ถูกต้อง"])
        self.assertEqual(form.errors["batch"], ["รุ่นที่เลือกไม่ถูกต้อง"])
        self.assertEqual(form.errors["doc_type"], ["ประเภทที่เลือกไม่ถูกต้อง"])

    def test_batch_from_another_department_is_invalid(self):
        ce = self.make_department()
        form = SearchForm(
            {"course_code": "CN200", "department": ce.pk, "batch": self.batches[22].pk}
        )

        valid = form.is_valid()

        self.assertFalse(valid)
        self.assertEqual(form.errors["batch"], ["รุ่น CN22 ไม่ได้อยู่ในภาค CE"])

    def test_batch_of_inactive_department_is_not_selectable(self):
        ce = self.make_department(is_active=False)
        ce22 = Batch.objects.create(department=ce, number=22)
        form = SearchForm({"course_code": "CN200", "batch": ce22.pk})

        valid = form.is_valid()

        self.assertFalse(valid)
        self.assertIn("batch", form.errors)

    def test_course_code_alone_is_valid_with_empty_filters(self):
        form = SearchForm({"course_code": "cn200"})

        valid = form.is_valid()

        self.assertTrue(valid, form.errors)
        self.assertEqual(
            form.cleaned_data,
            {"course_code": "cn200", "department": None, "batch": None, "doc_type": None},
        )

    def test_filters_clean_to_the_selected_rows(self):
        form = SearchForm(
            {
                "course_code": "CN200",
                "department": self.cn.pk,
                "batch": self.batches[22].pk,
                "doc_type": self.exam.pk,
            }
        )

        valid = form.is_valid()

        self.assertTrue(valid, form.errors)
        self.assertEqual(form.cleaned_data["department"], self.cn)
        self.assertEqual(form.cleaned_data["batch"], self.batches[22])
        self.assertEqual(form.cleaned_data["doc_type"], self.exam)


class UploadFormTests(UploadTestCase):
    def test_required_fields_show_thai_error_messages(self):
        form = UploadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get("batch_course"), ["กรุณาเลือกวิชา"])
        self.assertEqual(form.errors.get("doc_type"), ["กรุณาเลือกประเภทเอกสาร"])
        self.assertEqual(form.errors.get("title"), ["กรุณาระบุชื่อเอกสาร"])
        self.assertEqual(form.errors.get("file"), ["กรุณาแนบไฟล์ PDF"])
        self.assertEqual(form.errors.get("disclaimer"), ["กรุณายืนยันว่าไฟล์นี้ไม่ละเมิดลิขสิทธิ์"])

    def test_title_too_long_shows_thai_error_message(self):
        form = UploadForm(data={"title": "ก" * 201})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.get("title"), ["ชื่อเอกสารต้องมีความยาวไม่เกิน 200 ตัวอักษร"])

    def test_exam_year_be_validation_shows_thai_error_messages(self):
        for value, message in (
            (2499, "ปี พ.ศ. ต้องไม่น้อยกว่า 2500"),
            (2701, "ปี พ.ศ. ต้องไม่เกิน 2700"),
            ("not_a_number", "กรุณาระบุปี พ.ศ. เป็นตัวเลข"),
        ):
            with self.subTest(value=value):
                form = UploadForm(data={"exam_year_be": value})
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors.get("exam_year_be"), [message])

    def test_empty_file_shows_thai_error_message(self):
        form = UploadForm(data={}, files={"file": SimpleUploadedFile("a.pdf", b"")})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["file"], ["ไฟล์ที่แนบว่างเปล่า"])

    def test_unknown_choices_show_thai_error_messages(self):
        form = UploadForm(
            data={"batch_course": "99999", "doc_type": "99999", "exam_period": "99999"}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["batch_course"], ["วิชาที่เลือกไม่ถูกต้อง"])
        self.assertEqual(form.errors["doc_type"], ["ประเภทเอกสารที่เลือกไม่ถูกต้อง"])
        self.assertEqual(form.errors["exam_period"], ["ช่วงสอบที่เลือกไม่ถูกต้อง"])
