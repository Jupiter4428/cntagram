from django.core.management import call_command

from accounts.models import Role
from catalog.models import Batch, BatchCourse, Course, Department

from .base import CatalogTestCase


class SeedCommandTests(CatalogTestCase):
    def test_seed_commands_idempotent(self):
        """คำสั่ง seed_roles และ seed_catalog ต้องรันซ้ำได้โดยไม่สร้างข้อมูลซ้ำซ้อน"""
        call_command("seed_roles")
        call_command("seed_roles")
        call_command("seed_catalog")
        call_command("seed_catalog")

        self.assertEqual(Role.objects.count(), 4)
        self.assertEqual(Department.objects.count(), 4)
        # รุ่นตัวอย่าง CN21-CN25 ใช้วิชาชุดเดียวกัน 4 วิชา (ไม่สร้างวิชาซ้ำต่อรุ่น)
        self.assertEqual(
            [b.code for b in Batch.objects.all()], ["CN21", "CN22", "CN23", "CN24", "CN25"]
        )
        self.assertEqual(Course.objects.count(), 4)
        self.assertEqual(BatchCourse.objects.count(), 5 * 4)
