from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Department

User = get_user_model()


class CatalogTestCase(TestCase):
    """setUp ร่วม: ภาค CN, นักศึกษาทั่วไป และ Super Admin"""

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
