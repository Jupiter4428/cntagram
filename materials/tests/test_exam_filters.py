from django.test import override_settings
from django.urls import reverse

from ..forms import SearchForm
from ..models import ExamDetail, ExamPeriod
from ..selectors import search_documents
from .base import SearchTestCase


class ExamSearchFilterTests(SearchTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.midterm = ExamPeriod.objects.create(code="midterm", name_th="กลางภาค")
        cls.final = ExamPeriod.objects.create(code="final", name_th="ปลายภาค")
        cls.exam_mid = cls.make_document(
            cls.cn200[21], title="mid 2566", doc_type=cls.exam
        )
        cls.exam_final = cls.make_document(
            cls.cn200[22], title="final 2567", doc_type=cls.exam
        )
        cls.exam_pending = cls.make_document(
            cls.cn200[23], title="pending", doc_type=cls.exam, status="pending"
        )
        cls.sheet = cls.make_document(cls.cn200[22], title="summary")
        ExamDetail.objects.create(
            document=cls.exam_mid, exam_period=cls.midterm, exam_year_be=2566
        )
        ExamDetail.objects.create(
            document=cls.exam_final, exam_period=cls.final, exam_year_be=2567
        )
        ExamDetail.objects.create(
            document=cls.exam_pending, exam_period=cls.final, exam_year_be=2567
        )

    def test_filter_by_period_without_doc_type_excludes_summaries(self):
        self.assertEqual(
            list(search_documents(course_code="CN200", exam_period=self.final)),
            [self.exam_final],
        )

    def test_filter_by_year(self):
        self.assertEqual(
            list(search_documents(course_code="CN200", exam_year_be=2566)),
            [self.exam_mid],
        )

    def test_filters_combine_with_existing_type_and_batch(self):
        result = search_documents(
            course_code="CN200",
            department=self.cn,
            batch=self.batches[22],
            doc_type=self.exam,
            exam_period=self.final,
            exam_year_be=2567,
        )
        self.assertEqual(list(result), [self.exam_final])

    def test_pending_exam_never_appears(self):
        self.assertEqual(
            list(
                search_documents(
                    course_code="CN200", exam_period=self.final, exam_year_be=2567
                )
            ),
            [self.exam_final],
        )

    def test_year_outside_range_has_thai_error(self):
        for year in (1999, 2701):
            with self.subTest(year=year):
                form = SearchForm({"course_code": "CN200", "exam_year_be": year})
                self.assertFalse(form.is_valid())
                self.assertIn("ปีต้องอยู่ในช่วง พ.ศ. 2500–2700", str(form.errors))

    def test_search_uses_one_query_for_many_results(self):
        with self.assertNumQueries(1):
            for doc in search_documents(course_code="CN200", exam_period=self.final):
                (doc.title, doc.doc_type.code, doc.batch_course.course.code)

    def test_search_page_renders_filters_and_errors(self):
        self.client.force_login(self.uploader)
        response = self.client.get(
            reverse("materials:vault"), {"course_code": "CN200", "exam_year_be": "1999"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ปีต้องอยู่ในช่วง พ.ศ. 2500–2700")
        response = self.client.get(
            reverse("materials:vault"),
            {"course_code": "CN200", "exam_period": self.final.pk},
        )
        self.assertContains(response, "final 2567")
        self.assertEqual(
            [d.pk for d in response.context["documents"]], [self.exam_final.pk]
        )
