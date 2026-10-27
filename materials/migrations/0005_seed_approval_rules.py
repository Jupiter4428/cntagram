"""seed กฎอนุมัติให้ doc_type ที่มีอยู่แล้วตอน migrate (US-9)

ไม่งั้นหลัง migrate จะไม่มีใครอนุมัติเอกสารได้เลยจนกว่าจะรัน seed_approval_rules
doc_type ที่ seed ทีหลังให้รัน `python manage.py seed_approval_rules` (กฎชุดเดียวกัน)
"""
from django.db import migrations

# ค่าชุดเดียวกับ materials/management/commands/seed_approval_rules.py แก้ที่หนึ่งต้องแก้อีกที่
# (migration ห้าม import โค้ดของ app เพราะโค้ดเปลี่ยนได้ แต่ migration ต้องรันได้เหมือนเดิม)
APPROVER_ROLES = [("moderator", "ผู้ดูแลเนื้อหา"), ("super_admin", "ผู้ดูแลระบบ")]
MODE_BY_VAULT = {"exam": "all", "lecture": "any"}


def seed_rules(apps, schema_editor):
    DocType = apps.get_model("materials", "DocType")
    DocTypeRequiredRole = apps.get_model("materials", "DocTypeRequiredRole")
    Role = apps.get_model("accounts", "Role")
    doc_types = list(DocType.objects.all())
    if not doc_types:
        return
    roles = [
        Role.objects.get_or_create(code=code, defaults={"name_th": name_th})[0]
        for code, name_th in APPROVER_ROLES
    ]
    for doc_type in doc_types:
        for role in roles:
            DocTypeRequiredRole.objects.get_or_create(
                doc_type=doc_type, role=role, defaults={"mode": MODE_BY_VAULT[doc_type.vault]}
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_department"),
        ("materials", "0004_doc_type_required_role"),
    ]

    operations = [
        migrations.RunPython(seed_rules, migrations.RunPython.noop),
    ]
