from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .. import selectors, services
from ..models import Role
from ..services import register_user
from .base import ModeratorTestMixin, RegistrationTestMixin, VALID_PASSWORD

User = get_user_model()


class RegisterUserServiceTests(RegistrationTestMixin, TestCase):
    def test_creates_user_with_student_id_and_hashed_password(self):
        consent_at = timezone.now()
        user = self.register(pdpa_consent_at=consent_at)

        self.assertEqual(user.student_id, "6610612345")
        self.assertEqual(user.entry_year, 66)
        self.assertEqual(user.department, self.department)
        self.assertEqual(user.pdpa_consent_at, consent_at)
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.assertNotEqual(user.password, VALID_PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_entry_year_extracted_from_student_id_67(self):
        user = self.register(email="6710619999@student.tu.ac.th")
        self.assertEqual(user.student_id, "6710619999")
        self.assertEqual(user.entry_year, 67)

    def test_assigns_student_role(self):
        user = self.register()
        role_codes = list(user.user_roles.values_list("role__code", flat=True))
        self.assertEqual(role_codes, [Role.STUDENT])

    def test_rolls_back_user_when_student_role_missing(self):
        Role.objects.filter(code=Role.STUDENT).delete()
        with self.assertRaises(Role.DoesNotExist):
            self.register()

        self.assertFalse(User.objects.filter(email="6610612345@student.tu.ac.th").exists())

    def test_duplicate_email_at_database_insertion_raises_validation_error(self):
        self.register(email="6610612345@student.tu.ac.th")
        with self.assertRaises(ValidationError) as ctx:
            self.register(email="6610612345@student.tu.ac.th", nickname="Another")
        self.assertIn("email", ctx.exception.message_dict)
        self.assertIn("อีเมลนี้ถูกใช้สมัครแล้ว", ctx.exception.message_dict["email"])

    def test_requires_explicit_pdpa_consent_time(self):
        with self.assertRaises(TypeError):
            register_user(
                email="6610612345@student.tu.ac.th",
                password=VALID_PASSWORD,
                nickname="Ploy",
                department=self.department,
            )

        self.assertFalse(User.objects.filter(email="6610612345@student.tu.ac.th").exists())


class ModeratorServiceTests(ModeratorTestMixin, TestCase):
    def test_assign_and_remove_moderator_many_to_many(self):
        ur1 = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        ur2 = services.assign_moderator(
            user=self.user_momo, department=self.dept_ce, granted_by=self.admin
        )

        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_ce)
        )

        services.remove_moderator(user_role=ur1)
        self.assertFalse(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_ce)
        )

    def test_cannot_assign_duplicate_moderator(self):
        ur = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.assertEqual(ur.granted_by, self.admin)

        with self.assertRaises(ValidationError):
            services.assign_moderator(
                user=self.user_momo, department=self.dept_cn, granted_by=self.admin
            )
