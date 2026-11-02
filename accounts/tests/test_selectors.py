import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Batch, Course, Department

from .. import selectors, services
from ..models import Role, UserRole
from ..selectors import admin_dashboard
from .base import ModeratorTestCase

User = get_user_model()


class AdminDashboardSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(code="CN", name_th="คอมพิวเตอร์", name_en="Computer")
        Department.objects.create(code="OLD", name_th="ภาคเก่า", name_en="Old", is_active=False)
        Batch.objects.create(department=cls.cn, number=21)
        Batch.objects.create(department=cls.cn, number=22)
        for code in ("CN101", "CN102", "SC135"):
            Course.objects.create(code=code, name_en=code)
        student, _ = Role.objects.get_or_create(code=Role.STUDENT, defaults={"name_th": "นักศึกษา"})
        admin, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        cls.users = []
        for i, role in enumerate((student, student, admin)):
            user = User.objects.create_user(
                email=f"661000000{i}@student.tu.ac.th",
                password="pw",
                nickname=f"User{i}",
                department=cls.cn,
                pdpa_consent_at=timezone.now(),
            )
            UserRole.objects.create(user=user, role=role)
            cls.users.append(user)

    def test_totals_count_active_departments_batches_and_courses(self):
        totals = admin_dashboard()["totals"]

        self.assertEqual(
            (totals["departments"], totals["batches"], totals["courses"]),
            (1, 2, 3),
        )

    def test_role_counts_are_sorted_by_count_with_percent_and_donut_slice(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            dashboard["roles"],
            [
                {"label": "นักศึกษา", "count": 2, "percent": 67, "offset": 0, "end": 67},
                {"label": "ผู้ดูแลระบบ", "count": 1, "percent": 33, "offset": 67, "end": 100},
            ],
        )

    def test_role_counts_count_a_moderator_of_two_departments_once(self):
        moderator, _ = Role.objects.get_or_create(code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลภาค"})
        me = Department.objects.create(code="ME", name_th="เครื่องกล", name_en="Mechanical")
        for department in (self.cn, me):
            UserRole.objects.create(user=self.users[0], role=moderator, department=department)

        roles = admin_dashboard()["roles"]

        self.assertEqual([r["count"] for r in roles if r["label"] == moderator.name_th], [1])

    def test_new_user_counts_by_today_week_month_year_and_all(self):
        def joined(user, *date_parts):
            moment = datetime.datetime(*date_parts, 12, tzinfo=datetime.timezone.utc)
            User.objects.filter(pk=user.pk).update(created_at=moment)

        self.add_users(1)
        joined(self.users[0], 2026, 10, 24)  # วันนี้ (เสาร์)
        joined(self.users[1], 2026, 10, 20)  # สัปดาห์นี้ (เริ่มจันทร์ 19)
        joined(self.users[2], 2026, 10, 2)  # เดือนนี้
        joined(User.objects.get(nickname="Extra0"), 2025, 12, 31)  # ปีก่อน

        dashboard = admin_dashboard(today=datetime.date(2026, 10, 24))

        counts = dashboard["new_users"]
        self.assertEqual(
            (counts["day"], counts["week"], counts["month"], counts["year"]),
            (1, 2, 3, 3),
        )

    def test_all_users_count_goes_up_by_one_per_created_user(self):
        before = admin_dashboard()["new_users"]["all"]

        self.add_users(1)

        self.assertEqual(admin_dashboard()["new_users"]["all"], before + 1)

    def test_all_users_count_does_not_drop_when_the_newest_user_is_deleted(self):
        before = admin_dashboard()["new_users"]["all"]
        newest = User.objects.latest("pk")
        UserRole.objects.filter(user=newest).delete()
        newest.delete()

        dashboard = admin_dashboard()

        self.assertEqual(dashboard["new_users"]["all"], before)
        self.assertEqual(dashboard["totals"]["users"], before)

    def add_users(self, count):
        for i in range(count):
            User.objects.create_user(
                email=f"6610{900000 + i}@student.tu.ac.th",
                password=None,
                nickname=f"Extra{i}",
                department=self.cn,
                pdpa_consent_at=timezone.now(),
            )

    def test_users_page_lists_newest_first_with_role_labels_and_upload_count(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            [
                (user.nickname, [r.role.name_th for r in user.user_roles.all()], user.upload_count)
                for user in dashboard["users_page"]
            ],
            [("User2", ["ผู้ดูแลระบบ"], 0), ("User1", ["นักศึกษา"], 0), ("User0", ["นักศึกษา"], 0)],
        )

    def test_users_are_split_into_pages_of_seven(self):
        self.add_users(6)

        users_page = admin_dashboard(page=2)["users_page"]

        self.assertEqual(users_page.paginator.num_pages, 2)
        self.assertEqual([user.nickname for user in users_page], ["User1", "User0"])

    def test_out_of_range_page_shows_the_last_page(self):
        self.add_users(6)

        users_page = admin_dashboard(page="99")["users_page"]

        self.assertEqual(users_page.number, 2)

    def test_page_numbers_show_six_pages_then_an_ellipsis_and_the_last(self):
        self.add_users(88)  # 91 คน = 13 หน้า

        users_page = admin_dashboard(page=1)["users_page"]

        self.assertEqual(
            [str(n) for n in users_page.elided_range],
            ["1", "2", "3", "4", "5", "6", "…", "13"],
        )

    def test_department_overview_lists_active_departments_with_user_and_batch_counts(self):
        dashboard = admin_dashboard()

        self.assertEqual(
            [(d.code, d.user_count, d.batch_count) for d in dashboard["departments"]],
            [("CN", 3, 2)],
        )

    def test_dashboard_runs_a_fixed_number_of_queries(self):
        with self.assertNumQueries(10):
            dashboard = admin_dashboard()
            for user in dashboard["users_page"]:
                [r.role.name_th for r in user.user_roles.all()]


class ModeratorSelectorTests(ModeratorTestCase):
    def test_department_can_have_many_moderators(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        services.assign_moderator(
            user=self.user_nana, department=self.dept_cn, granted_by=self.admin
        )

        moderators = selectors.moderator_list().filter(department=self.dept_cn)
        self.assertEqual(
            {m.user for m in moderators}, {self.user_momo, self.user_nana}
        )

    def test_is_moderator_of_department_is_scoped_to_assigned_department(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        self.assertTrue(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_cn)
        )
        self.assertFalse(
            selectors.is_moderator_of_department(user=self.user_momo, department=self.dept_me)
        )

    def test_moderator_list_queries_prevent_n_plus_one(self):
        services.assign_moderator(
            user=self.user_momo, department=self.dept_cn, granted_by=self.admin
        )
        services.assign_moderator(
            user=self.user_nana, department=self.dept_ce, granted_by=self.admin
        )
        with self.assertNumQueries(1):
            for m in selectors.moderator_list():
                _ = (m.user.email, m.department.code, m.granted_by.email)
