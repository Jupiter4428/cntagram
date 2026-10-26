from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Batch, BatchCourse, Course, Department

class Command(BaseCommand):
    help = "Seed initial departments (CN, CE, ME, EE) and sample batches CN21-CN25 with shared courses"

    @transaction.atomic
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

        # รุ่นตัวอย่างให้ US-5 อัปโหลดชีทได้เลย ทุกรุ่นผูกวิชาชุดเดียวกัน (Course สร้างครั้งเดียว)
        courses_data = [
            ("CN101", "Introduction to Computer Programming"),
            ("CN200", "Discrete Mathematics"),
            ("CN201", "Data Structures and Algorithms"),
            ("SC135", "General Physics"),
        ]
        courses = [
            Course.objects.get_or_create(code=code, defaults={"name_en": name_en})[0]
            for code, name_en in courses_data
        ]
        cn = Department.objects.get(code="CN")
        for number in range(21, 26):
            batch, created = Batch.objects.get_or_create(department=cn, number=number)
            for course in courses:
                BatchCourse.objects.get_or_create(batch=batch, course=course)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"[{status}] {batch.code}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded batches and courses!"))