from catalog.models import Batch

from ..forms import SearchForm, UploadForm
from .base import SearchTestCase, UploadTestCase


class SearchFormTests(SearchTestCase):
    def test_blank_course_code_is_invalid(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                form = SearchForm({"course_code": value})

                self.assertFalse(form.is_valid())
                self.assertIn("course_code", form.errors)

    def test_blank_course_code_shows_thai_error_message(self):
        form = SearchForm({"course_code": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["course_code"], ["กรุณาระบุรหัสวิชา"])

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
        form_low = UploadForm(data={"exam_year_be": 2499})
        self.assertFalse(form_low.is_valid())
        self.assertEqual(form_low.errors.get("exam_year_be"), ["ปี พ.ศ. ต้องไม่น้อยกว่า 2500"])

        form_high = UploadForm(data={"exam_year_be": 2701})
        self.assertFalse(form_high.is_valid())
        self.assertEqual(form_high.errors.get("exam_year_be"), ["ปี พ.ศ. ต้องไม่เกิน 2700"])

        form_invalid = UploadForm(data={"exam_year_be": "not_a_number"})
        self.assertFalse(form_invalid.is_valid())
        self.assertEqual(form_invalid.errors.get("exam_year_be"), ["กรุณาระบุปี พ.ศ. เป็นตัวเลข"])
