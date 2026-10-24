import datetime

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department
from accounts.selectors import admin_dashboard
from materials.models import Document, DocType, DocumentVersion
from materials.selectors import monthly_uploads, uploaded_file_count

User = get_user_model()


class BatchCourseWithDocumentsTests(TestCase):
    def test_cannot_remove_course_that_has_documents(self):
        """ถอดวิชาออกจากรุ่นไม่ได้ ถ้ามีเอกสารอัปโหลดอยู่ในวิชานั้นแล้ว (US-4)"""
        dept = Department.objects.create(code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering")
        admin = User.objects.create_user(
            email="6810610002@student.tu.ac.th",
            password="password123",
            nickname="admin_test",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        role, _ = Role.objects.get_or_create(code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"})
        UserRole.objects.create(user=admin, role=role)
        batch = Batch.objects.create(department=dept, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        batch_course = BatchCourse.objects.create(batch=batch, course=course)
        doc_type = DocType.objects.create(code="summary", name_th="สรุป", vault=DocType.Vault.LECTURE)
        Document.objects.create(
            batch_course=batch_course, doc_type=doc_type, uploader=admin, title="สรุปบทที่ 1", description="-"
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse("catalog:batch_course_remove", args=[batch.pk, batch_course.pk]),
            follow=True,
        )

        self.assertTrue(BatchCourse.objects.filter(pk=batch_course.pk).exists())
        self.assertContains(response, "ถอดวิชา CN200 ไม่ได้ เพราะมีเอกสารอัปโหลดอยู่ในวิชานี้แล้ว")


class UploadStatsTests(TestCase):
    """ตัวเลขการอัปโหลดที่หน้า Dashboard ของ Super Admin ใช้"""

    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering")
        cls.uploader = User.objects.create_user(
            email="6810610003@student.tu.ac.th",
            password=None,
            nickname="Ton",
            department=dept,
            pdpa_consent_at=timezone.now(),
        )
        batch = Batch.objects.create(department=dept, number=21)
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        cls.batch_course = BatchCourse.objects.create(batch=batch, course=course)
        cls.doc_type = DocType.objects.create(code="summary", name_th="สรุป", vault=DocType.Vault.LECTURE)

    def upload(self, *, versions=1):
        document = Document.objects.create(
            batch_course=self.batch_course,
            doc_type=self.doc_type,
            uploader=self.uploader,
            title="สรุป CN200",
            description="-",
        )
        for i in range(versions):
            document.add_version(
                storage_path=f"vault/CN/21/CN200/summary/{document.pk}-{i}.pdf",
                original_name="cn200.pdf",
                size_bytes=100,
                sha256=f"{i:064x}",
            )
        return document

    def uploaded_in(self, year, month):
        version = self.upload().current_version
        moment = datetime.datetime(year, month, 15, tzinfo=datetime.timezone.utc)
        DocumentVersion.objects.filter(pk=version.pk).update(uploaded_at=moment)

    def test_count_is_zero_before_any_upload(self):
        self.assertEqual(uploaded_file_count(), 0)

    def test_count_includes_every_uploaded_version(self):
        self.upload(versions=2)

        with self.assertNumQueries(1):
            count = uploaded_file_count()

        self.assertEqual(count, 2)

    def test_template_tag_renders_the_count(self):
        self.upload()
        template = Template("{% load materials_stats %}{% uploaded_file_count %}")

        rendered = template.render(Context())

        self.assertEqual(rendered, "1")

    def test_monthly_uploads_cover_the_last_six_months_including_empty_ones(self):
        self.uploaded_in(2026, 10)
        self.uploaded_in(2026, 10)
        self.uploaded_in(2026, 8)
        self.uploaded_in(2026, 3)  # เก่ากว่า 6 เดือน ไม่นับ

        rows = monthly_uploads(today=datetime.date(2026, 10, 24))

        self.assertEqual(
            [(row["month"], row["count"], row["percent"]) for row in rows],
            [
                (datetime.date(2026, 5, 1), 0, 0),
                (datetime.date(2026, 6, 1), 0, 0),
                (datetime.date(2026, 7, 1), 0, 0),
                (datetime.date(2026, 8, 1), 1, 50),
                (datetime.date(2026, 9, 1), 0, 0),
                (datetime.date(2026, 10, 1), 2, 100),
            ],
        )

    def test_monthly_uploads_tag_gives_six_months(self):
        template = Template("{% load materials_stats %}{% monthly_uploads as rows %}{{ rows|length }}")

        rendered = template.render(Context())

        self.assertEqual(rendered, "6")

    def test_admin_users_page_counts_documents_each_user_uploaded(self):
        self.upload(versions=2)

        users_page = admin_dashboard()["users_page"]

        self.assertEqual([(user.nickname, user.upload_count) for user in users_page], [("Ton", 1)])
