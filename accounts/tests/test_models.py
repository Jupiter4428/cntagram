from django.test import TestCase

from ..models import Role, User


class RoleSeedMigrationTests(TestCase):
    def test_migrations_create_all_roles(self):
        codes = set(Role.objects.values_list("code", flat=True))

        self.assertEqual(
            codes, {Role.STUDENT, Role.ALUMNI, Role.MODERATOR, Role.SUPER_ADMIN}
        )


class UserAvatarModelTests(TestCase):
    def test_user_has_avatar_field(self):
        field = User._meta.get_field("avatar")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 255)

    def test_anonymize_clears_avatar(self):
        from catalog.models import Department
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        from django.utils import timezone

        dept = Department.objects.create(code="CN", name_th="คอม", name_en="Comp")
        avatar_path = default_storage.save(
            "avatars/test_anon.jpg", ContentFile(b"test")
        )
        self.assertTrue(default_storage.exists(avatar_path))

        user = User.objects.create_user(
            email="6510000001@student.tu.ac.th",
            password="Password123!",
            nickname="TestUser",
            department=dept,
            pdpa_consent_at=timezone.now(),
            avatar=avatar_path,
        )
        self.assertEqual(user.avatar, avatar_path)
        user.anonymize()
        user.refresh_from_db()
        self.assertIsNone(user.avatar)
        self.assertFalse(default_storage.exists(avatar_path))
