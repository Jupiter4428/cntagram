from django.contrib.auth.models import AnonymousUser
from django.template import RequestContext, Template
from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import Role, User, UserRole
from catalog.models import Department
from materials.context_processors import approval_permissions


class ApprovalPermissionsContextProcessorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.dept = Department.objects.create(code="CN", name_th="คอมพิวเตอร์", name_en="Computer")
        cls.role_student = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})[0]
        cls.role_mod = Role.objects.get_or_create(code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแล"})[0]
        cls.role_admin = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "แอดมิน"})[0]

        cls.student = User.objects.create_user(
            email="6610610001@student.tu.ac.th",
            password="password123",
            nickname="Student1",
            department=cls.dept,
            pdpa_consent_at=now,
        )
        UserRole.objects.create(user=cls.student, role=cls.role_student)

        cls.moderator = User.objects.create_user(
            email="6610610002@student.tu.ac.th",
            password="password123",
            nickname="Mod1",
            department=cls.dept,
            pdpa_consent_at=now,
        )
        UserRole.objects.create(user=cls.moderator, role=cls.role_mod, department=cls.dept)

        cls.super_admin = User.objects.create_user(
            email="6610610003@student.tu.ac.th",
            password="password123",
            nickname="Admin1",
            department=cls.dept,
            pdpa_consent_at=now,
        )
        UserRole.objects.create(user=cls.super_admin, role=cls.role_admin)

    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_guest_gets_false(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        context = approval_permissions(request)

        self.assertFalse(context["can_review_materials"])

    def test_request_without_user_gets_false(self):
        request = self.factory.get("/")

        context = approval_permissions(request)

        self.assertFalse(context["can_review_materials"])

    def test_normal_student_gets_false(self):
        request = self.factory.get("/")
        request.user = self.student

        context = approval_permissions(request)

        self.assertFalse(context["can_review_materials"])

    def test_moderator_gets_true(self):
        request = self.factory.get("/")
        request.user = self.moderator

        context = approval_permissions(request)

        self.assertTrue(context["can_review_materials"])

    def test_super_admin_gets_true(self):
        request = self.factory.get("/")
        request.user = self.super_admin

        context = approval_permissions(request)

        self.assertTrue(context["can_review_materials"])

    def test_template_rendering_includes_can_review_materials_from_settings(self):
        request = self.factory.get("/")
        request.user = self.moderator

        template = Template("{% if can_review_materials %}REVIEW_ALLOWED{% else %}FORBIDDEN{% endif %}")
        rendered = template.render(RequestContext(request))

        self.assertIn("REVIEW_ALLOWED", rendered)
