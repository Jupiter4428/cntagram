from django.core.management.base import BaseCommand
from catalog.models import Department

class Command(BaseCommand):
    help = "Seed initial departments (CN, CE, ME, EE)"

    def handle(self, *args, **kwargs):
        # รายการภาควิชาเริ่มต้นตามเงื่อนไขใน Ticket
        departments_data = [
            {"code": "CN", "name_th": "วิศวกรรมคอมพิวเตอร์", "name_en": "Computer Engineering"},
            {"code": "CE", "name_th": "วิศวกรรมโยธา", "name_en": "Civil Engineering"},
            {"code": "ME", "name_th": "วิศวกรรมเครื่องกล", "name_en": "Mechanical Engineering"},
            {"code": "EE", "name_th": "วิศวกรรมไฟฟ้า", "name_en": "Electrical Engineering"},
        ]

        # ใช้ get_or_create เพื่อให้รันซ้ำได้โดยไม่เกิด Error ข้อมูลซ้ำ
        for item in departments_data:
            dept, created = Department.objects.get_or_create(
                code=item["code"],
                defaults={
                    "name_th": item["name_th"],
                    "name_en": item["name_en"],
                    "is_active": True,
                }
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(f"[{status}] {dept.code}: {dept.name_th}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded departments!"))