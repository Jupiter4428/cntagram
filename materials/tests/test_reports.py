from django.core.exceptions import ValidationError

from django.urls import reverse

from .base import SearchTestCase
from ..models import Report
from ..services import report_document


class ReportTests(SearchTestCase):
    def setUp(self):
        self.doc = self.make_document(self.cn200[21], title="Test PDF")

    def test_report_created_and_duplicate_blocked(self):
        report = report_document(
            document=self.doc,
            reporter=self.uploader,
            reason_type=Report.Reason.COPYRIGHT,
            reason="เน€เธเธทเนเธญเธซเธฒเธกเธตเธเธฑเธเธซเธฒ",
        )
        self.assertEqual(report.status, Report.Status.OPEN)
        with self.assertRaises(ValidationError):
            report_document(
                document=self.doc,
                reporter=self.uploader,
                reason_type=Report.Reason.COPYRIGHT,
                reason="เธเนเธณ",
            )

    def test_only_published_documents_can_be_reported(self):
        self.doc.status = "hidden"
        self.doc.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            report_document(
                document=self.doc,
                reporter=self.uploader,
                reason_type=Report.Reason.OTHER,
                reason="เน€เธซเธ•เธธเธเธฅ",
            )

    def test_report_form_requires_login_and_valid_input(self):
        url = reverse("materials:report_document", args=[self.doc.pk])
        self.client.force_login(self.uploader)
        response = self.client.post(
            url, {"reason_type": "other", "reason": "เธเธดเธ”"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), 1)
        response = self.client.post(url, {"reason_type": "other", "reason": ""})
        self.assertEqual(response.status_code, 200)

    def test_normal_user_cannot_view_report_queue(self):
        self.client.force_login(self.uploader)
        response = self.client.get(reverse("materials:open_reports"))
        self.assertEqual(response.status_code, 403)
