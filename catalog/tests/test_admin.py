from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Batch, BatchCourse, Course, Department

User = get_user_model()


class CatalogAdminTests(TestCase):
    """Django admin ของ catalog (TD-3)"""

    @classmethod
    def setUpTestData(cls):
        cls.dept_cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin-password",
            nickname="Admin",
            department=cls.dept_cn,
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_changelist_opens_for_every_catalog_model(self):
        for model in ("department", "batch", "course", "batchcourse", "systemsetting"):
            with self.subTest(model=model):
                response = self.client.get(reverse(f"admin:catalog_{model}_changelist"))
                self.assertEqual(response.status_code, 200)

    def _make_batch_course_in_new_department(self, n):
        department = Department.objects.create(
            code=f"D{n}", name_th=f"ภาค {n}", name_en=f"Department {n}"
        )
        batch = Batch.objects.create(department=department, number=n)
        course = Course.objects.create(code=f"CN{n}00", name_en=f"Course {n}")
        return BatchCourse.objects.create(batch=batch, course=course)

    def test_batch_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            self._make_batch_course_in_new_department(n)

        with self.assertNumQueries(6):
            self.client.get(reverse("admin:catalog_batch_changelist"))

    def test_batchcourse_changelist_has_no_n_plus_1(self):
        for n in range(1, 4):
            self._make_batch_course_in_new_department(n)

        with self.assertNumQueries(6):
            self.client.get(reverse("admin:catalog_batchcourse_changelist"))

    def test_admin_saves_course_code_in_upper_case(self):
        response = self.client.post(
            reverse("admin:catalog_course_add"),
            {"code": "cn101", "name_th": "", "name_en": "Programming"},
        )

        self.assertRedirects(response, reverse("admin:catalog_course_changelist"))
        self.assertTrue(Course.objects.filter(code="CN101").exists())
