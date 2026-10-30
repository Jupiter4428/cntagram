from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Course, Department


class DepartmentCodeTests(TestCase):
    """รหัสภาคอยู่ใน path ไฟล์ (vault/{code}/...) จึงรับแค่ A-Z (issue #63)"""

    def test_full_clean_rejects_zero_width_space_in_code(self):
        dept = Department(code="C\u200bN", name_th="คอมพิวเตอร์", name_en="Computer")

        with self.assertRaises(ValidationError) as ctx:
            dept.full_clean()

        self.assertIn("code", ctx.exception.message_dict)

    def test_full_clean_rejects_non_ascii_letter_that_uppercases_to_ascii(self):
        dept = Department(code="c\u00df", name_th="คอมพิวเตอร์", name_en="Computer")  # \u00df.upper() = "SS"

        with self.assertRaises(ValidationError) as ctx:
            dept.full_clean()

        self.assertIn("code", ctx.exception.message_dict)

    def test_full_clean_accepts_lowercase_code_and_stores_it_uppercase(self):
        dept = Department(code=" cn ", name_th="คอมพิวเตอร์", name_en="Computer")

        dept.full_clean()

        self.assertEqual(dept.code, "CN")


class CourseCodeTests(TestCase):
    """รหัสวิชา = อักษรภาค + เลขวิชาไม่เกิน 3 หลัก เช่น CN201 และอยู่ใน path ไฟล์ (issue #63)"""

    def test_full_clean_rejects_code_not_letters_then_up_to_three_digits(self):
        for code in ["101", "CN", "CN1234", "CN10A"]:
            with self.subTest(code=code):
                course = Course(code=code, name_en="Programming")

                with self.assertRaises(ValidationError) as ctx:
                    course.full_clean()

                self.assertIn("code", ctx.exception.message_dict)

    def test_full_clean_rejects_zero_width_space_in_code(self):
        course = Course(code="CN\u200b101", name_en="Programming")

        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()

        self.assertIn("code", ctx.exception.message_dict)

    def test_full_clean_rejects_non_ascii_letter_that_uppercases_to_ascii(self):
        course = Course(code="cn\u0131101", name_en="Programming")  # \u0131.upper() = "I"

        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()

        self.assertIn("code", ctx.exception.message_dict)

    def test_full_clean_accepts_lowercase_code_and_stores_it_uppercase(self):
        course = Course(code="cn101", name_en="Programming")

        course.full_clean()

        self.assertEqual(course.code, "CN101")
