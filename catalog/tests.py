from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, Department

User = get_user_model()


class DepartmentTests(TestCase):

  def setUp(self):
    self.client = Client()
    now = timezone.now()

    # 1. สร้าง Role จำลองใน Test DB ก่อน (รองรับทั้งฟิลด์ code หรือ name)
    role_field = "code" if hasattr(Role, "code") else "name"
    self.role_student, _ = Role.objects.get_or_create(
        **{role_field: "student"}
    )
    self.role_super_admin, _ = Role.objects.get_or_create(
        **{role_field: "super_admin"}
    )

    # 2. สร้างภาควิชาเริ่มต้นสำหรับใช้ทดสอบ
    self.dept_cn = Department.objects.create(
        code="CN",
        name_th="วิศวกรรมคอมพิวเตอร์",
        name_en="Computer Engineering",
    )

    # 3. สร้าง User ทั่วไป (student)
    self.student = User.objects.create_user(
        email="6810610001@student.tu.ac.th",
        password="password123",
        nickname="student_test",
        department=self.dept_cn,
        pdpa_consent_at=now,
    )
    # ส่ง Instance ของ Role เข้าไป
    UserRole.objects.create(user=self.student, role=self.role_student)

    # 4. สร้าง Super Admin
    self.admin = User.objects.create_user(
        email="6810610002@student.tu.ac.th",
        password="password123",
        nickname="admin_test",
        department=self.dept_cn,
        is_superuser=True,
        pdpa_consent_at=now,
    )
    # ส่ง Instance ของ Role เข้าไป
    UserRole.objects.create(user=self.admin, role=self.role_super_admin)

  def test_permission_denied_for_non_super_admin(self):
    """User ทั่วไปเข้าหน้านี้ต้องได้ 403 Forbidden"""
    self.client.force_login(self.student)
    response = self.client.get(reverse("catalog:department_list"))
    self.assertEqual(response.status_code, 403)

  def test_duplicate_department_code(self):
    """แต่งตั้ง/เพิ่มรหัสภาควิชาซ้ำไม่ได้ (ตรวจสอบ unique และ normalize)"""
    self.client.force_login(self.admin)
    response = self.client.post(
        reverse("catalog:department_create"),
        {
            "code": "cn",  # ตัวพิมพ์เล็ก ระบบต้อง normalize เป็น CN
            "name_th": "คอมพิวเตอร์ 2",
            "name_en": "Computer 2",
            "is_active": True,
        },
    )
    self.assertEqual(Department.objects.filter(code="CN").count(), 1)
    self.assertIn("code", response.context["form"].errors)

  def test_cannot_delete_department_with_batches(self):
    """ลบภาควิชาที่มีรุ่นผูกอยู่ไม่ได้ พร้อมแจ้งเตือนภาษาไทย (PROTECT)"""
    self.client.force_login(self.admin)
    Batch.objects.create(department=self.dept_cn, number=21)

    response = self.client.post(
        reverse("catalog:department_delete", args=[self.dept_cn.pk]),
        follow=True,
    )
    self.assertTrue(Department.objects.filter(code="CN").exists())
    self.assertContains(response, "ลบไม่ได้ เพราะยังมีรุ่น/วิชาอยู่ในภาคนี้")