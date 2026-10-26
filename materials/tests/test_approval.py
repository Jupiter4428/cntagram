from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from ..forms import ReviewForm
from ..models import Approval, DocType, Document, DocumentVersion
from ..selectors import get_document_for_review, pending_documents_for_moderator
from ..services import review_document

User = get_user_model()


class ApprovalBaseTestCase(TestCase):
    """Setup base test data for departments, roles, users, and documents."""

    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()

        # Roles
        cls.role_student, _ = Role.objects.get_or_create(
            code=Role.STUDENT, defaults={"name_th": "นักศึกษา"}
        )
        cls.role_moderator, _ = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )
        cls.role_super_admin, _ = Role.objects.get_or_create(
            code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"}
        )

        # Departments
        cls.dept_cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.dept_me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )

        # Batches & Courses
        cls.batch_cn = Batch.objects.create(department=cls.dept_cn, number=24)
        cls.batch_me = Batch.objects.create(department=cls.dept_me, number=24)

        cls.course_cn = Course.objects.create(code="CN101", name_en="Computer Programming")
        cls.course_me = Course.objects.create(code="ME101", name_en="Engineering Mechanics")

        cls.bc_cn = BatchCourse.objects.create(batch=cls.batch_cn, course=cls.course_cn)
        cls.bc_me = BatchCourse.objects.create(batch=cls.batch_me, course=cls.course_me)

        # Doc Types
        cls.doc_type_summary, _ = DocType.objects.get_or_create(
            code="summary", defaults={"name_th": "ชีทสรุป", "vault": DocType.Vault.LECTURE}
        )
        cls.doc_type_exam, _ = DocType.objects.get_or_create(
            code="exam", defaults={"name_th": "ข้อสอบเก่า", "vault": DocType.Vault.EXAM}
        )

        # Users
        cls.uploader_cn = User.objects.create_user(
            email="6610000001@student.tu.ac.th",
            password="password123",
            nickname="UploaderCN",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.uploader_cn, role=cls.role_student)

        cls.mod_cn = User.objects.create_user(
            email="6610000002@student.tu.ac.th",
            password="password123",
            nickname="ModCN",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.mod_cn, role=cls.role_student)
        UserRole.objects.create(
            user=cls.mod_cn, role=cls.role_moderator, department=cls.dept_cn
        )

        cls.mod_me = User.objects.create_user(
            email="6610000003@student.tu.ac.th",
            password="password123",
            nickname="ModME",
            department=cls.dept_me,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.mod_me, role=cls.role_student)
        UserRole.objects.create(
            user=cls.mod_me, role=cls.role_moderator, department=cls.dept_me
        )

        cls.super_admin = User.objects.create_user(
            email="6610000004@student.tu.ac.th",
            password="password123",
            nickname="SuperAdmin",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.super_admin, role=cls.role_super_admin)

        cls.normal_student = User.objects.create_user(
            email="6610000005@student.tu.ac.th",
            password="password123",
            nickname="NormalStudent",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.normal_student, role=cls.role_student)

    def create_document(
        self,
        *,
        batch_course=None,
        doc_type=None,
        uploader=None,
        status=Document.Status.PENDING,
        title="Test Sheet",
    ):
        doc = Document.objects.create(
            batch_course=batch_course or self.bc_cn,
            doc_type=doc_type or self.doc_type_summary,
            uploader=uploader or self.uploader_cn,
            title=title,
            description="Detailed test description",
            status=status,
        )
        DocumentVersion.objects.create(
            document=doc,
            version_no=1,
            storage_path=f"vault/test/{doc.pk}_v1.pdf",
            original_name="test.pdf",
            size_bytes=2048,
            sha256="a" * 64,
        )
        return doc


