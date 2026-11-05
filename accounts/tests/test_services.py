from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
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


class ModeratorServiceTests(ModeratorTestCase):
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


class DeleteOwnAccountServiceTests(ModeratorTestCase):
    def test_correct_password_anonymizes_user_and_removes_roles(self):
        services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)

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
        self.assertTrue(self.admin.user_roles.filter(role=self.role_super_admin).exists())

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



class DeleteAccountRateLimitServiceTests(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)

    def test_key_generation_has_no_pii(self):
        from accounts.services import _delete_account_failure_key
        key = _delete_account_failure_key(user_id=123, client_ip="192.168.1.1")
        self.assertTrue(key.startswith("delete-account-failures:"))
        self.assertNotIn("123", key)
        self.assertNotIn("192.168.1.1", key)

    def test_rate_limit_flow(self):
        from accounts import services
        user_id = 999
        client_ip = "10.0.0.1"

        self.assertFalse(services.is_delete_account_rate_limited(user_id=user_id, client_ip=client_ip))
        for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
            services.record_delete_account_failure(user_id=user_id, client_ip=client_ip)

        self.assertTrue(services.is_delete_account_rate_limited(user_id=user_id, client_ip=client_ip))
        services.clear_delete_account_failures(user_id=user_id, client_ip=client_ip)
        self.assertFalse(services.is_delete_account_rate_limited(user_id=user_id, client_ip=client_ip))
