from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, Department

User = get_user_model()


class DepartmentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # สร้าง Role พื้นฐานโดยใช้ Role constants
        self.role_student, _ = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})
        self.role_super_admin, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})

        # สร้างภาควิชาตั้งต้น
        self.dept_cn = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )

        # นักศึกษาทั่วไป
        self.student = User.objects.create_user(
            email="6810610001@student.tu.ac.th",
            password="password123",
            nickname="student_test",
            department=self.dept_cn,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.student, role=self.role_student)

        # Super Admin
        self.admin = User.objects.create_user(
            email="6810610002@student.tu.ac.th",
            password="password123",
            nickname="admin_test",
            department=self.dept_cn,
            is_superuser=True,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.admin, role=self.role_super_admin)

    def test_anonymous_user_redirect_to_login(self):
        """ผู้ใช้ที่ไม่ได้ล็อกอิน เข้าหน้านี้ต้อง redirect ไปยังหน้า login"""
        response = self.client.get(reverse("catalog:department_list"))
        login_url = reverse("accounts:login")
        expected_url = f"{login_url}?next={reverse('catalog:department_list')}"
        self.assertRedirects(response, expected_url)

    def test_permission_denied_for_non_super_admin(self):
        """User ทั่วไปที่ล็อกอินแล้ว เข้าหน้านี้ต้องได้ 403 Forbidden"""
        self.client.force_login(self.student)
        response = self.client.get(reverse("catalog:department_list"))
        self.assertEqual(response.status_code, 403)

    def test_duplicate_department_code(self):
        """เพิ่มรหัสภาควิชาซ้ำไม่ได้ โดย normalize เป็นตัวพิมพ์ใหญ่แล้วแจ้งเตือน"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:department_create"),
            {
                "code": "cn",
                "name_th": "คอมพิวเตอร์ 2",
                "name_en": "Computer 2",
                "is_active": True,
            },
        )
        self.assertEqual(Department.objects.filter(code="CN").count(), 1)
        self.assertFormError(response.context["form"], "code", "รหัสภาควิชานี้มีอยู่ในระบบแล้ว")

    def test_update_department_keep_same_code(self):
        """แก้ไขภาคโดยใช้ code เดิมต้องผ่านและ redirect ได้ปกติ"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("catalog:department_update", args=[self.dept_cn.pk]),
            {
                "code": "CN",
                "name_th": "วิศวกรรมคอมพิวเตอร์ (แก้ไข)",
                "name_en": "Computer Engineering",
                "is_active": True,
            },
        )
        self.assertRedirects(response, reverse("catalog:department_list"))
        self.dept_cn.refresh_from_db()
        self.assertEqual(self.dept_cn.name_th, "วิศวกรรมคอมพิวเตอร์ (แก้ไข)")

    def test_cannot_delete_department_with_batches(self):
        """ลบภาควิชาที่มีรุ่นผูกอยู่ไม่ได้ พร้อมแจ้งเตือนว่ายังมีรุ่น/วิชาอยู่ในภาค"""
        self.client.force_login(self.admin)
        Batch.objects.create(department=self.dept_cn, number=21)

        response = self.client.post(
            reverse("catalog:department_delete", args=[self.dept_cn.pk]),
            follow=True,
        )
        self.assertTrue(Department.objects.filter(code="CN").exists())
        self.assertContains(response, "ลบไม่ได้ เพราะยังมีรุ่น/วิชาอยู่ในภาคนี้")

    def test_cannot_delete_department_with_users(self):
        """ลบภาควิชาที่มี user ผูกอยู่ (แต่ไม่มีรุ่น) ไม่ได้ พร้อมแจ้งเตือนว่ายังมีผู้ใช้สังกัดอยู่"""
        dept_ce = Department.objects.create(code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering")
        User.objects.create_user(
            email="6810610003@student.tu.ac.th",
            password="password123",
            nickname="ce_user",
            department=dept_ce,
            pdpa_consent_at=self.now,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("catalog:department_delete", args=[dept_ce.pk]),
            follow=True,
        )
        self.assertTrue(Department.objects.filter(code="CE").exists())
        self.assertContains(response, "ลบไม่ได้ เพราะยังมีผู้ใช้สังกัดภาคนี้อยู่")

    def test_seed_commands_idempotent(self):
        """คำสั่ง seed_roles และ seed_catalog ต้องรันซ้ำได้โดยไม่สร้างข้อมูลซ้ำซ้อน"""
        call_command("seed_roles")
        call_command("seed_roles")
        call_command("seed_catalog")
        call_command("seed_catalog")

        self.assertEqual(Role.objects.count(), 4)
        self.assertEqual(Department.objects.count(), 4)