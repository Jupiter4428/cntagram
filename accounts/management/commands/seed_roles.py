from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from accounts.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial roles and grant super_admin to superusers"

    def handle(self, *args, **options):
        ROLES = [
            (Role.STUDENT, "นักศึกษา"),
            (Role.ALUMNI, "ศิษย์เก่า"),
            (Role.MODERATOR, "ผู้ดูแลเนื้อหา"),
            (Role.SUPER_ADMIN, "ผู้ดูแลระบบ"),
        ]

        for code, name_th in ROLES:
            role, created = Role.objects.get_or_create(code=code, defaults={"name_th": name_th})
            status = "Created" if created else "Already exists"
            self.stdout.write(f"[{status}] Role: {role.code}")

        super_admin_role = Role.objects.get(code=Role.SUPER_ADMIN)
        superusers = User.objects.filter(is_superuser=True)

        for su in superusers:
            ur, created = UserRole.objects.get_or_create(user=su, role=super_admin_role)
            status = "Assigned" if created else "Already assigned"
            self.stdout.write(f"[{status}] super_admin to superuser: {su.email}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded roles and superuser permissions!"))