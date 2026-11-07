from django.urls import reverse

from ..models import DocType, Document
from .base import ApprovalBaseTestCase


class AdminDashboardMissingRulesWarningTests(ApprovalBaseTestCase):
    def test_admin_home_warns_when_pending_documents_lack_approval_rules(self):
        self.client.force_login(self.super_admin)

        # Baseline: No pending documents without rules
        res_baseline = self.client.get(reverse("accounts:home"))
        self.assertNotContains(res_baseline, "ไม่มีกฎการอนุมัติ")

        # Create doc_type without rules and a pending document
        no_rule_type = DocType.objects.create(
            code="cheatsheet", name_th="สูตรลัด", vault=DocType.Vault.LECTURE
        )
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=no_rule_type,
            uploader=self.uploader_cn,
            title="Cheat Sheet Document",
            status=Document.Status.PENDING,
        )

        res_with_warning = self.client.get(reverse("accounts:home"))
        self.assertContains(res_with_warning, "ไม่มีกฎการอนุมัติ")
        self.assertContains(res_with_warning, "สูตรลัด")
        self.assertContains(res_with_warning, "<strong>1</strong> ฉบับ")
        self.assertContains(
            res_with_warning, reverse("admin:materials_doctype_changelist")
        )
