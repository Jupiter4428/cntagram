from django.urls import reverse

from catalog.models import Batch, BatchCourse, Course

from .base import CatalogTestCase


class Issue98AdminNavigationTests(CatalogTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_delete_confirmation_shows_batch_code_and_cancel_link(self):
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        response = self.client.get(reverse("catalog:batch_delete", args=[batch.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CN21")
        self.assertContains(response, reverse("catalog:batch_list"))
        self.assertContains(response, "ยกเลิก")
        self.assertNotContains(response, 'disabled aria-describedby="batch-delete-warning"')

    def test_delete_confirmation_warns_and_disables_action_for_batch_with_courses(self):
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        BatchCourse.objects.create(batch=batch, course=course)
        response = self.client.get(reverse("catalog:batch_delete", args=[batch.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ไม่สามารถลบรุ่น CN21 ได้")
        self.assertContains(response, 'disabled aria-describedby="batch-delete-warning"')
        self.assertTrue(Batch.objects.filter(pk=batch.pk).exists())

    def test_admin_dashboard_links_to_batches_and_courses(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("catalog:batch_list")}"')
        self.assertContains(response, f'href="{reverse("catalog:course_list")}"')

    def test_admin_sidebar_highlights_batch_and_course_pages(self):
        for url_name in ("catalog:batch_list", "catalog:course_list"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "is-active")
                self.assertContains(response, f'href="{reverse(url_name)}"')
