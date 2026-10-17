"""seed รุ่นและวิชาตัวอย่าง (US-4) ให้ทีมใช้ทดสอบอัปโหลดชีท (US-5) ได้เลย

รันซ้ำได้ ไม่สร้างข้อมูลซ้ำ ชื่อวิชาเป็นข้อมูลตัวอย่าง แก้ภายหลังได้
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Batch, BatchCourse, Course, Department

# seed ภาควิชาครบชุด (CN, CE, ME, EE) เป็นงานของ US-3 ที่นี่สร้างเฉพาะ CN ถ้ายังไม่มี
DEPARTMENT = {
    "code": "CN",
    "name_th": "วิศวกรรมคอมพิวเตอร์",
    "name_en": "Computer Engineering",
}
BATCH_NUMBERS = [21, 22, 23, 24, 25]
COURSES = [
    ("CN101", "Introduction to Computer Programming"),
    ("CN200", "Discrete Mathematics"),
    ("CN201", "Data Structures and Algorithms"),
    ("SC135", "General Physics"),
]


class Command(BaseCommand):
    help = "Seed sample batches (CN21-CN25) and courses shared across batches."

    @transaction.atomic
    def handle(self, *args, **options):
        department, _ = Department.objects.get_or_create(
            code=DEPARTMENT["code"],
            defaults={
                "name_th": DEPARTMENT["name_th"],
                "name_en": DEPARTMENT["name_en"],
            },
        )
        courses = [
            Course.objects.get_or_create(code=code, defaults={"name_en": name_en})[0]
            for code, name_en in COURSES
        ]

        created = {"batch": 0, "batch_course": 0}
        for number in BATCH_NUMBERS:
            batch, is_new = Batch.objects.get_or_create(
                department=department, number=number
            )
            created["batch"] += is_new
            for course in courses:
                _, is_new = BatchCourse.objects.get_or_create(batch=batch, course=course)
                created["batch_course"] += is_new

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded catalog: {created['batch']} new batches, "
                f"{created['batch_course']} new batch courses."
            )
        )
