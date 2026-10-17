from io import StringIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, User, UserRole
from catalog.models import Batch, BatchCourse, Course, Department, SystemSetting

from .models import Approval, DocType, DocTypeRequiredRole, Document
from .services import approve_document


class ApproveDocumentTests(TestCase):
    """US-9: ข้อสอบเก่าต้องได้รับอนุมัติจากทั้ง Moderator และ Super Admin"""

    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )
        cls.moderator_role = Role.objects.create(code=Role.MODERATOR, name_th="ผู้ดูแลภาค")
        cls.admin_role = Role.objects.create(code=Role.SUPER_ADMIN, name_th="ผู้ดูแลระบบ")

        cls.exam = DocType.objects.create(
            code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM
        )
        cls.summary = DocType.objects.create(
            code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE
        )
        for role in (cls.moderator_role, cls.admin_role):
            DocTypeRequiredRole.objects.create(
                doc_type=cls.exam, role=role, mode=DocTypeRequiredRole.Mode.ALL
            )
            DocTypeRequiredRole.objects.create(
                doc_type=cls.summary, role=role, mode=DocTypeRequiredRole.Mode.ANY
            )

        cls.uploader = cls._user("6610000001", "Uploader")
        cls.moderator = cls._user("6610000002", "Mo")
        UserRole.objects.create(
            user=cls.moderator, role=cls.moderator_role, department=cls.cn
        )
        cls.admin = cls._user("6610000003", "Ad")
        UserRole.objects.create(user=cls.admin, role=cls.admin_role)

        course = Course.objects.create(code="CN200", name_en="Discrete Math")
        cls.cn25 = BatchCourse.objects.create(
            batch=Batch.objects.create(department=cls.cn, number=25), course=course
        )
        cls.cn22 = BatchCourse.objects.create(
            batch=Batch.objects.create(department=cls.cn, number=22), course=course
        )

    @classmethod
    def _user(cls, student_id, nickname):
        return User.objects.create_user(
            email=f"{student_id}@student.tu.ac.th",
            password="pw",
            nickname=nickname,
            department=cls.cn,
            pdpa_consent_at=timezone.now(),
        )

    def _document(self, *, batch_course=None, doc_type=None):
        return Document.objects.create(
            batch_course=batch_course or self.cn25,
            doc_type=doc_type or self.exam,
            uploader=self.uploader,
            title="CN200 Midterm",
            description="-",
        )

    def test_user_with_both_roles_completes_the_missing_side(self):
        both = self._user("6610000004", "Both")
        UserRole.objects.create(user=both, role=self.moderator_role, department=self.cn)
        UserRole.objects.create(user=both, role=self.admin_role)
        document = self._document()
        approve_document(document=document, approver=self.moderator)

        document = approve_document(document=document, approver=both)

        self.assertEqual(document.status, Document.Status.PUBLISHED)
        self.assertEqual(
            Approval.objects.get(approver=both).approver_role, self.admin_role
        )

    def test_exam_approved_by_moderator_alone_stays_pending(self):
        document = self._document()

        approve_document(document=document, approver=self.moderator)

        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.PENDING)
        approval = Approval.objects.get(document=document)
        self.assertEqual(approval.approver, self.moderator)
        self.assertEqual(approval.approver_role, self.moderator_role)
        self.assertEqual(approval.decision, Approval.Decision.APPROVED)

    def test_exam_approved_by_moderator_then_admin_is_published(self):
        document = self._document()

        approve_document(document=document, approver=self.moderator)
        approve_document(document=document, approver=self.admin)

        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.PUBLISHED)
        self.assertEqual(document.approvals.count(), 2)

    def test_summary_with_any_rule_is_published_by_one_moderator(self):
        document = self._document(doc_type=self.summary)

        approve_document(document=document, approver=self.moderator)

        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.PUBLISHED)

    def test_moderator_cannot_approve_legacy_batch_exam(self):
        document = self._document(batch_course=self.cn22)

        with self.assertRaises(PermissionDenied):
            approve_document(document=document, approver=self.moderator)

        self.assertFalse(document.approvals.exists())

    def test_legacy_batch_limit_is_read_from_system_setting(self):
        SystemSetting.objects.create(key=SystemSetting.LEGACY_BATCH_MAX, value="21")
        document = self._document(batch_course=self.cn22)

        approve_document(document=document, approver=self.moderator)

        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.PENDING)
        self.assertTrue(document.approvals.filter(approver=self.moderator).exists())

    def test_moderator_of_other_department_cannot_approve(self):
        me_moderator = self._user("6610000004", "MeMo")
        UserRole.objects.create(
            user=me_moderator, role=self.moderator_role, department=self.me
        )
        document = self._document()

        with self.assertRaises(PermissionDenied):
            approve_document(document=document, approver=me_moderator)

    def test_same_approver_cannot_approve_twice(self):
        document = self._document()
        approve_document(document=document, approver=self.moderator)

        with self.assertRaises(ValidationError):
            approve_document(document=document, approver=self.moderator)

        self.assertEqual(document.approvals.count(), 1)

    def test_cannot_approve_document_that_is_not_pending(self):
        document = self._document(batch_course=self.cn22)
        approve_document(document=document, approver=self.admin)
        other_admin = self._user("6610000005", "Ad2")
        UserRole.objects.create(user=other_admin, role=self.admin_role)

        with self.assertRaises(ValidationError):
            approve_document(document=document, approver=other_admin)

    def test_admin_alone_publishes_legacy_batch_exam(self):
        document = self._document(batch_course=self.cn22)

        approve_document(document=document, approver=self.admin)

        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.PUBLISHED)


class SeedApprovalRulesCommandTests(TestCase):
    def test_exam_needs_both_roles_and_lecture_types_need_either(self):
        DocType.objects.create(code="exam", name_th="ข้อสอบเก่า", vault="exam")
        DocType.objects.create(code="summary", name_th="ชีทสรุป", vault="lecture")

        call_command("seed_approval_rules", stdout=StringIO())
        call_command("seed_approval_rules", stdout=StringIO())  # รันซ้ำต้องไม่สร้างซ้ำ

        rules = set(
            DocTypeRequiredRole.objects.values_list("doc_type__code", "role__code", "mode")
        )
        self.assertEqual(
            rules,
            {
                ("exam", Role.MODERATOR, "all"),
                ("exam", Role.SUPER_ADMIN, "all"),
                ("summary", Role.MODERATOR, "any"),
                ("summary", Role.SUPER_ADMIN, "any"),
            },
        )
