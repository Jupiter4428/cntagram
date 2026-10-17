from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts import models as account_models

User = get_user_model()

class Command(BaseCommand):
    help = "Seed initial roles (student, alumni, moderator, super_admin) and grant super_admin to superusers"

    def handle(self, *args, **kwargs):
        roles_list = ["student", "alumni", "moderator", "super_admin"]

        # -------------------------------------------------------------
        # 1. Seed Role 4 ค่า (รองรับทั้งกรณีมีตาราง Role หรือเก็บใน UserRole)
        # -------------------------------------------------------------
        role_objs = {}
        if hasattr(account_models, "Role"):
            RoleModel = getattr(account_models, "Role")
            # ตรวจสอบชื่อฟิลด์ของโมเดล Role (code หรือ name)
            field_name = "code" if hasattr(RoleModel, "code") else "name"
            for role_name in roles_list:
                role_obj, created = RoleModel.objects.get_or_create(**{field_name: role_name})
                role_objs[role_name] = role_obj
                status = "Created" if created else "Already exists"
                self.stdout.write(f"[{status}] Role: {role_name}")
        else:
            self.stdout.write("Role definition verified: student, alumni, moderator, super_admin")

        # -------------------------------------------------------------
        # 2. ให้ Superuser ทุกคนได้ UserRole(role=super_admin)
        # -------------------------------------------------------------
        UserRole = getattr(account_models, "UserRole", None)
        if not UserRole:
            self.stdout.write(self.style.ERROR("Model UserRole not found in accounts/models.py"))
            return

        superusers = User.objects.filter(is_superuser=True)
        if not superusers.exists():
            self.stdout.write(
                self.style.WARNING("No superusers found. Run 'python manage.py createsuperuser' first.")
            )

        for su in superusers:
            # ถ้า role เป็น ForeignKey ให้ใช้อ็อบเจกต์ Role ถ้าเป็น CharField ให้ใช้ string
            target_role = role_objs.get("super_admin", "super_admin")

            lookup_kwargs = {"user": su, "role": target_role}
            # ถ้า UserRole มีฟิลด์ department ให้ super_admin เป็น None (ไม่ผูกกับภาควิชาใด)
            if hasattr(UserRole, "department"):
                lookup_kwargs["department"] = None

            user_role, created = UserRole.objects.get_or_create(**lookup_kwargs)
            status = "Assigned" if created else "Already assigned"
            self.stdout.write(f"[{status}] super_admin to superuser: {su.get_username()}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded roles and superuser permissions!"))