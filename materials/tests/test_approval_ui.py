"""Integration tests for US-9 approval status presentation."""

from django.urls import reverse

from ..models import Approval
from ..services import review_document
from .base import ApprovalBaseTestCase


class ApprovalStatusUITests(ApprovalBaseTestCase):
    def test_queue_shows_moderator_approval_and_admin_still_needed(self):
        document = self.create_document(doc_type=self.doc_type_exam)
        review_document(document=document, approver=self.mod_cn, decision=Approval.Decision.APPROVED)
        self.client.force_login(self.super_admin)

        response = self.client.get(reverse("materials:approval_queue"))

        self.assertEqual(response.status_code, 200)
        shown = next(doc for doc in response.context["documents"] if doc.pk == document.pk)
        self.assertEqual(shown.approval_ui.approved_roles, [self.role_moderator])
        self.assertEqual(shown.approval_ui.missing_roles, [self.role_super_admin])
        self.assertTrue(shown.approval_ui.can_review)

    def test_review_page_has_approval_ui_for_authorized_moderator(self):
        document = self.create_document(doc_type=self.doc_type_exam)
        self.client.force_login(self.mod_cn)

        response = self.client.get(reverse("materials:approval_review", args=[document.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["document"].approval_ui.can_review)
        self.assertCountEqual(
            response.context["document"].approval_ui.missing_roles,
            [self.role_moderator, self.role_super_admin],
        )

    def test_legacy_exam_blocks_moderator_with_reason(self):
        document = self.create_exam_of_batch(22)
        self.client.force_login(self.mod_cn)

        response = self.client.get(reverse("materials:approval_review", args=[document.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["document"].approval_ui.can_review)
        self.assertIn("Super Admin", response.context["document"].approval_ui.reason)
