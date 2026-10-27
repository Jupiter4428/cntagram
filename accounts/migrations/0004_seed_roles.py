from django.db import migrations

ROLES = [
    ("student", "นักศึกษา"),
    ("alumni", "ศิษย์เก่า"),
    ("moderator", "ผู้ดูแลเนื้อหา"),
    ("super_admin", "ผู้ดูแลระบบ"),
]


def seed_roles(apps, schema_editor):
    """สร้าง role ตั้งต้นให้ระบบสมัครสมาชิก (US-1) และจัดการ moderator (US-10) ใช้ได้ทันทีหลัง migrate"""
    Role = apps.get_model("accounts", "Role")
    for code, name_th in ROLES:
        Role.objects.get_or_create(code=code, defaults={"name_th": name_th})


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_department"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
