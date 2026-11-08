from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from materials.models import Approval, DocType, DocTypeRequiredRole, Document

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class UserDashboardTemplateTagsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.now = timezone.now()
        cls.dept_cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.dept_me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )
        cls.batch_cn = Batch.objects.create(department=cls.dept_cn, number=24)
        cls.batch_me = Batch.objects.create(department=cls.dept_me, number=24)
        cls.course = Course.objects.create(code="CN101", name_en="Computer Programming")
        cls.bc_cn = BatchCourse.objects.create(batch=cls.batch_cn, course=cls.course)
        cls.bc_me = BatchCourse.objects.create(batch=cls.batch_me, course=cls.course)

        cls.role_student, _ = Role.objects.get_or_create(
            code=Role.STUDENT, defaults={"name_th": "นักศึกษา"}
        )
        cls.role_moderator, _ = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )

        cls.doc_type_summary = DocType.objects.create(
            code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE
        )
        DocTypeRequiredRole.objects.create(
            doc_type=cls.doc_type_summary, role=cls.role_moderator
        )

        cls.student = User.objects.create_user(
            email="6610000010@student.tu.ac.th",
            password="password",
            nickname="Ton",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(user=cls.student, role=cls.role_student)

        cls.other_student = User.objects.create_user(
            email="6610000011@student.tu.ac.th",
            password="password",
            nickname="Other",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )

        cls.moderator = User.objects.create_user(
            email="6610000012@student.tu.ac.th",
            password="password",
            nickname="P'Mo",
            department=cls.dept_cn,
            pdpa_consent_at=cls.now,
        )
        UserRole.objects.create(
            user=cls.moderator, role=cls.role_moderator, department=cls.dept_cn
        )

    def test_student_home_shows_only_own_documents_with_statuses_and_rejection_reason(
        self,
    ):
        # Student's documents (pending, published, rejected, hidden)
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="CN101 Midterm Summary",
            status=Document.Status.PENDING,
        )
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="CN101 Final Summary",
            status=Document.Status.PUBLISHED,
        )
        d_rejected = Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="CN101 Lecture Slides",
            status=Document.Status.REJECTED,
        )
        Approval.objects.create(
            document=d_rejected,
            approver=self.moderator,
            approver_role=self.role_moderator,
            decision=Approval.Decision.REJECTED,
            reason="ผิดวิชาและเนื้อหาไม่ตรงตามหลักสูตร",
        )
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="CN101 Hidden Notes",
            status=Document.Status.HIDDEN,
        )

        # Other student's document (should not be shown)
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.other_student,
            title="Secret Friend Document",
            status=Document.Status.PENDING,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("accounts:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ไฟล์ของฉัน")
        self.assertContains(response, "CN101 Midterm Summary")
        self.assertContains(
            response,
            '<span class="badge bg-warning text-dark">รออนุมัติ</span>',
            html=True,
        )
        self.assertContains(response, "CN101 Final Summary")
        self.assertContains(
            response, '<span class="badge bg-success">เผยแพร่แล้ว</span>', html=True
        )
        self.assertContains(response, "CN101 Lecture Slides")
        self.assertContains(
            response, '<span class="badge bg-danger">ถูกปฏิเสธ</span>', html=True
        )
        self.assertContains(
            response, "เหตุผลที่ถูกปฏิเสธ:</strong> ผิดวิชาและเนื้อหาไม่ตรงตามหลักสูตร"
        )
        self.assertContains(response, "CN101 Hidden Notes")
        self.assertContains(
            response, '<span class="badge bg-secondary">ซ่อนอยู่</span>', html=True
        )
        self.assertNotContains(response, "Secret Friend Document")
        self.assertNotContains(response, "MODERATOR QUEUE")

    def test_moderator_home_shows_pending_approvals_count_for_assigned_department(self):
        # 1 pending doc in CN
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="Pending CN 1",
            status=Document.Status.PENDING,
        )
        # 1 pending doc in ME (not CN)
        Document.objects.create(
            batch_course=self.bc_me,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="Pending ME",
            status=Document.Status.PENDING,
        )

        self.client.force_login(self.moderator)

        # Baseline check with 1 pending in CN
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MODERATOR QUEUE")
        self.assertContains(response, "รออนุมัติ <strong>1</strong> ไฟล์ (ภาค CN)")
        self.assertContains(response, reverse("materials:approval_queue"))

        # Baseline dashboard 8 queries + 3 fixed poll/shoutbox + 1 vault snapshot = 12.
        with self.assertNumQueries(12):
            self.client.get(reverse("accounts:home"))

        # Add 4 more pending documents in CN (total 5)
        for i in range(2, 6):
            Document.objects.create(
                batch_course=self.bc_cn,
                doc_type=self.doc_type_summary,
                uploader=self.student,
                title=f"Pending CN {i}",
                status=Document.Status.PENDING,
            )

        # Query count remains constant with 5 documents (no N+1).
        with self.assertNumQueries(12):
            resp = self.client.get(reverse("accounts:home"))
        self.assertContains(resp, "รออนุมัติ <strong>5</strong> ไฟล์ (ภาค CN)")

    def test_empty_documents_shows_upload_cta(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("accounts:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "คุณยังไม่มีประวัติการอัปโหลดเอกสารในระบบ")
        self.assertContains(response, reverse("materials:upload"))

    def test_dashboard_query_count_remains_constant(self):
        self.client.force_login(self.student)

        # Baseline: 1 document
        Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="Doc 0",
            status=Document.Status.PUBLISHED,
        )
        # Dashboard: 5 queries + poll aggregate, vote existence,
        # shoutbox, vault snapshot = 9.
        with self.assertNumQueries(9):
            self.client.get(reverse("accounts:home"))

        # Add 4 more documents (total 5)
        for i in range(1, 5):
            Document.objects.create(
                batch_course=self.bc_cn,
                doc_type=self.doc_type_summary,
                uploader=self.student,
                title=f"Doc {i}",
                status=Document.Status.PUBLISHED,
            )

        # Same 9 queries regardless of document count (no N+1).
        with self.assertNumQueries(9):
            self.client.get(reverse("accounts:home"))

    def test_home_archive_and_board_index_reflect_published_documents(self):
        doc = Document.objects.create(
            batch_course=self.bc_cn,
            doc_type=self.doc_type_summary,
            uploader=self.student,
            title="Real Lecture Note",
            status=Document.Status.PUBLISHED,
        )
        self.client.force_login(self.student)
        response = self.client.get(reverse("accounts:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CN101 · Real Lecture Note")
        self.assertContains(response, f'{reverse("materials:vault")}?course_code=CN101')
        self.assertContains(
            response, reverse("materials:document_detail", args=[doc.pk])
        )
        self.assertContains(response, "1 ไฟล์")
        self.assertNotContains(response, "ยังไม่มีเอกสารที่เผยแพร่ในคลังขณะนี้")

        # Guest sees login links for the published items
        self.client.logout()
        guest_resp = self.client.get(reverse("accounts:home"))
        self.assertContains(guest_resp, "CN101 · Real Lecture Note")
        self.assertContains(guest_resp, "1 ไฟล์ · สมาชิก")
        self.assertNotContains(
            guest_resp, f'{reverse("materials:vault")}?course_code=CN101'
        )
