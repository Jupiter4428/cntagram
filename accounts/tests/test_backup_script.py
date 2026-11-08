import re
from django.test import SimpleTestCase


def is_production_database_url(url: str) -> bool:
    """Determine whether a database URL points to a production database."""
    db_name = re.sub(r"\?.*", "", url.split("/")[-1]) if "/" in url else ""
    if re.search(r"(render\.com|onrender\.com)", url):
        return True
    if "test" not in db_name and "localhost" not in url and "127.0.0.1" not in url:
        return True
    return False


def verify_production_restore_allowed(
    target_url: str,
    allow_destructive: str | None,
    confirm_production_restore: str | None,
) -> tuple[bool, str]:
    """Validate permissions before performing database restoration."""
    if allow_destructive != "YES":
        return False, "ALLOW_DESTRUCTIVE_RESTORE=YES required"

    db_name = (
        re.sub(r"\?.*", "", target_url.split("/")[-1]) if "/" in target_url else ""
    )
    if is_production_database_url(target_url):
        if confirm_production_restore != db_name:
            return (
                False,
                f"CONFIRM_PRODUCTION_RESTORE must match target database '{db_name}'",
            )

    return True, "Allowed"


def compare_table_row_counts(
    source_counts: dict[str, int],
    restored_counts: dict[str, int],
) -> list[str]:
    """Compare table row counts and return list of mismatched table descriptions."""
    mismatches = []
    for table, src_cnt in source_counts.items():
        dst_cnt = restored_counts.get(table)
        if dst_cnt is None:
            mismatches.append(f"{table}: missing in restored database")
        elif src_cnt != dst_cnt:
            mismatches.append(f"{table}: source={src_cnt} vs restored={dst_cnt}")
    return mismatches


class BackupRestoreSafetyTests(SimpleTestCase):
    def test_production_url_detection(self):
        prod_urls = [
            "postgres://user:pass@dpg-abc-a.singapore-postgres.render.com/cntagram",
            "postgres://user:pass@prod-db.example.com:5432/cntagram",
            "postgres://user:pass@192.168.1.50:5432/cntagram_live",
        ]
        for url in prod_urls:
            with self.subTest(url=url):
                self.assertTrue(is_production_database_url(url))

    def test_non_production_url_detection(self):
        non_prod_urls = [
            "postgres://user:pass@localhost:5432/cntagram_dev",
            "postgres://user:pass@127.0.0.1:5432/cntagram",
            "postgres://user:pass@db.example.com/cntagram_restore_test",
            "postgres://user:pass@db.example.com/test_db",
        ]
        for url in non_prod_urls:
            with self.subTest(url=url):
                self.assertFalse(is_production_database_url(url))

    def test_restore_refuses_without_destructive_flag(self):
        url = "postgres://user:pass@localhost:5432/cntagram_test"
        allowed, msg = verify_production_restore_allowed(
            target_url=url,
            allow_destructive=None,
            confirm_production_restore=None,
        )
        self.assertFalse(allowed)
        self.assertIn("ALLOW_DESTRUCTIVE_RESTORE", msg)

    def test_restore_to_production_refuses_without_exact_db_name_confirmation(self):
        url = "postgres://user:pass@dpg-abc.singapore-postgres.render.com/cntagram"
        # Missing confirmation
        allowed, msg = verify_production_restore_allowed(
            target_url=url,
            allow_destructive="YES",
            confirm_production_restore=None,
        )
        self.assertFalse(allowed)
        self.assertIn("CONFIRM_PRODUCTION_RESTORE", msg)

        # Mismatched confirmation
        allowed, msg = verify_production_restore_allowed(
            target_url=url,
            allow_destructive="YES",
            confirm_production_restore="wrong_db",
        )
        self.assertFalse(allowed)
        self.assertIn("CONFIRM_PRODUCTION_RESTORE", msg)

        # Exact match confirmation
        allowed, msg = verify_production_restore_allowed(
            target_url=url,
            allow_destructive="YES",
            confirm_production_restore="cntagram",
        )
        self.assertTrue(allowed)
        self.assertEqual(msg, "Allowed")

    def test_compare_table_row_counts_matches_100_percent(self):
        source = {
            "app_user": 10,
            "department": 4,
            "course": 25,
            "document": 15,
        }
        restored = dict(source)
        mismatches = compare_table_row_counts(source, restored)
        self.assertEqual(mismatches, [])

    def test_compare_table_row_counts_detects_mismatch(self):
        source = {
            "app_user": 10,
            "department": 4,
            "course": 25,
        }
        restored = {
            "app_user": 9,
            "department": 4,
            # course missing
        }
        mismatches = compare_table_row_counts(source, restored)
        self.assertEqual(len(mismatches), 2)
        self.assertIn("app_user: source=10 vs restored=9", mismatches)
        self.assertIn("course: missing in restored database", mismatches)
