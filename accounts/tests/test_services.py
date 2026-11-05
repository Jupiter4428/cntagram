from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from .. import selectors, services
from ..models import Role, UserRole
from ..services import register_user
from .base import ModeratorTestCase, RegistrationTestCase, VALID_PASSWORD

User = get_user_model()


class RegisterUserServiceTests(RegistrationTestCase):
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

        self.assertFalse(
            User.objects.filter(email="6610612345@student.tu.ac.th").exists()
        )

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

        self.assertFalse(
            User.objects.filter(email="6610612345@student.tu.ac.th").exists()
        )


class ModeratorServiceTests(ModeratorTestCase):
    def test_assign_and_remove_moderator_many_to_many(self):
        ur1 = services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        services.assign_moderator(
            user=self.user_momo, department=self.dept_ce, granted_by=self.admin
        )

        self.assertTrue(
            selectors.is_moderator_of_department(
                user=self.user_momo, department=self.dept_cn
            )
        )
        self.assertTrue(
            selectors.is_moderator_of_department(
                user=self.user_momo, department=self.dept_ce
            )
        )

        services.remove_moderator(user_role=ur1)
        self.assertFalse(
            selectors.is_moderator_of_department(
                user=self.user_momo, department=self.dept_cn
            )
        )
        self.assertTrue(
            selectors.is_moderator_of_department(
                user=self.user_momo, department=self.dept_ce
            )
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


class DeleteOwnAccountServiceTests(ModeratorTestCase):
    def test_correct_password_anonymizes_user_and_removes_roles(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )

        services.delete_own_account(user=self.user_momo, password="password123")

        self.user_momo.refresh_from_db()
        self.assertEqual(self.user_momo.nickname, "Deleted user")
        self.assertFalse(self.user_momo.is_active)
        self.assertNotIn("6510610001", self.user_momo.email + self.user_momo.student_id)
        self.assertFalse(self.user_momo.user_roles.exists())

    def test_wrong_password_raises_and_leaves_account_unchanged(self):
        with self.assertRaises(ValidationError) as ctx:
            services.delete_own_account(user=self.user_momo, password="wrong-password")

        self.assertIn("password", ctx.exception.message_dict)
        self.user_momo.refresh_from_db()
        self.assertEqual(self.user_momo.nickname, "momo")
        self.assertTrue(self.user_momo.is_active)
        self.assertTrue(self.user_momo.check_password("password123"))
        self.assertTrue(self.user_momo.user_roles.exists())

    def test_last_super_admin_cannot_delete_own_account(self):
        with self.assertRaises(ValidationError):
            services.delete_own_account(user=self.admin, password="password123")

        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(
            self.admin.user_roles.filter(role=self.role_super_admin).exists()
        )

    def test_super_admin_can_delete_own_account_when_another_remains(self):
        UserRole.objects.create(user=self.user_nana, role=self.role_super_admin)

        services.delete_own_account(user=self.admin, password="password123")

        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)

    def test_same_email_can_register_again_after_deletion(self):
        services.delete_own_account(user=self.user_momo, password="password123")

        user = register_user(
            email="6510610001@student.tu.ac.th",
            password=VALID_PASSWORD,
            nickname="momo2",
            department=self.dept_cn,
            pdpa_consent_at=timezone.now(),
        )

        self.assertEqual(user.student_id, "6510610001")
