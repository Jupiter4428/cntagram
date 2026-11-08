import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from portal.permissions import is_super_admin
from materials.services import bulk_import_documents_from_csv

User = get_user_model()


class Command(BaseCommand):
    help = "Bulk import documents from a CSV file (US-17)"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
        parser.add_argument(
            "--files",
            dest="files_dir",
            type=str,
            required=True,
            help="Directory where source PDF files are located",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate rows without saving to DB or storage",
        )
        parser.add_argument(
            "--user",
            dest="user_email",
            type=str,
            default=None,
            help="Email of the Super Admin executing the import (default: first Super Admin in system)",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        files_dir = options["files_dir"]
        dry_run = options["dry_run"]
        user_email = options["user_email"]

        if not os.path.isfile(csv_file):
            raise CommandError(f"ไม่พบไฟล์ CSV: {csv_file}")

        if not os.path.isdir(files_dir):
            raise CommandError(f"ไม่พบโฟลเดอร์ไฟล์: {files_dir}")

        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                raise CommandError(f"ไม่พบผู้ใช้ที่มีอีเมล: {user_email}")
        else:
            # หา Super Admin คนแรกในระบบ
            user = (
                User.objects.filter(user_roles__role__code="super_admin")
                .order_by("pk")
                .first()
            )
            if not user:
                user = User.objects.filter(is_superuser=True).order_by("pk").first()

        if not user or not is_super_admin(user):
            raise CommandError("ต้องระบุบัญชี Super Admin ในการสั่งนำเข้า (--user)")

        try:
            with open(csv_file, "r", encoding="utf-8-sig") as f:
                csv_content = f.read()
        except Exception as e:
            raise CommandError(f"ไม่สามารถเปิดอ่านไฟล์ CSV ได้: {e}")

        mode_label = "[DRY RUN] " if dry_run else ""
        self.stdout.write(f"{mode_label}กำลังตรวจสอบและนำเข้าเอกสารจาก {csv_file}...")

        summary = bulk_import_documents_from_csv(
            csv_content=csv_content,
            files_dir=files_dir,
            user=user,
            dry_run=dry_run,
        )

        for res in summary.results:
            tag = {
                "imported": self.style.SUCCESS("[PASS]"),
                "skipped": self.style.WARNING("[SKIP]"),
                "failed": self.style.ERROR("[FAIL]"),
            }.get(res.status, res.status)
            self.stdout.write(
                f"  แถว {res.row_num}: {tag} {res.title or res.file_path} - {res.message}"
            )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"สรุปผลการนำเข้า {mode_label}:")
        self.stdout.write(f"  ทั้งหมด: {summary.total_rows} แถว")
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"  ผ่าน {summary.imported_count} แถว"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"  นำเข้าสำเร็จ {summary.imported_count} แถว")
            )
        self.stdout.write(self.style.WARNING(f"  ข้าม {summary.skipped_count} แถว"))
        self.stdout.write(self.style.ERROR(f"  ผิดพลาด {summary.failed_count} แถว"))
        self.stdout.write("=" * 50)
