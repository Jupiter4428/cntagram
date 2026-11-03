from django.test import TestCase

from catalog.forms import CourseForm, DepartmentForm


class DepartmentFormTests(TestCase):
    def test_valid_code_passes(self):
        form = DepartmentForm(
            data={"code": "cn", "name_th": "คอมพิวเตอร์", "name_en": "Computer", "is_active": True}
        )

        is_valid = form.is_valid()

        self.assertTrue(is_valid)


    def test_department_form_labels(self):
        form = DepartmentForm()
        self.assertEqual(form.fields["code"].label, "รหัสภาควิชา")
        self.assertEqual(form.fields["name_th"].label, "ชื่อไทย")
        self.assertEqual(form.fields["name_en"].label, "ชื่ออังกฤษ")
        self.assertEqual(form.fields["is_active"].label, "เปิดใช้งาน")
    def test_shows_error_on_code_for_zero_width_space(self):
        form = DepartmentForm(
            data={"code": "C\u200bN", "name_th": "คอมพิวเตอร์", "name_en": "Computer", "is_active": True}
        )

        is_valid = form.is_valid()

        self.assertFalse(is_valid)
        self.assertEqual(
            form.errors["code"], ["รหัสภาควิชาต้องเป็นตัวอักษรภาษาอังกฤษ A-Z 2-5 ตัว"]
        )


class CourseFormTests(TestCase):
    def test_valid_code_passes(self):
        form = CourseForm(data={"code": "cn101", "name_th": "", "name_en": "Programming"})

        is_valid = form.is_valid()

        self.assertTrue(is_valid)

    def test_shows_error_on_code_for_slash(self):
        form = CourseForm(data={"code": "CN/101", "name_th": "", "name_en": "Programming"})

        is_valid = form.is_valid()

        self.assertFalse(is_valid)
        self.assertEqual(
            form.errors["code"], ["รหัสวิชาต้องเป็นตัวอักษรภาษาอังกฤษ A-Z ตามด้วยตัวเลข 1-3 หลัก เช่น CN201"]
        )
