from catalog.models import Batch, BatchCourse

from ..selectors import search_documents
from .base import SearchTestCase


class SearchDocumentsTests(SearchTestCase):
    def test_returns_published_documents_of_the_course_from_every_batch(self):
        expected = {
            self.make_document(self.cn200[n], title=f"CN200 CN{n}").pk
            for n in (21, 22, 23)
        }
        self.make_document(self.cn200[21], title="pending", status="pending")
        self.make_document(self.cn200[22], title="hidden", status="hidden")
        self.make_document(self.cn201_cn22, title="other course")

        result = search_documents(course_code="cn200")

        self.assertEqual({doc.pk for doc in result}, expected)

    def test_department_batch_and_doc_type_filters_combine(self):
        cn22_exam = self.make_document(
            self.cn200[22], title="CN22 exam", doc_type=self.exam
        )
        self.make_document(self.cn200[22], title="CN22 summary")
        self.make_document(self.cn200[21], title="CN21 exam", doc_type=self.exam)

        result = search_documents(
            course_code="CN200",
            department=self.cn,
            batch=self.batches[22],
            doc_type=self.exam,
        )

        self.assertEqual([doc.pk for doc in result], [cn22_exam.pk])

    def test_department_filter_drops_other_departments_with_the_same_course(self):
        ce = self.make_department()
        ce22 = Batch.objects.create(department=ce, number=22)
        ce_cn200 = BatchCourse.objects.create(batch=ce22, course=self.cn200[22].course)
        self.make_document(ce_cn200, title="CE22 exam", doc_type=self.exam)
        self.make_document(self.cn200[22], title="CN22 exam", doc_type=self.exam)

        result = search_documents(course_code="CN200", department=ce)

        self.assertEqual([doc.title for doc in result], ["CE22 exam"])

    def test_result_rows_load_in_a_single_query(self):
        for n in (21, 22, 23, 23):
            self.make_document(self.cn200[n], title=f"CN200 CN{n}")

        with self.assertNumQueries(1):
            for doc in search_documents(course_code="CN200"):
                (
                    doc.batch_course.batch.code,
                    doc.batch_course.course.display_name,
                    doc.doc_type.name_th,
                    doc.uploader.nickname,
                )
