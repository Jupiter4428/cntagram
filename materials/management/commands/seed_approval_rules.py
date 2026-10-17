"""seed กฎอนุมัติ (doc_type_required_role) ของ US-9 ตามคลังของแต่ละประเภทเอกสาร

- คลังข้อสอบ (vault = exam): ต้องได้ทั้ง moderator และ super_admin (mode = all)
- คลังชีท (vault = lecture): moderator หรือ super_admin คนใดก็ได้ (mode = any)

ต้องมี doc_type ก่อน (seed_materials ของ US-5) รันซ้ำได้ ไม่แก้กฎที่แอดมินปรับไปแล้ว
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role
from materials.models import DocType, DocTypeRequiredRole

APPROVER_ROLES = [(Role.MODERATOR, "ผู้ดูแลภาค"), (Role.SUPER_ADMIN, "ผู้ดูแลระบบ")]
MODE_BY_VAULT = {
    DocType.Vault.EXAM: DocTypeRequiredRole.Mode.ALL,
    DocType.Vault.LECTURE: DocTypeRequiredRole.Mode.ANY,
}


class Command(BaseCommand):
    help = "Seed approval rules: exams need moderator and super_admin, others need either."

    @transaction.atomic
    def handle(self, *args, **options):
        doc_types = list(DocType.objects.all())
        if not doc_types:
            self.stdout.write(self.style.WARNING("No doc types yet: run seed_materials first."))
            return
        # role seed หลักอยู่ใน US-3 ที่นี่สร้างเฉพาะ role ที่อนุมัติได้ถ้ายังไม่มี
        roles = [
            Role.objects.get_or_create(code=code, defaults={"name_th": name_th})[0]
            for code, name_th in APPROVER_ROLES
        ]
        for doc_type in doc_types:
            for role in roles:
                DocTypeRequiredRole.objects.get_or_create(
                    doc_type=doc_type,
                    role=role,
                    defaults={"mode": MODE_BY_VAULT[doc_type.vault]},
                )
        self.stdout.write(self.style.SUCCESS("Seeded approval rules."))
