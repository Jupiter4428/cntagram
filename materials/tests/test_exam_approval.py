"""เทสต์ของ US-9: กฎอนุมัติจาก doc_type_required_role, ข้อสอบต้องอนุมัติสองฝ่าย และกฎข้อสอบรุ่นเก่า"""
from importlib import import_module
from io import StringIO

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, UserRole
from catalog.models import SystemSetting

from ..models import Approval, DocType, DocTypeRequiredRole, Document
from ..selectors import approval_progress, approval_progress_for, pending_documents_for_moderator
from ..services import review_document
from .base import ApprovalBaseTestCase

User = get_user_model()


class ApprovalProgressSelectorTests(ApprovalBaseTestCase):
    """US-9: who has approved and who is still awaited, for the FE"""

    def test_exam_approved_by_moderator_awaits_super_admin(self):
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        progress = approval_progress(document=doc)

        self.assertEqual(progress.approved_roles, [self.role_moderator])
        self.assertEqual(progress.missing_roles, [self.role_super_admin])
        self.assertTrue(progress.require_all)
        self.assertTrue(progress.approvable)

    def test_rejected_exam_awaits_nobody(self):
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)
        review_document(
            document=doc, approver=self.super_admin, decision=Approval.Decision.REJECTED, reason="ละเมิดลิขสิทธิ์"
        )
        doc.refresh_from_db()

        progress = approval_progress(document=doc)

        self.assertEqual(progress.approved_roles, [self.role_moderator])
        self.assertEqual(progress.missing_roles, [])

    def test_doc_type_without_rules_awaits_nobody(self):
        doc_type_slide = DocType.objects.create(code="slide", name_th="สไลด์", vault=DocType.Vault.LECTURE)
        doc = self.create_document(doc_type=doc_type_slide)

        progress = approval_progress(document=doc)

        self.assertEqual(progress.approved_roles, [])
        self.assertEqual(progress.missing_roles, [])
        self.assertFalse(progress.approvable)

    def test_pending_sheet_awaits_either_role(self):
        doc = self.create_document(doc_type=self.doc_type_summary)

        progress = approval_progress(document=doc)

        self.assertEqual(progress.approved_roles, [])
        self.assertCountEqual(progress.missing_roles, [self.role_moderator, self.role_super_admin])
        self.assertFalse(progress.require_all)

    def test_sheet_approved_by_one_role_awaits_nobody(self):
        doc = self.create_document(doc_type=self.doc_type_summary)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        progress = approval_progress(document=doc)

        self.assertEqual(progress.approved_roles, [self.role_moderator])
        self.assertEqual(progress.missing_roles, [])

    def test_legacy_exam_awaits_super_admin_only(self):
        doc = self.create_exam_of_batch(22)

        progress = approval_progress(document=doc)

        self.assertEqual(progress.missing_roles, [self.role_super_admin])
        self.assertFalse(progress.require_all)

    def test_exam_progress_uses_three_queries(self):
        doc = Document.objects.select_related("doc_type", "batch_course__batch").get(
            pk=self.create_document(doc_type=self.doc_type_exam).pk
        )

        # rules, legacy_batch_max, approvals
        with self.assertNumQueries(3):
            approval_progress(document=doc)


class ApprovalProgressForQueueTests(ApprovalBaseTestCase):
    def test_queue_progress_of_every_document_in_three_queries(self):
        exam = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=exam, approver=self.mod_cn, decision=Approval.Decision.APPROVED)
        sheet = self.create_document(doc_type=self.doc_type_summary)
        legacy = self.create_exam_of_batch(22)
        documents = list(pending_documents_for_moderator(user=self.super_admin))

        with self.assertNumQueries(3):
            progress = approval_progress_for(documents=documents)

        self.assertEqual(
            {pk: (p.approved_roles, p.missing_roles) for pk, p in progress.items()},
            {
                exam.pk: ([self.role_moderator], [self.role_super_admin]),
                sheet.pk: ([], [self.role_moderator, self.role_super_admin]),
                legacy.pk: ([], [self.role_super_admin]),
            },
        )


