from django.contrib.auth.forms import AuthenticationForm
from django.test import TestCase

from ..forms import LoginForm, RegisterForm
from .base import RegistrationTestMixin


class LoginFormTests(TestCase):
    def test_login_form_extends_django_authentication_form(self):
        self.assertTrue(issubclass(LoginForm, AuthenticationForm))


class RegisterFormTests(RegistrationTestMixin, TestCase):
    def assertFieldError(self, data, field):
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(field, form.errors)
        return form

    def test_valid_data_normalizes_email(self):
        form = RegisterForm(data=self.payload(email="  6610612345@Student.TU.ac.th "))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "6610612345@student.tu.ac.th")

    def test_rejects_non_student_domain(self):
        for email in ("6610612345@gmail.com", "6610612345@tu.ac.th"):
            with self.subTest(email=email):
                self.assertFieldError(self.payload(email=email), "email")

    def test_malformed_email_shows_thai_error(self):
        form = self.assertFieldError(self.payload(email="not-an-email"), "email")
        self.assertEqual(form.errors["email"], ["รูปแบบอีเมลไม่ถูกต้อง"])

    def test_rejects_local_part_that_is_not_10_digits(self):
        for email in (
            "661061234@student.tu.ac.th",
            "66106123456@student.tu.ac.th",
            "66106abcde@student.tu.ac.th",
            "๖๖๑๐๖๑๒๓๔๕@student.tu.ac.th",
        ):
            with self.subTest(email=email):
                self.assertFieldError(self.payload(email=email), "email")

    def test_rejects_faculty_code_other_than_10(self):
        form = self.assertFieldError(
            self.payload(email="6620612345@student.tu.ac.th"), "email"
        )
        self.assertIn("คณะวิศวกรรมศาสตร์", form.errors["email"][0])

    def test_rejects_duplicate_email(self):
        self.register(nickname="First")
        self.assertFieldError(self.payload(), "email")

    def test_rejects_reserved_nickname(self):
        for nickname in ("admin", "Ad-Min", "MODERATOR", "แอดมิน"):
            with self.subTest(nickname=nickname):
                form = self.assertFieldError(self.payload(nickname=nickname), "nickname")
                self.assertIn("ชื่อเล่นนี้ถูกสงวนไว้ กรุณาใช้ชื่ออื่น", form.errors["nickname"][0])

    def test_blank_required_fields_show_thai_error(self):
        for field in ("email", "nickname", "department", "password", "password_confirm"):
            with self.subTest(field=field):
                form = self.assertFieldError(self.payload(**{field: ""}), field)
                self.assertEqual(form.errors[field], ["กรุณากรอกข้อมูลช่องนี้"])

    def test_requires_pdpa_consent(self):
        form = self.assertFieldError(self.payload(pdpa_consent=None), "pdpa_consent")
        self.assertIn("PDPA", form.errors["pdpa_consent"][0])

    def test_rejects_password_mismatch(self):
        self.assertFieldError(
            self.payload(password_confirm="Something-Else-123"), "password_confirm"
        )

    def test_rejects_weak_password(self):
        self.assertFieldError(
            self.payload(password="12345678", password_confirm="12345678"), "password"
        )

    def test_rejects_password_too_similar_to_nickname(self):
        form = self.assertFieldError(
            self.payload(
                nickname="Supaporn",
                password="Supaporn12345",
                password_confirm="Supaporn12345",
            ),
            "password",
        )
        self.assertTrue(
            any("คล้าย" in err or "similar" in err.lower() for err in form.errors["password"])
        )

    def test_department_choices_only_include_active_departments(self):
        queryset = RegisterForm().fields["department"].queryset
        self.assertIn(self.department, queryset)
        self.assertNotIn(self.inactive_department, queryset)

    def test_rejects_inactive_department_with_thai_error(self):
        form = self.assertFieldError(
            self.payload(department=str(self.inactive_department.pk)), "department"
        )
        self.assertEqual(form.errors["department"], ["กรุณาเลือกภาควิชาจากรายการ"])

    def test_invalid_fields_get_bootstrap_invalid_class(self):
        form = self.assertFieldError(self.payload(nickname="admin"), "nickname")
        self.assertIn("is-invalid", form.fields["nickname"].widget.attrs["class"])
        self.assertNotIn("is-invalid", form.fields["email"].widget.attrs["class"])
