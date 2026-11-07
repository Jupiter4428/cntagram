from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from accounts.models import Role
from catalog.models import Batch, BatchCourse

from ..models import Approval, DocType, Document
from ..selectors import (
    moderator_pending_summary,
    pending_documents_without_rules,
    pending_documents_without_rules_summary,
    search_documents,
    user_documents,
)
from .base import ApprovalBaseTestCase, SearchTestCase

User = get_user_model()


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


class UserDocumentsTests(SearchTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email="6610000099@student.tu.ac.th",
            password="password",
            nickname="Other",
            department=self.cn,
            pdpa_consent_at=timezone.now(),
        )

    def test_returns_only_documents_uploaded_by_given_user(self):
        doc1 = self.make_document(
            self.cn200[21], title="My Doc 1", uploader=self.uploader
        )
        doc2 = self.make_document(
            self.cn200[22], title="My Doc 2", uploader=self.uploader
        )
        self.make_document(self.cn200[21], title="Other Doc", uploader=self.other_user)

        docs = user_documents(user=self.uploader)

        self.assertEqual(list(docs), [doc2, doc1])  # Ordered by -created_at

    def test_returns_documents_of_all_statuses(self):
        d_pending = self.make_document(
            self.cn200[21], title="Pending", status=Document.Status.PENDING
        )
        d_published = self.make_document(
            self.cn200[21], title="Published", status=Document.Status.PUBLISHED
        )
        d_rejected = self.make_document(
            self.cn200[21], title="Rejected", status=Document.Status.REJECTED
        )
        d_hidden = self.make_document(
            self.cn200[21], title="Hidden", status=Document.Status.HIDDEN
        )

        docs = list(user_documents(user=self.uploader))

        self.assertEqual(len(docs), 4)
        self.assertIn(d_pending, docs)
        self.assertIn(d_published, docs)
        self.assertIn(d_rejected, docs)
        self.assertIn(d_hidden, docs)

    def test_annotates_latest_rejection_reason_for_rejected_documents(self):
        rejected_doc = self.make_document(
            self.cn200[21], title="Rejected Doc", status=Document.Status.REJECTED
        )
        published_doc = self.make_document(
            self.cn200[22], title="Published Doc", status=Document.Status.PUBLISHED
        )

        mod_role = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )[0]
        Approval.objects.create(
            document=rejected_doc,
            approver=self.other_user,
            approver_role=mod_role,
            decision=Approval.Decision.REJECTED,
            reason="ไฟล์ผิดวิชาและเนื้อหาไม่ชัดเจน",
        )

        docs = {doc.pk: doc for doc in user_documents(user=self.uploader)}

        self.assertEqual(
            docs[rejected_doc.pk].rejection_reason, "ไฟล์ผิดวิชาและเนื้อหาไม่ชัดเจน"
        )
        self.assertIsNone(docs[published_doc.pk].rejection_reason)

    def test_returns_empty_queryset_for_anonymous_or_none(self):
        self.assertEqual(list(user_documents(user=None)), [])
        self.assertEqual(list(user_documents(user=AnonymousUser())), [])

    def test_loads_relations_without_n_plus_one(self):
        for i in range(5):
            self.make_document(self.cn200[21], title=f"Doc {i}", uploader=self.uploader)

        # 1 query for documents + rejection_reason subquery
        with self.assertNumQueries(1):
            for doc in user_documents(user=self.uploader):
                _ = (
                    doc.batch_course.batch.department.code,
                    doc.batch_course.course.code,
                    doc.doc_type.name_th,
                    doc.rejection_reason,
                )


class ModeratorPendingSummaryTests(ApprovalBaseTestCase):
    def setUp(self):
        super().setUp()
        # Pending doc in CN uploaded by student CN
        self.doc_cn_pending = Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.uploader_cn,
            title="CN Pending Doc",
            status=Document.Status.PENDING,
        )
        # Pending doc in ME uploaded by student ME
        self.uploader_me = User.objects.create_user(
            email="6610000088@student.tu.ac.th",
            password="password",
            nickname="UploaderME",
            department=self.dept_me,
            pdpa_consent_at=self.now,
        )
        self.doc_me_pending = Document.objects.create(
            batch_course=self.bc_me,
            doc_type=self.doc_type_summary,
            uploader=self.uploader_me,
            title="ME Pending Doc",
            status=Document.Status.PENDING,
        )

    def test_returns_none_for_student_or_anonymous(self):
        self.assertIsNone(moderator_pending_summary(user=self.uploader_cn))
        self.assertIsNone(moderator_pending_summary(user=None))
        self.assertIsNone(moderator_pending_summary(user=AnonymousUser()))

    def test_counts_only_pending_for_moderator_department_excluding_own_uploads(self):
        # Mod CN's own upload in CN (should NOT be counted in pending for self)
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.mod_cn,
            title="Mod's Own Upload",
            status=Document.Status.PENDING,
        )

        summary = moderator_pending_summary(user=self.mod_cn)

        self.assertIsNotNone(summary)
        self.assertEqual(summary["count"], 1)  # Only doc_cn_pending
        self.assertEqual(summary["department_codes"], ["CN"])


class PendingDocumentsWithoutRulesTests(ApprovalBaseTestCase):
    def test_summary_returns_zero_when_no_pending_documents_lack_rules(self):
        summary = pending_documents_without_rules_summary()
        self.assertEqual(summary["count"], 0)
        self.assertEqual(summary["doc_types"], [])

    def test_summary_counts_pending_documents_whose_doc_type_has_no_rules(self):
        custom_type = DocType.objects.create(
            code="custom_note", name_th="โน้ตสรุปพิเศษ", vault=DocType.Vault.LECTURE
        )
        doc = Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=custom_type,
            uploader=self.uploader_cn,
            title="Custom Doc",
            status=Document.Status.PENDING,
        )
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=custom_type,
            uploader=self.uploader_cn,
            title="Published Custom Doc",
            status=Document.Status.PUBLISHED,
        )

        summary = pending_documents_without_rules_summary()
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["doc_types"], ["โน้ตสรุปพิเศษ"])
        self.assertEqual(list(pending_documents_without_rules()), [doc])
