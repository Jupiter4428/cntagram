from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from .. import selectors, services
from ..models import Role, UserRole
from ..services import register_user
from .base import (
    ModeratorTestCase,
    RegistrationTestCase,
    ThrottleTestCase,
    VALID_PASSWORD,
    make_department,
)

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


class LoginServiceTests(ThrottleTestCase):
    def setUp(self):
        super().setUp()
        self.department = make_department(code="CN")
        self.user = User.objects.create_user(
            email="6610000001@student.tu.ac.th",
            password=VALID_PASSWORD,
            nickname="LoginTester",
            department=self.department,
            pdpa_consent_at=timezone.now(),
        )

    def test_record_login_failure_increments_attempts(self):
        ip = "192.0.2.1"
        for _ in range(3):
            services.record_login_failure(identifier=self.user.email, client_ip=ip)

        id_key, ip_key = services._login_failure_keys(
            identifier=self.user.email, client_ip=ip
        )
        self.assertEqual(cache.get(id_key), 3)
        self.assertEqual(cache.get(ip_key), 3)

    def test_record_login_failure_resets_window_when_key_expired(self):
        ip = "192.0.2.1"
        services.record_login_failure(identifier=self.user.email, client_ip=ip)
        id_key, ip_key = services._login_failure_keys(
            identifier=self.user.email, client_ip=ip
        )
        cache.delete(id_key)
        cache.delete(ip_key)
        services.record_login_failure(identifier=self.user.email, client_ip=ip)
        self.assertEqual(cache.get(id_key), 1)
        self.assertEqual(cache.get(ip_key), 1)

    def test_attempt_login_inactive_user_fails(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        attempt = services.attempt_login(
            identifier=self.user.email, password=VALID_PASSWORD, client_ip="192.0.2.1"
        )

        self.assertIsNone(attempt.user)

    def test_attempt_login_success(self):
        ip = "192.0.2.1"
        attempt = services.attempt_login(
            identifier=self.user.email,
            password=VALID_PASSWORD,
            client_ip=ip,
        )
        self.assertEqual(attempt.user, self.user)
        self.assertFalse(attempt.rate_limited)
        self.assertFalse(
            services.is_login_rate_limited(identifier=self.user.email, client_ip=ip)
        )

    @override_settings(LOGIN_RATE_LIMIT_ATTEMPTS=1)
    def test_attempt_login_failure_records_attempt(self):
        ip = "192.0.2.1"
        attempt = services.attempt_login(
            identifier=self.user.email,
            password="wrong-password",
            client_ip=ip,
        )
        self.assertIsNone(attempt.user)
        self.assertFalse(attempt.rate_limited)
        self.assertTrue(
            services.is_login_rate_limited(identifier=self.user.email, client_ip=ip)
        )

    def test_attempt_login_rate_limited(self):
        ip = "192.0.2.1"
        for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
            services.record_login_failure(identifier=self.user.email, client_ip=ip)

        attempt = services.attempt_login(
            identifier=self.user.email,
            password=VALID_PASSWORD,
            client_ip=ip,
        )
        self.assertIsNone(attempt.user)
        self.assertTrue(attempt.rate_limited)


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


class DeleteAccountRateLimitServiceTests(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)

    def test_key_generation_has_no_pii(self):
        from accounts.services import _delete_account_failure_key

        key = _delete_account_failure_key(user_id=9876543210)
        self.assertTrue(key.startswith("delete-account-failures:"))
        self.assertNotIn("9876543210", key)

    def test_rate_limit_flow(self):
        from accounts import services

        user_id = 999

        self.assertFalse(services.is_delete_account_rate_limited(user_id=user_id))
        for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
            services.record_delete_account_failure(user_id=user_id)

        self.assertTrue(services.is_delete_account_rate_limited(user_id=user_id))
        services.clear_delete_account_failures(user_id=user_id)
        self.assertFalse(services.is_delete_account_rate_limited(user_id=user_id))


class UserAvatarServiceTests(RegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.register()

    def make_image_file(self, format="JPEG", size=(50, 50), filename="avatar.jpg"):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile

        buf = io.BytesIO()
        img = Image.new("RGB", size, color="blue")
        img.save(buf, format=format)
        ext = format.lower()
        content = buf.getvalue()
        return SimpleUploadedFile(
            filename or f"avatar.{ext}", content, content_type=f"image/{ext}"
        )

    def test_update_avatar_saves_file_and_updates_user(self):
        from django.core.files.storage import default_storage

        image_file = self.make_image_file(format="PNG")
        updated_user = services.update_user_avatar(user=self.user, file=image_file)

        self.assertIsNotNone(updated_user.avatar)
        self.assertTrue(updated_user.avatar.startswith("avatars/"))
        self.assertTrue(default_storage.exists(updated_user.avatar))
        self.addCleanup(default_storage.delete, updated_user.avatar)

    def test_update_avatar_replaces_old_avatar_in_storage(self):
        from django.core.files.storage import default_storage

        img1 = self.make_image_file(format="JPEG")
        updated_user = services.update_user_avatar(user=self.user, file=img1)
        old_path = updated_user.avatar
        self.assertTrue(default_storage.exists(old_path))

        img2 = self.make_image_file(format="PNG")
        updated_user = services.update_user_avatar(user=self.user, file=img2)
        new_path = updated_user.avatar
        self.addCleanup(default_storage.delete, new_path)

        self.assertNotEqual(old_path, new_path)
        self.assertFalse(default_storage.exists(old_path))
        self.assertTrue(default_storage.exists(new_path))

    def test_update_avatar_rejects_file_exceeding_max_size(self):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a file whose size attribute > 2MB
        big_content = b"x" * 100
        image_file = SimpleUploadedFile(
            "big.jpg", big_content, content_type="image/jpeg"
        )
        with patch.object(image_file, "size", services.MAX_AVATAR_SIZE_BYTES + 1):
            with self.assertRaises(ValidationError) as cm:
                services.update_user_avatar(user=self.user, file=image_file)
            self.assertIn("ขนาดไฟล์ต้องไม่เกิน", str(cm.exception))

    def test_update_avatar_rejects_corrupted_or_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_file = SimpleUploadedFile(
            "fake.jpg", b"not-a-real-image-bytes", content_type="image/jpeg"
        )
        with self.assertRaises(ValidationError) as cm:
            services.update_user_avatar(user=self.user, file=fake_file)
        self.assertIn("ไฟล์ที่อัปโหลดไม่ใช่รูปภาพที่ถูกต้อง", str(cm.exception))

    def test_update_avatar_rejects_unsupported_format(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io
        from PIL import Image

        buf = io.BytesIO()
        img = Image.new("RGB", (30, 30), color="red")
        img.save(buf, format="BMP")
        bmp_file = SimpleUploadedFile(
            "avatar.bmp", buf.getvalue(), content_type="image/bmp"
        )

        with self.assertRaises(ValidationError) as cm:
            services.update_user_avatar(user=self.user, file=bmp_file)
        self.assertIn("รองรับเฉพาะไฟล์ภาพนามสกุล", str(cm.exception))

    def test_delete_avatar_removes_file_and_clears_user_field(self):
        from django.core.files.storage import default_storage

        img = self.make_image_file()
        updated_user = services.update_user_avatar(user=self.user, file=img)
        path = updated_user.avatar
        self.assertTrue(default_storage.exists(path))

        cleared_user = services.delete_user_avatar(user=self.user)
        self.assertIsNone(cleared_user.avatar)
        self.assertFalse(default_storage.exists(path))

    def test_delete_avatar_when_no_avatar_succeeds(self):
        self.assertIsNone(self.user.avatar)
        cleared_user = services.delete_user_avatar(user=self.user)
        self.assertIsNone(cleared_user.avatar)

    def test_update_avatar_cleans_up_file_on_db_error(self):
        from unittest.mock import patch
        from django.core.files.storage import default_storage
        from django.db import IntegrityError

        img = self.make_image_file()
        deleted_paths = []
        original_delete = default_storage.delete

        def record_delete(path):
            deleted_paths.append(path)
            return original_delete(path)

        with patch.object(default_storage, "delete", side_effect=record_delete):
            with patch.object(User, "save", side_effect=IntegrityError("DB failure")):
                with self.assertRaises(IntegrityError):
                    services.update_user_avatar(user=self.user, file=img)

        self.assertIsNone(self.user.avatar)
        self.assertEqual(len(deleted_paths), 1)
        self.assertTrue(deleted_paths[0].startswith("avatars/user_"))
        self.assertFalse(default_storage.exists(deleted_paths[0]))