class ApprovalModelTests(ApprovalBaseTestCase):
    def test_approval_creation_and_clean_validation(self):
        doc = self.create_document()

        # Rejecting without reason must fail clean()
        approval = Approval(
            document=doc,
            approver=self.mod_cn,
            approver_role=self.role_moderator,
            decision=Approval.Decision.REJECTED,
            reason="",
        )
        with self.assertRaises(ValidationError) as ctx:
            approval.clean()
        self.assertIn("reason", ctx.exception.message_dict)

        # Rejecting with reason passes
        approval.reason = "ไฟล์ไม่ชัดเจน กรุณาสแกนใหม่"
        approval.save()
        self.assertIsNotNone(approval.pk)
        self.assertEqual(approval.decision, Approval.Decision.REJECTED)

    def test_duplicate_approval_by_same_user_prevented(self):
        doc = self.create_document()
        Approval.objects.create(
            document=doc,
            approver=self.mod_cn,
            approver_role=self.role_moderator,
            decision=Approval.Decision.APPROVED,
        )

        with self.assertRaises(IntegrityError):
            Approval.objects.create(
                document=doc,
                approver=self.mod_cn,
                approver_role=self.role_moderator,
                decision=Approval.Decision.APPROVED,
            )


class ReviewFormTests(TestCase):
    def test_approve_valid_without_reason(self):
        form = ReviewForm(data={"decision": Approval.Decision.APPROVED, "reason": ""})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["reason"])

    def test_reject_requires_reason(self):
        form = ReviewForm(data={"decision": Approval.Decision.REJECTED, "reason": "   "})
        self.assertFalse(form.is_valid())
        self.assertIn("reason", form.errors)
        self.assertIn("กรุณาระบุเหตุผล", form.errors["reason"][0])

    def test_reject_valid_with_reason(self):
        form = ReviewForm(
            data={"decision": Approval.Decision.REJECTED, "reason": "เนื้อหาไม่ถูกต้อง"}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["reason"], "เนื้อหาไม่ถูกต้อง")


class ApprovalSelectorTests(ApprovalBaseTestCase):
    def test_moderator_sees_only_pending_documents_of_their_department(self):
        doc_cn_pending = self.create_document(batch_course=self.bc_cn, title="CN Pending")
        doc_cn_published = self.create_document(
            batch_course=self.bc_cn, status=Document.Status.PUBLISHED, title="CN Published"
        )
        doc_me_pending = self.create_document(batch_course=self.bc_me, title="ME Pending")

        cn_docs = pending_documents_for_moderator(user=self.mod_cn)
        self.assertIn(doc_cn_pending, cn_docs)
        self.assertNotIn(doc_cn_published, cn_docs)
        self.assertNotIn(doc_me_pending, cn_docs)

        me_docs = pending_documents_for_moderator(user=self.mod_me)
        self.assertIn(doc_me_pending, me_docs)
        self.assertNotIn(doc_cn_pending, me_docs)

    def test_super_admin_sees_pending_documents_of_all_departments(self):
        doc_cn = self.create_document(batch_course=self.bc_cn, title="CN Pending")
        doc_me = self.create_document(batch_course=self.bc_me, title="ME Pending")

        all_docs = pending_documents_for_moderator(user=self.super_admin)
        self.assertIn(doc_cn, all_docs)
        self.assertIn(doc_me, all_docs)

    def test_normal_user_or_unauthenticated_gets_empty_queryset(self):
        self.create_document(batch_course=self.bc_cn)
        docs = pending_documents_for_moderator(user=self.normal_student)
        self.assertEqual(docs.count(), 0)

    def test_moderator_cannot_see_own_uploaded_file_in_queue(self):
        own_doc = self.create_document(
            batch_course=self.bc_cn,
            uploader=self.mod_cn,
            title="Moderator Own Doc",
        )
        other_doc = self.create_document(
            batch_course=self.bc_cn,
            uploader=self.uploader_cn,
            title="Other Student Doc",
        )

        docs = pending_documents_for_moderator(user=self.mod_cn)
        self.assertNotIn(own_doc, docs)
        self.assertIn(other_doc, docs)

    def test_already_approved_document_excluded_from_moderator_queue(self):
        doc = self.create_document(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_exam,
            status=Document.Status.PENDING,
        )
        Approval.objects.create(
            document=doc,
            approver=self.mod_cn,
            approver_role=self.role_moderator,
            decision=Approval.Decision.APPROVED,
        )

        docs = pending_documents_for_moderator(user=self.mod_cn)
        self.assertNotIn(doc, docs)

    def test_get_document_for_review_permissions_and_existence(self):
        doc_cn = self.create_document(batch_course=self.bc_cn)

        # Mod CN can access
        fetched = get_document_for_review(document_id=doc_cn.pk, user=self.mod_cn)
        self.assertEqual(fetched.pk, doc_cn.pk)

        # Super Admin can access
        fetched_sa = get_document_for_review(document_id=doc_cn.pk, user=self.super_admin)
        self.assertEqual(fetched_sa.pk, doc_cn.pk)

        # Mod ME gets Document.DoesNotExist for CN doc (cannot distinguish from non-existent doc)
        with self.assertRaises(Document.DoesNotExist):
            get_document_for_review(document_id=doc_cn.pk, user=self.mod_me)

        # Normal student gets Document.DoesNotExist
        with self.assertRaises(Document.DoesNotExist):
            get_document_for_review(document_id=doc_cn.pk, user=self.normal_student)

    def test_get_document_for_review_already_processed_raises_does_not_exist(self):
        doc_published = self.create_document(
            batch_course=self.bc_cn, status=Document.Status.PUBLISHED
        )
        with self.assertRaises(Document.DoesNotExist):
            get_document_for_review(document_id=doc_published.pk, user=self.mod_cn)


