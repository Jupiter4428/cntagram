from django.core.exceptions import PermissionDenied, ValidationError

from django.urls import reverse

from accounts.models import Role, UserRole
from .base import SearchTestCase
from ..models import Report, TakedownRequest, Document
from ..services import resolve_report


class ResolveReportTests(SearchTestCase):
    def setUp(self):
        self.doc = self.make_document(self.cn200[21], title="Review me")
        self.report = Report.objects.create(
            document=self.doc,
            reporter=self.uploader,
            reason_type=Report.Reason.COPYRIGHT,
            reason="copyright",
        )
        role, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN)
        UserRole.objects.create(user=self.uploader, role=role)

    def test_remove_hides_document_and_records_decision(self):
        result = resolve_report(
            kind="report",
            report_id=self.report.pk,
            actor=self.uploader,
            decision="remove",
            resolution_reason="confirmed",
        )
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, Document.Status.HIDDEN)
        self.assertEqual(result.handled_by, self.uploader)
        self.assertIsNotNone(result.resolved_at)
        with self.assertRaises(ValidationError):
            resolve_report(
                kind="report",
                report_id=self.report.pk,
                actor=self.uploader,
                decision="dismiss",
                resolution_reason="again",
            )

    def test_dismiss_keeps_document_published(self):
        resolve_report(
            kind="report",
            report_id=self.report.pk,
            actor=self.uploader,
            decision="dismiss",
            resolution_reason="not substantiated",
        )
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, Document.Status.PUBLISHED)

    def test_external_claim_needs_document_for_removal(self):
        claim = TakedownRequest.objects.create(
            claimant_name="Owner",
            contact_email="owner@example.com",
            content_identifier="CN200",
            reason="copyright",
            rights_confirmed=True,
        )
        with self.assertRaises(ValidationError):
            resolve_report(
                kind="takedown",
                report_id=claim.pk,
                actor=self.uploader,
                decision="remove",
                resolution_reason="confirmed",
            )
        resolve_report(
            kind="takedown",
            report_id=claim.pk,
            actor=self.uploader,
            decision="remove",
            resolution_reason="confirmed",
            document_id=self.doc.pk,
        )
        claim.refresh_from_db()
        self.assertEqual(claim.document, self.doc)

    def test_non_admin_denied(self):
        UserRole.objects.filter(user=self.uploader).delete()
        with self.assertRaises(PermissionDenied):
            resolve_report(
                kind="report",
                report_id=self.report.pk,
                actor=self.uploader,
                decision="remove",
                resolution_reason="test",
            )
        self.client.force_login(self.uploader)
        self.assertEqual(
            self.client.get(reverse("materials:review_reports")).status_code, 403
        )

    def test_admin_can_view_queue(self):
        self.client.force_login(self.uploader)
        response = self.client.get(reverse("materials:review_reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review me")

    def test_dismiss_restores_hidden_document(self):
        self.doc.status = Document.Status.HIDDEN
        self.doc.save(update_fields=["status"])
        resolve_report(
            kind="report",
            report_id=self.report.pk,
            actor=self.uploader,
            decision="dismiss",
            resolution_reason="ไม่พบการละเมิด",
        )
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, Document.Status.PUBLISHED)

    def test_resolve_view_post_redirects_and_hides_document(self):
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["report", self.report.pk])
        response = self.client.post(
            url, {"decision": "remove", "resolution_reason": "ยืนยันการละเมิด"}
        )
        self.assertRedirects(response, reverse("materials:review_reports"))
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, Document.Status.HIDDEN)

    def test_resolve_view_requires_admin(self):
        UserRole.objects.filter(user=self.uploader).delete()
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["report", self.report.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(
                url, {"decision": "dismiss", "resolution_reason": "x"}
            ).status_code,
            403,
        )

    def test_unknown_kind_returns_404(self):
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["unknown", self.report.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_selector_has_constant_query_count(self):
        from ..selectors import review_all_reports

        for i in range(3):
            doc = self.make_document(self.cn200[21], title=f"Doc {i}")
            Report.objects.create(
                document=doc,
                reporter=self.uploader,
                reason_type=Report.Reason.OTHER,
                reason="test",
            )
        with self.assertNumQueries(2):
            reports, takedowns = review_all_reports(status="open")
            list(reports)
            list(takedowns)

    def test_takedown_unknown_document_is_form_error(self):
        claim = TakedownRequest.objects.create(
            claimant_name="Owner",
            contact_email="owner@example.com",
            content_identifier="CN200",
            reason="copyright",
            rights_confirmed=True,
        )
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["takedown", claim.pk])
        response = self.client.post(
            url,
            {
                "decision": "remove",
                "resolution_reason": "ตรวจแล้ว",
                "document_id": 999999,
            },
        )
        self.assertEqual(response.status_code, 200)
        claim.refresh_from_db()
        self.assertEqual(claim.status, "open")

    def test_resolution_get_shows_document_and_age(self):
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["report", self.report.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review me")
        self.assertContains(response, "ส่งเมื่อ")

    def test_resolution_post_redirects_and_hides_document(self):
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["report", self.report.pk])
        response = self.client.post(
            url, {"decision": "remove", "resolution_reason": "copyright confirmed"}
        )
        self.assertRedirects(response, reverse("materials:review_reports"))
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, Document.Status.HIDDEN)

    def test_resolution_view_non_admin_returns_403(self):
        UserRole.objects.filter(user=self.uploader).delete()
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["report", self.report.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(
                url, {"decision": "dismiss", "resolution_reason": "test"}
            ).status_code,
            403,
        )

    def test_resolution_view_invalid_kind_returns_404(self):
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["unknown", self.report.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_resolution_view_invalid_document_id_shows_form_error(self):
        claim = TakedownRequest.objects.create(
            claimant_name="Owner",
            contact_email="owner@example.com",
            content_identifier="unknown",
            reason="copyright",
            rights_confirmed=True,
        )
        self.client.force_login(self.uploader)
        url = reverse("materials:resolve_report", args=["takedown", claim.pk])
        response = self.client.post(
            url,
            {
                "decision": "remove",
                "resolution_reason": "confirmed",
                "document_id": 999999,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ไม่พบเอกสารที่ระบุ")
        claim.refresh_from_db()
        self.assertEqual(claim.status, TakedownRequest.Status.OPEN)

    def test_review_all_reports_constant_queries(self):
        from ..selectors import review_all_reports

        for i in range(3):
            doc = self.make_document(self.cn200[21], title=f"Doc {i}")
            Report.objects.create(
                document=doc,
                reporter=self.uploader,
                reason_type=Report.Reason.OTHER,
                reason="reason",
            )
        with self.assertNumQueries(2):
            reports, takedowns = review_all_reports(status="open")
            list(reports)
            list(takedowns)
