from catalog import selectors
from catalog.models import Batch, BatchCourse, Course

from .base import CatalogTestCase


class BatchHasCoursesTests(CatalogTestCase):
    def test_empty_batch_has_no_courses(self):
        """รุ่นว่างไม่มีวิชาที่ผูกอยู่"""
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        self.assertFalse(selectors.batch_has_courses(batch=batch))

    def test_batch_with_course_returns_true(self):
        """รุ่นที่ผูกวิชาแล้วต้องตรวจพบวิชา"""
        batch = Batch.objects.create(department=self.dept_cn, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        BatchCourse.objects.create(batch=batch, course=course)
        self.assertTrue(selectors.batch_has_courses(batch=batch))