class ExamDualApprovalServiceTests(ApprovalBaseTestCase):
    """US-9: approval rules come from doc_type_required_role"""

    def test_doc_type_without_rules_cannot_be_approved(self):
        doc_type_slide = DocType.objects.create(
            code="slide", name_th="สไลด์", vault=DocType.Vault.LECTURE
        )
        doc = self.create_document(doc_type=doc_type_slide)

        with self.assertRaises(PermissionDenied):
            review_document(
                document=doc, approver=self.super_admin, decision=Approval.Decision.APPROVED
            )

    def test_exam_approved_by_moderator_only_stays_pending(self):
        doc = self.create_document(doc_type=self.doc_type_exam)

        approval = review_document(
            document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PENDING)
        self.assertEqual(approval.approver_role, self.role_moderator)

    def test_exam_approved_by_moderator_then_super_admin_is_published(self):
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        review_document(
            document=doc, approver=self.super_admin, decision=Approval.Decision.APPROVED
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)

    def test_moderator_cannot_approve_exam_of_legacy_batch(self):
        doc = self.create_exam_of_batch(23)

        with self.assertRaises(PermissionDenied) as ctx:
            review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)
        self.assertIn("Super Admin เท่านั้น", str(ctx.exception))

    def test_super_admin_alone_publishes_exam_of_legacy_batch(self):
        doc = self.create_exam_of_batch(22)

        review_document(
            document=doc, approver=self.super_admin, decision=Approval.Decision.APPROVED
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)

    def test_legacy_batch_limit_is_read_from_system_setting(self):
        SystemSetting.objects.create(key=SystemSetting.LEGACY_BATCH_MAX, value="20")
        doc = self.create_exam_of_batch(22)

        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        self.assertTrue(Approval.objects.filter(document=doc, approver=self.mod_cn).exists())

    def test_user_with_both_roles_counts_for_the_side_still_missing(self):
        UserRole.objects.create(user=self.super_admin, role=self.role_moderator, department=self.dept_cn)
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        approval = review_document(
            document=doc, approver=self.super_admin, decision=Approval.Decision.APPROVED
        )

        doc.refresh_from_db()
        self.assertEqual(approval.approver_role, self.role_super_admin)
        self.assertEqual(doc.status, Document.Status.PUBLISHED)

    def test_exam_approved_by_two_moderators_stays_pending(self):
        second_mod = User.objects.create_user(
            email="6610000006@student.tu.ac.th",
            password="password123",
            nickname="ModCN2",
            department=self.dept_cn,
            pdpa_consent_at=self.now,
        )
        UserRole.objects.create(user=second_mod, role=self.role_moderator, department=self.dept_cn)
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        review_document(document=doc, approver=second_mod, decision=Approval.Decision.APPROVED)

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PENDING)

    def test_django_superuser_without_role_row_cannot_review(self):
        # super admin นับจากแถว user_role เท่านั้น เหมือน portal.permissions.is_super_admin
        superuser = User.objects.create_superuser(
            email="6610000007@student.tu.ac.th",
            password="password123",
            nickname="Root",
            department=self.dept_cn,
            pdpa_consent_at=self.now,
        )
        doc = self.create_document(doc_type=self.doc_type_summary)

        with self.assertRaises(PermissionDenied):
            review_document(document=doc, approver=superuser, decision=Approval.Decision.APPROVED)
        self.assertFalse(Approval.objects.filter(document=doc).exists())

    def test_document_no_longer_pending_cannot_be_reviewed(self):
        doc = self.create_document(doc_type=self.doc_type_exam, status=Document.Status.REJECTED)

        with self.assertRaises(ValidationError):
            review_document(
                document=doc, approver=self.super_admin, decision=Approval.Decision.APPROVED
            )
        self.assertFalse(Approval.objects.filter(document=doc).exists())

    def test_same_approver_cannot_decide_twice(self):
        doc = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)

        with self.assertRaises(ValidationError):
            review_document(document=doc, approver=self.mod_cn, decision=Approval.Decision.APPROVED)
        self.assertEqual(Approval.objects.filter(document=doc).count(), 1)


class SeedApprovalRulesCommandTests(TestCase):
    def rules(self):
        return set(DocTypeRequiredRole.objects.values_list("doc_type__code", "role__code", "mode"))

    def test_exam_needs_every_approver_role_and_sheet_needs_either(self):
        DocType.objects.create(code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM)
        DocType.objects.create(code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE)

        call_command("seed_approval_rules", stdout=StringIO())

        self.assertEqual(
            self.rules(),
            {
                ("exam", Role.MODERATOR, "all"),
                ("exam", Role.SUPER_ADMIN, "all"),
                ("summary", Role.MODERATOR, "any"),
                ("summary", Role.SUPER_ADMIN, "any"),
            },
        )

    def test_rerun_keeps_a_mode_an_admin_changed(self):
        DocType.objects.create(code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM)
        call_command("seed_approval_rules", stdout=StringIO())
        DocTypeRequiredRole.objects.update(mode=DocTypeRequiredRole.Mode.ANY)

        call_command("seed_approval_rules", stdout=StringIO())

        self.assertEqual(
            self.rules(),
            {("exam", Role.MODERATOR, "any"), ("exam", Role.SUPER_ADMIN, "any")},
        )

    def test_without_doc_types_seeds_nothing(self):
        out = StringIO()

        call_command("seed_approval_rules", stdout=out)

        self.assertIn("seed_materials", out.getvalue())
        self.assertFalse(DocTypeRequiredRole.objects.exists())


class SeedApprovalRulesMigrationTests(TestCase):
    """0005 seeds rules for doc types already in the database when it is migrated"""

    def test_existing_doc_types_get_rules_by_vault(self):
        DocType.objects.create(code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM)
        DocType.objects.create(code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE)
        migration = import_module("materials.migrations.0005_seed_approval_rules")

        migration.seed_rules(django_apps, None)

        self.assertEqual(
            set(DocTypeRequiredRole.objects.values_list("doc_type__code", "role__code", "mode")),
            {
                ("exam", Role.MODERATOR, "all"),
                ("exam", Role.SUPER_ADMIN, "all"),
                ("summary", Role.MODERATOR, "any"),
                ("summary", Role.SUPER_ADMIN, "any"),
            },
        )


class ExamApprovalViewTests(ApprovalBaseTestCase):
    def test_moderator_posting_on_legacy_exam_is_forbidden_and_told_why(self):
        doc = self.create_exam_of_batch(22)
        self.client.force_login(self.mod_cn)

        response = self.client.post(
            reverse("materials:approval_review", kwargs={"document_id": doc.pk}),
            {"decision": Approval.Decision.APPROVED, "reason": ""},
        )

        self.assertContains(response, "Super Admin เท่านั้น", status_code=403)
        self.assertFalse(Approval.objects.filter(document=doc).exists())
