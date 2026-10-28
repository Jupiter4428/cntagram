from django.test import TestCase

from ..models import Role


class RoleSeedMigrationTests(TestCase):
    def test_migrations_create_all_roles(self):
        codes = set(Role.objects.values_list("code", flat=True))

        self.assertEqual(codes, {Role.STUDENT, Role.ALUMNI, Role.MODERATOR, Role.SUPER_ADMIN})
