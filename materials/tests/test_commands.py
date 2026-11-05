from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import SystemSetting

from ..models import DocType, DocTypeRequiredRole, ExamPeriod


class SeedMaterialsCommandTests(TestCase):
    def seed(self):
        call_command("seed_materials", stdout=StringIO())

    def test_seeds_doc_types_exam_periods_and_settings(self):
        self.seed()

        self.assertEqual(
            dict(DocType.objects.values_list("code", "vault")),
            {
                "summary": "lecture",
                "slide": "lecture",
                "cheatsheet": "lecture",
                "exam": "exam",
            },
        )
        self.assertEqual(
            set(ExamPeriod.objects.values_list("code", flat=True)), {"midterm", "final"}
        )
        self.assertEqual(SystemSetting.get_int("max_upload_mb"), 50)
        self.assertEqual(SystemSetting.get_int("legacy_batch_max"), 23)

    def test_seeds_approval_rules_for_every_doc_type(self):
        # ไม่งั้นหลังติดตั้งใหม่จะไม่มีใครอนุมัติเอกสารได้ (US-9)
        self.seed()

        self.assertEqual(
            set(DocTypeRequiredRole.objects.values_list("doc_type__code", flat=True)),
            {"summary", "slide", "cheatsheet", "exam"},
        )

    def test_rerun_does_not_duplicate_or_overwrite_admin_changes(self):
        self.seed()
        SystemSetting.objects.filter(pk="max_upload_mb").update(value="20")

        self.seed()

        self.assertEqual(DocType.objects.count(), 4)
        self.assertEqual(ExamPeriod.objects.count(), 2)
        self.assertEqual(SystemSetting.get_int("max_upload_mb"), 20)
