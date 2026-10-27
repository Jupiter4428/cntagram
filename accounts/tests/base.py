from django.contrib.auth import get_user_model
from django.utils import timezone

from catalog.models import Department

from ..models import Role, UserRole
from ..services import register_user

User = get_user_model()

VALID_PASSWORD = "Cn331-Strong-Passw0rd"


class RegistrationTestMixin:
    """ข้อมูลตั้งต้นและ payload ที่ถูกต้องสำหรับทดสอบการสมัครสมาชิก"""

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )
        cls.inactive_department = Department.objects.create(
            code="OLD",
            name_th="ภาคที่ปิดแล้ว",
            name_en="Closed Department",
            is_active=False,
        )

    def register(self, **overrides):
        kwargs = {
            "email": "6610612345@student.tu.ac.th",
            "password": VALID_PASSWORD,
            "nickname": "Ploy",
            "department": self.department,
            "pdpa_consent_at": timezone.now(),
        }
        kwargs.update(overrides)
        return register_user(**kwargs)

    def payload(self, **overrides):
        data = {
            "email": "6610612345@student.tu.ac.th",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
            "nickname": "Ploy",
            "department": str(self.department.pk),
            "pdpa_consent": "on",
        }
        data.update(overrides)
        return {k: v for k, v in data.items() if v is not None}


class ModeratorTestMixin:
    """ข้อมูลตั้งต้นสำหรับทดสอบการจัดการและสิทธิ์ของ moderator"""

    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()
        cls.role_super_admin, _ = Role.objects.get_or_create(
            code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"}
        )
        cls.role_moderator, _ = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )
        cls.role_student, _ = Role.objects.get_or_create(
            code=Role.STUDENT, defaults={"name_th": "นักศึกษา"}
        )

        cls.dept_cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.dept_ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )
        cls.dept_me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )

        cls.admin = User.objects.create_user(
            email="6510610099@student.tu.ac.th",
            password="password123",
            nickname="admin",
            department=cls.dept_cn,
            is_superuser=True,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.admin, role=cls.role_super_admin)

        cls.user_momo = User.objects.create_user(
            email="6510610001@student.tu.ac.th",
            password="password123",
            nickname="momo",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.user_momo, role=cls.role_student)

        cls.user_nana = User.objects.create_user(
            email="6510610002@student.tu.ac.th",
            password="password123",
            nickname="nana",
            department=cls.dept_ce,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.user_nana, role=cls.role_student)
