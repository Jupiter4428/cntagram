from catalog.models import Batch

from ..forms import SearchForm
from .base import SearchTestCase


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
