from django.contrib.auth.models import AnonymousUser
from django.template import RequestContext, Template
from django.test import RequestFactory

from materials.context_processors import approval_permissions

from .base import ApprovalBaseTestCase


class ApprovalPermissionsContextProcessorTests(ApprovalBaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_anonymous_guest_gets_false(self):
        """Guest (ยังไม่ได้ล็อกอิน) ได้ can_review_materials เป็น False"""
        request = self.factory.get("/")
        request.user = AnonymousUser()

        context = approval_permissions(request)

        self.assertFalse(bool(context["can_review_materials"]))

    def test_request_without_user_gets_false(self):
        """Request ที่ไม่มี attribute user ได้ can_review_materials เป็น False"""
        request = self.factory.get("/")

        context = approval_permissions(request)

        self.assertFalse(bool(context["can_review_materials"]))

    def test_normal_student_gets_false(self):
        """นักศึกษาทั่วไปได้ can_review_materials เป็น False"""
        request = self.factory.get("/")
        request.user = self.normal_student

        context = approval_permissions(request)

        self.assertFalse(bool(context["can_review_materials"]))

    def test_moderator_gets_true(self):
        """Moderator ประจำภาควิชาได้ can_review_materials เป็น True"""
        request = self.factory.get("/")
        request.user = self.mod_cn

        context = approval_permissions(request)

        self.assertTrue(bool(context["can_review_materials"]))

    def test_super_admin_gets_true(self):
        """Super Admin ได้ can_review_materials เป็น True"""
        request = self.factory.get("/")
        request.user = self.super_admin

        context = approval_permissions(request)

        self.assertTrue(bool(context["can_review_materials"]))

    def test_template_rendering_includes_can_review_materials_from_settings(self):
        """การประเมิน template สามารถอ่านและประเมินค่า can_review_materials ได้อย่างถูกต้อง"""
        request = self.factory.get("/")
        request.user = self.mod_cn

        template = Template("{% if can_review_materials %}REVIEW_ALLOWED{% else %}FORBIDDEN{% endif %}")
        rendered = template.render(RequestContext(request))

        self.assertIn("REVIEW_ALLOWED", rendered)

    def test_unused_flag_runs_no_query(self):
        """หน้าที่ไม่ได้เรียกใช้ can_review_materials จะไม่รัน query ใดๆ (SimpleLazyObject)"""
        request = self.factory.get("/")
        request.user = self.mod_cn

        with self.assertNumQueries(0):
            Template("no flag here").render(RequestContext(request))
