from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from accounts import selectors, services
from catalog.models import Department

User = get_user_model()


class ModeratorManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        self.role_super_admin, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        self.role_moderator, _ = Role.objects.get_or_create(code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"})
        self.role_student, _ = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})

        self.dept_cn = Department.objects.create(code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering")
        self.dept_ce = Department.objects.create(code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering")
        self.dept_me = Department.objects.create(code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering")

        self.admin = User.objects.create_user(
            email = "6510610099@student.tu.ac.th",
            password="password123",
            nickname="admin",
            department=self.dept_cn,
            is_superuser=True,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.admin, role=self.role_super_admin)

        self.user_momo = User.objects.create_user(
            email = "6510610001@student.tu.ac.th",
            password="password123",
            nickname="momo",
            department=self.dept_cn,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=self.user_momo, role=self.role_student)

    def test_assign_and_remove_moderator_many_to_many(self):
        """AC: ผูก user กับหลายภาควิชาได้ (M:N) และถอดถอนได้"""
        ur1 = services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)
        ur2 = services.assign_moderator(user=self.user_momo, department=self.dept_ce, granted_by=self.admin)

        self.assertTrue(selectors.is_moderator_of_department(self.user_momo, self.dept_cn))
        self.assertTrue(selectors.is_moderator_of_department(self.user_momo, self.dept_ce))

        services.remove_moderator(user_role=ur1)
        self.assertFalse(selectors.is_moderator_of_department(self.user_momo, self.dept_cn))
        self.assertTrue(selectors.is_moderator_of_department(self.user_momo, self.dept_ce))

    def test_moderator_cannot_moderate_other_departments(self):
        """AC: Moderator ภาคหนึ่ง ไม่มีสิทธิ์จัดการภาคอื่น"""
        services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)

        self.assertTrue(selectors.is_moderator_of_department(self.user_momo, self.dept_cn))
        self.assertFalse(selectors.is_moderator_of_department(self.user_momo, self.dept_me))

    def test_cannot_assign_duplicate_moderator(self):
        """AC: แต่งตั้งซ้ำ (user + ภาคเดิม) ไม่ได้ และบันทึก granted_by ถูกต้อง"""
        ur = services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)
        self.assertEqual(ur.granted_by, self.admin)

        with self.assertRaises(ValidationError):
            services.assign_moderator(user=self.user_momo, department=self.dept_cn, granted_by=self.admin)

    def test_non_super_admin_gets_403(self):
        """Security: ผู้ใช้ที่ไม่ใช่ Super Admin เข้าหน้านี้ต้องได้ 403 Forbidden"""
        self.client.force_login(self.user_momo)
        response = self.client.get(reverse("accounts:moderator_manage"))
        self.assertEqual(response.status_code, 403)