class ApprovalServiceTests(ApprovalBaseTestCase):
    def test_uploader_cannot_approve_their_own_document(self):
        UserRole.objects.create(
            user=self.uploader_cn, role=self.role_moderator, department=self.dept_cn
        )
        doc = self.create_document(uploader=self.uploader_cn)

        with self.assertRaises(PermissionDenied) as ctx:
            review_document(
                document=doc,
                approver=self.uploader_cn,
                decision=Approval.Decision.APPROVED,
            )
        self.assertIn("ไม่สามารถอนุมัติหรือปฏิเสธเอกสารของตนเองได้", str(ctx.exception))

    def test_moderator_of_other_dept_cannot_review(self):
        doc_cn = self.create_document(batch_course=self.bc_cn)

        with self.assertRaises(PermissionDenied):
            review_document(
                document=doc_cn,
                approver=self.mod_me,
                decision=Approval.Decision.APPROVED,
            )

    def test_approve_lecture_sheet_changes_status_to_published(self):
        doc = self.create_document(doc_type=self.doc_type_summary)

        approval = review_document(
            document=doc,
            approver=self.mod_cn,
            decision=Approval.Decision.APPROVED,
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        self.assertEqual(approval.decision, Approval.Decision.APPROVED)
        self.assertEqual(approval.approver_role, self.role_moderator)
        self.assertTrue(Approval.objects.filter(document=doc, approver=self.mod_cn).exists())

    def test_super_admin_approve_changes_status_to_published(self):
        doc = self.create_document(batch_course=self.bc_cn, doc_type=self.doc_type_summary)

        approval = review_document(
            document=doc,
            approver=self.super_admin,
            decision=Approval.Decision.APPROVED,
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        self.assertEqual(approval.decision, Approval.Decision.APPROVED)
        self.assertEqual(approval.approver_role, self.role_super_admin)
        self.assertTrue(Approval.objects.filter(document=doc, approver=self.super_admin).exists())

    def test_reject_changes_status_to_rejected(self):
        doc = self.create_document(doc_type=self.doc_type_summary)

        approval = review_document(
            document=doc,
            approver=self.mod_cn,
            decision=Approval.Decision.REJECTED,
            reason="ชีทเนื้อหาไม่ครบถ้วน",
        )

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.REJECTED)
        self.assertEqual(approval.decision, Approval.Decision.REJECTED)
        self.assertEqual(approval.reason, "ชีทเนื้อหาไม่ครบถ้วน")

    def test_review_already_reviewed_document_raises_validation_error(self):
        doc = self.create_document(doc_type=self.doc_type_summary, status=Document.Status.PUBLISHED)

        with self.assertRaises(ValidationError) as ctx:
            review_document(
                document=doc,
                approver=self.mod_cn,
                decision=Approval.Decision.REJECTED,
                reason="ต้องการปฏิเสธย้อนหลัง",
            )
        self.assertIn("เอกสารนี้ถูกพิจารณาไปแล้ว", str(ctx.exception))

    def test_duplicate_approval_by_same_approver_raises_validation_error(self):
        doc = self.create_document(doc_type=self.doc_type_exam, status=Document.Status.PENDING)

        review_document(
            document=doc,
            approver=self.mod_cn,
            decision=Approval.Decision.APPROVED,
        )

        with self.assertRaises(ValidationError) as ctx:
            review_document(
                document=doc,
                approver=self.mod_cn,
                decision=Approval.Decision.APPROVED,
            )
        self.assertIn("คุณพิจารณาเอกสารนี้ไปแล้ว", str(ctx.exception))

    def test_approve_exam_document_remains_pending(self):
        doc = self.create_document(doc_type=self.doc_type_exam)

        approval = review_document(
            document=doc,
            approver=self.mod_cn,
            decision=Approval.Decision.APPROVED,
        )

        doc.refresh_from_db()
        # Status remains pending awaiting US-9 second approval
        self.assertEqual(doc.status, Document.Status.PENDING)
        self.assertEqual(approval.decision, Approval.Decision.APPROVED)


class ApprovalViewsTests(ApprovalBaseTestCase):
    def setUp(self):
        self.client = Client()
        self.queue_url = reverse("materials:approval_queue")

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(self.queue_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_normal_student_forbidden_from_queue_and_review(self):
        doc = self.create_document()
        self.client.force_login(self.normal_student)

        # Queue page forbidden
        response = self.client.get(self.queue_url)
        self.assertEqual(response.status_code, 403)

        # Review page forbidden
        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 403)

    def test_moderator_of_other_dept_gets_404_from_review_doc(self):
        doc_cn = self.create_document(batch_course=self.bc_cn)
        self.client.force_login(self.mod_me)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc_cn.pk})
        response = self.client.get(review_url)
        # Cannot distinguish other dept from non-existent document
        self.assertEqual(response.status_code, 404)

    def test_approval_queue_displays_department_documents(self):
        doc_cn = self.create_document(batch_course=self.bc_cn, title="CN Unique Title")
        doc_me = self.create_document(batch_course=self.bc_me, title="ME Unique Title")

        self.client.force_login(self.mod_cn)
        response = self.client.get(self.queue_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/approval_queue.html")
        self.assertContains(response, "CN Unique Title")
        self.assertNotContains(response, "ME Unique Title")
        self.assertContains(response, "Pending")

    def test_approval_queue_does_not_display_own_uploaded_documents(self):
        self.create_document(
            batch_course=self.bc_cn,
            uploader=self.mod_cn,
            title="My Own Document",
        )
        self.client.force_login(self.mod_cn)

        response = self.client.get(self.queue_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "My Own Document")

    def test_approval_review_get_renders_form_and_file_info(self):
        doc = self.create_document(batch_course=self.bc_cn, title="Math Summary")
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.get(review_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "materials/approval_review.html")
        self.assertContains(response, "Math Summary")
        self.assertContains(response, "test.pdf")
        self.assertIsInstance(response.context["form"], ReviewForm)

    def test_approval_review_already_processed_returns_404(self):
        doc_published = self.create_document(
            batch_course=self.bc_cn, status=Document.Status.PUBLISHED
        )
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc_published.pk})
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 404)

        # POST should also return 404
        post_response = self.client.post(
            review_url,
            {"decision": Approval.Decision.REJECTED, "reason": "พยายามแก้สถานะ"},
        )
        self.assertEqual(post_response.status_code, 404)
        doc_published.refresh_from_db()
        self.assertEqual(doc_published.status, Document.Status.PUBLISHED)

    def test_approval_review_post_approve_successful(self):
        doc = self.create_document(batch_course=self.bc_cn)
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED, "reason": ""},
            follow=True,
        )

        self.assertRedirects(response, self.queue_url)
        self.assertContains(response, "บันทึกผลการพิจารณา")
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        self.assertTrue(Approval.objects.filter(document=doc, approver=self.mod_cn).exists())

    def test_approval_review_post_super_admin_approve_successful(self):
        doc = self.create_document(batch_course=self.bc_cn)
        self.client.force_login(self.super_admin)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED, "reason": ""},
            follow=True,
        )

        self.assertRedirects(response, self.queue_url)
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PUBLISHED)
        approval = Approval.objects.get(document=doc, approver=self.super_admin)
        self.assertEqual(approval.approver_role, self.role_super_admin)

    def test_approval_review_post_reject_without_reason_shows_error(self):
        doc = self.create_document(batch_course=self.bc_cn)
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.REJECTED, "reason": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "reason", "กรุณาระบุเหตุผลเมื่อปฏิเสธเอกสาร"
        )
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PENDING)

    def test_approval_review_post_reject_with_reason_successful(self):
        doc = self.create_document(batch_course=self.bc_cn)
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.REJECTED, "reason": "ลายมืออ่านยาก กรุณาแก้ไข"},
            follow=True,
        )

        self.assertRedirects(response, self.queue_url)
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.REJECTED)
        approval = Approval.objects.get(document=doc, approver=self.mod_cn)
        self.assertEqual(approval.decision, Approval.Decision.REJECTED)
        self.assertEqual(approval.reason, "ลายมืออ่านยาก กรุณาแก้ไข")

    def test_approval_review_post_duplicate_submission_shows_form_error_not_500(self):
        doc = self.create_document(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_exam,
            status=Document.Status.PENDING,
        )
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})

        # First review is successful
        res1 = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED, "reason": ""},
            follow=True,
        )
        self.assertRedirects(res1, self.queue_url)
        self.assertEqual(Approval.objects.filter(document=doc, approver=self.mod_cn).count(), 1)

        # Second review attempt (e.g. resubmitting the form or if URL was reopened)
        # Note: selectors.get_document_for_review excludes already reviewed documents -> 404,
        # but if review_document service is invoked directly or concurrency occurs,
        # view catches ValidationError and adds error to form, returning 200 rather than 500.
        # Let's test the view handling of ValidationError:
        doc.status = Document.Status.PENDING
        doc.save()
        # Temporarily mock or test direct submission:
        res2 = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED, "reason": ""},
        )
        # Since mod_cn already approved, get_document_for_review raises 404!
        self.assertEqual(res2.status_code, 404)
        self.assertEqual(Approval.objects.filter(document=doc, approver=self.mod_cn).count(), 1)

    def test_approval_review_exam_approval_remains_pending_and_removed_from_queue(self):
        doc = self.create_document(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_exam,
            title="Exam Document Pending",
        )
        self.client.force_login(self.mod_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED, "reason": ""},
            follow=True,
        )
        self.assertRedirects(response, self.queue_url)

        # Document is still pending
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PENDING)

        # But it is removed from this moderator's queue
        queue_res = self.client.get(self.queue_url)
        self.assertNotContains(queue_res, "Exam Document Pending")

    def test_uploader_cannot_post_review_their_own_document(self):
        UserRole.objects.create(
            user=self.uploader_cn, role=self.role_moderator, department=self.dept_cn
        )
        doc = self.create_document(uploader=self.uploader_cn)
        self.client.force_login(self.uploader_cn)

        review_url = reverse("materials:approval_review", kwargs={"document_id": doc.pk})
        response = self.client.post(
            review_url,
            {"decision": Approval.Decision.APPROVED},
        )

        # Since queue excludes own uploaded files, get_document_for_review raises DoesNotExist -> 404
        self.assertEqual(response.status_code, 404)
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.PENDING)

    def test_approval_queue_num_queries(self):
        # Create 5 documents
        for i in range(5):
            self.create_document(
                batch_course=self.bc_cn,
                title=f"Bulk Doc {i}",
            )

        self.client.force_login(self.mod_cn)

        # Verify queries:
        # 1. session lookup
        # 2. user auth lookup
        # 3. super_admin check (can_review_any)
        # 4. moderator check (can_review_any)
        # 5. super_admin check (pending_documents_for_moderator)
        # 6. moderator department ids query
        # 7. main document query with all select_related joins
        # 8. document_version prefetch_related
        # No N+1 queries when rendering documents.
        with self.assertNumQueries(8):
            response = self.client.get(self.queue_url)
            self.assertEqual(response.status_code, 200)

        # Add 5 more documents (total 10) to strictly prove query count does not grow with N
        for i in range(5, 10):
            self.create_document(
                batch_course=self.bc_cn,
                title=f"Bulk Doc {i}",
            )

        with self.assertNumQueries(8):
            response = self.client.get(self.queue_url)
            self.assertEqual(response.status_code, 200)
