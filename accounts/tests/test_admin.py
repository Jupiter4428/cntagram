from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Department

from ..models import Role, UserRole

User = get_user_model()


class AccountsAdminTests(TestCase):
    """Django admin ของ accounts (TD-3)"""

    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(
            code="CN",
            name_th="วิศวกรรมคอมพิวเตอร์",
            name_en="Computer Engineering",
        )
        cls.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin-password",
            nickname="Admin",
            department=cls.department,
        )
        cls.student = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="student-password",
            nickname="Student",
            department=cls.department,
            pdpa_consent_at=timezone.now(),
        )
        cls.moderator = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลภาค"}
        )[0]

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist_opens_for_every_accounts_model(self):
        for model in ("user", "role", "userrole"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:accounts_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def test_user_change_page_hides_password_and_shows_student_id_read_only(self):
        response = self.client.get(
            reverse("admin:accounts_user_change", args=[self.student.pk])
        )

        form = response.context["adminform"].form
        self.assertNotIn("password", form.fields)
        self.assertNotContains(response, self.student.password)
        self.assertIn("nickname", form.fields)
        self.assertIn("department", form.fields)
        self.assertNotIn("student_id", form.fields)
        self.assertContains(response, "6610000000")

    def test_user_cannot_be_added_through_admin(self):
        response = self.client.get(reverse("admin:accounts_user_add"))

        self.assertEqual(response.status_code, 403)

    def _make_student_in_new_department(self, n):
        department = Department.objects.create(
            code=f"D{n}", name_th=f"ภาค {n}", name_en=f"Department {n}"
        )
        return User.objects.create_user(
            email=f"66100000{n:02d}@student.tu.ac.th",
            password="student-password",
            nickname=f"Student {n}",
            department=department,
            pdpa_consent_at=timezone.now(),
        )

    def test_user_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            self._make_student_in_new_department(n)

        with self.assertNumQueries(6):
            self.client.get(reverse("admin:accounts_user_changelist"))

    def test_userrole_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            student = self._make_student_in_new_department(n)
            UserRole.objects.create(
                user=student,
                role=self.moderator,
                department=student.department,
                granted_by=self.superuser,
            )

        with self.assertNumQueries(7):
            self.client.get(reverse("admin:accounts_userrole_changelist"))

    def test_admin_rejects_moderator_role_without_department(self):
        response = self.client.post(
            reverse("admin:accounts_userrole_add"),
            {"user": self.student.pk, "role": self.moderator.pk, "department": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("department", response.context["adminform"].form.errors)
        self.assertFalse(UserRole.objects.filter(user=self.student).exists())

    def test_admin_rejects_non_student_email_for_student(self):
        response = self.client.post(
            reverse("admin:accounts_user_change", args=[self.student.pk]),
            {
                "email": "student@gmail.com",
                "nickname": "Student",
                "department": self.department.pk,
                "is_active": "on",
            },
        )

        self.assertIn("email", response.context["adminform"].form.errors)
        self.student.refresh_from_db()
        self.assertEqual(self.student.email, "6610000000@student.tu.ac.th")

    def test_user_change_page_query_count_is_fixed(self):
        with self.assertNumQueries(4):
            self.client.get(reverse("admin:accounts_user_change", args=[self.student.pk]))

    def test_user_cannot_be_deleted_through_admin(self):
        response = self.client.get(
            reverse("admin:accounts_user_delete", args=[self.student.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.student.pk).exists())
