"""seed ข้อมูลตั้งต้นที่ฟอร์มอัปโหลดชีท (US-5) ต้องใช้: ประเภทเอกสาร ช่วงสอบ และค่าตั้งระบบ

รันซ้ำได้ ไม่สร้างซ้ำ และไม่เขียนทับค่าที่แอดมินแก้ไปแล้ว
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import SystemSetting
from materials.models import DocType, ExamPeriod

DOC_TYPES = [
    ("summary", "ชีทสรุป", DocType.Vault.LECTURE),
    ("slide", "สไลด์", DocType.Vault.LECTURE),
    ("cheatsheet", "ชีทย่อ", DocType.Vault.LECTURE),
    ("exam", "ข้อสอบเก่า", DocType.Vault.EXAM),
]
EXAM_PERIODS = [("midterm", "กลางภาค"), ("final", "ปลายภาค")]
SETTINGS = {SystemSetting.MAX_UPLOAD_MB: "50", SystemSetting.LEGACY_BATCH_MAX: "23"}


class Command(BaseCommand):
    help = "Seed document types, exam periods and default system settings."

    @transaction.atomic
    def handle(self, *args, **options):
        for code, name_th, vault in DOC_TYPES:
            DocType.objects.get_or_create(
                code=code, defaults={"name_th": name_th, "vault": vault}
            )
        for code, name_th in EXAM_PERIODS:
            ExamPeriod.objects.get_or_create(code=code, defaults={"name_th": name_th})
        for key, value in SETTINGS.items():
            SystemSetting.objects.get_or_create(key=key, defaults={"value": value})
        self.stdout.write(self.style.SUCCESS("Seeded materials data."))
