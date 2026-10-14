from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Batch, BatchCourse, Course, Department
from .selectors import batch_course_list, batch_list
from .services import (
    add_course_to_batch,
    create_batch,
    delete_batch,
    remove_course_from_batch,
)


class CatalogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.ce = Department.objects.create(
            code="CE", name_th="วิศวกรรมโยธา", name_en="Civil Engineering"
        )


class CreateBatchTests(CatalogTestCase):
    def test_batch_code_is_department_code_plus_number(self):
        batch = create_batch(department=self.cn, number=21)
        self.assertEqual(batch.code, "CN21")

    def test_duplicate_batch_is_rejected(self):
        create_batch(department=self.cn, number=21)
        with self.assertRaisesMessage(ValidationError, "รุ่น CN21 มีอยู่แล้ว"):
            create_batch(department=self.cn, number=21)
        self.assertEqual(Batch.objects.count(), 1)

    def test_same_number_in_other_department_is_allowed(self):
        create_batch(department=self.cn, number=21)
        batch = create_batch(department=self.ce, number=21)
        self.assertEqual(batch.code, "CE21")

    def test_number_below_one_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_batch(department=self.cn, number=0)
        self.assertFalse(Batch.objects.exists())


class AddCourseToBatchTests(CatalogTestCase):
    def setUp(self):
        self.cn21 = create_batch(department=self.cn, number=21)
        self.cn22 = create_batch(department=self.cn, number=22)

    def test_same_course_in_many_batches_is_stored_once(self):
        first = add_course_to_batch(
            batch=self.cn21, code="CN200", name_en="Discrete Mathematics"
        )
        second = add_course_to_batch(batch=self.cn22, code="cn200 ")

        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(first.course_id, second.course_id)
        self.assertEqual(BatchCourse.objects.count(), 2)

    def test_existing_course_name_is_not_overwritten(self):
        add_course_to_batch(batch=self.cn21, code="CN200", name_en="Discrete Mathematics")
        add_course_to_batch(batch=self.cn22, code="CN200", name_en="Something else")
        self.assertEqual(Course.objects.get().name_en, "Discrete Mathematics")

    def test_duplicate_course_in_same_batch_is_rejected(self):
        add_course_to_batch(batch=self.cn21, code="CN200", name_en="Discrete Mathematics")
        with self.assertRaisesMessage(ValidationError, "วิชา CN200 อยู่ในรุ่น CN21 แล้ว"):
            add_course_to_batch(batch=self.cn21, code="CN200")
        self.assertEqual(BatchCourse.objects.count(), 1)

    def test_new_course_requires_english_name(self):
        with self.assertRaises(ValidationError):
            add_course_to_batch(batch=self.cn21, code="CN999")
        self.assertFalse(Course.objects.exists())

    def test_blank_code_is_rejected(self):
        with self.assertRaises(ValidationError):
            add_course_to_batch(batch=self.cn21, code="  ", name_en="X")


class DeleteBatchTests(CatalogTestCase):
    def test_batch_with_courses_cannot_be_deleted(self):
        batch = create_batch(department=self.cn, number=21)
        add_course_to_batch(batch=batch, code="CN200", name_en="Discrete Mathematics")

        with self.assertRaisesMessage(ValidationError, "ลบรุ่น CN21 ไม่ได้"):
            delete_batch(batch=batch)
        self.assertTrue(Batch.objects.filter(pk=batch.pk).exists())

    def test_empty_batch_can_be_deleted(self):
        batch = create_batch(department=self.cn, number=21)
        delete_batch(batch=batch)
        self.assertFalse(Batch.objects.exists())

    def test_batch_can_be_deleted_after_removing_its_courses(self):
        batch = create_batch(department=self.cn, number=21)
        batch_course = add_course_to_batch(
            batch=batch, code="CN200", name_en="Discrete Mathematics"
        )
        remove_course_from_batch(batch_course=batch_course)
        delete_batch(batch=batch)
        self.assertFalse(Batch.objects.exists())


class RemoveCourseFromBatchTests(CatalogTestCase):
    def test_course_stays_after_removing_from_batch(self):
        batch = create_batch(department=self.cn, number=21)
        batch_course = add_course_to_batch(
            batch=batch, code="CN200", name_en="Discrete Mathematics"
        )
        remove_course_from_batch(batch_course=batch_course)

        self.assertFalse(BatchCourse.objects.exists())
        self.assertTrue(Course.objects.filter(code="CN200").exists())


class SelectorTests(CatalogTestCase):
    def setUp(self):
        self.cn21 = create_batch(department=self.cn, number=21)
        self.cn22 = create_batch(department=self.cn, number=22)
        create_batch(department=self.ce, number=21)
        add_course_to_batch(batch=self.cn21, code="CN201", name_en="Data Structures")
        add_course_to_batch(batch=self.cn21, code="CN101", name_en="Programming")

    def test_batch_list_counts_courses_in_one_query(self):
        with self.assertNumQueries(1):
            rows = [(b.code, b.course_count) for b in batch_list(department=self.cn)]
        self.assertEqual(rows, [("CN21", 2), ("CN22", 0)])

    def test_batch_course_list_is_sorted_without_extra_queries(self):
        with self.assertNumQueries(1):
            codes = [bc.course.code for bc in batch_course_list(batch=self.cn21)]
        self.assertEqual(codes, ["CN101", "CN201"])


class SeedCatalogCommandTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_catalog", stdout=StringIO())
        counts = (Batch.objects.count(), Course.objects.count(), BatchCourse.objects.count())
        call_command("seed_catalog", stdout=StringIO())

        self.assertEqual(
            (Batch.objects.count(), Course.objects.count(), BatchCourse.objects.count()),
            counts,
        )
        self.assertEqual(counts, (5, 4, 20))
        self.assertEqual(
            sorted(b.code for b in Batch.objects.all()),
            ["CN21", "CN22", "CN23", "CN24", "CN25"],
        )


class InputNormalizationTests(CatalogTestCase):
    def test_new_course_with_lowercase_code_is_normalized(self):
        cn21 = create_batch(department=self.cn, number=21)
        batch_course = add_course_to_batch(batch=cn21, code=" cn300", name_en="X")
        self.assertEqual(batch_course.course.code, "CN300")

    def test_non_integer_number_is_rejected(self):
        with self.assertRaises(ValidationError):
            create_batch(department=self.cn, number="21")


class BatchViewTests(CatalogTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="pw", nickname="admin", department=cls.cn
        )

    def test_guest_is_redirected(self):
        response = self.client.get(reverse("catalog:batch_manage", args=["CN"]))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_add_batch(self):
        self.client.force_login(self.admin)
        url = reverse("catalog:batch_manage", args=["cn"])
        response = self.client.post(url, {"number": 21}, follow=True)
        self.assertContains(response, "เพิ่มรุ่น CN21 แล้ว")
        response = self.client.post(url, {"number": 21})
        self.assertContains(response, "รุ่น CN21 มีอยู่แล้ว")

    def test_admin_cannot_delete_batch_with_courses(self):
        self.client.force_login(self.admin)
        batch = create_batch(department=self.cn, number=21)
        add_course_to_batch(batch=batch, code="CN200", name_en="Discrete Mathematics")
        response = self.client.post(
            reverse("catalog:batch_delete", args=[batch.pk]), follow=True
        )
        self.assertContains(response, "ลบรุ่น CN21 ไม่ได้")
        self.assertTrue(Batch.objects.filter(pk=batch.pk).exists())

    def test_admin_can_add_and_remove_course(self):
        self.client.force_login(self.admin)
        batch = create_batch(department=self.cn, number=21)
        url = reverse("catalog:batch_course_manage", args=[batch.pk])
        response = self.client.post(url, {"code": "CN999"})
        self.assertContains(response, "กรุณากรอกชื่อวิชาภาษาอังกฤษ")
        self.client.post(url, {"code": "CN200", "name_en": "Discrete Mathematics"})
        batch_course = BatchCourse.objects.get()
        self.client.post(reverse("catalog:batch_course_remove", args=[batch_course.pk]))
        self.assertFalse(BatchCourse.objects.exists())
