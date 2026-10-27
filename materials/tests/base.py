"""fixture ที่เทสต์ของ materials ใช้ร่วมกันทั้งชั้น selector, form, service และ view

SearchTestCase สำหรับค้นหา / เปิดอ่านเอกสาร (US-7), UploadTestCase สำหรับอัปโหลด (US-5)
และ ApprovalBaseTestCase สำหรับการอนุมัติ (US-6, US-9)
"""
import os
import shutil
import tempfile
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Role, UserRole
from catalog.models import Batch, BatchCourse, Course, Department

from ..models import DocType, DocTypeRequiredRole, Document, DocumentVersion, ExamPeriod

User = get_user_model()


class SearchTestCase(TestCase):
    """ภาค CN มีรุ่น CN21-CN23 เรียน CN200 ทุกรุ่น และ CN22 มี CN201 ด้วย"""

    @classmethod
    def setUpTestData(cls):
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.uploader = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="correct-horse-battery-staple",
            nickname="Uploader",
            department=cls.cn,
            pdpa_consent_at=timezone.now(),
        )
        cls.summary = DocType.objects.create(
            code="summary", name_th="ชีทสรุป", vault=DocType.Vault.LECTURE
        )
        cls.exam = DocType.objects.create(
            code="exam", name_th="ข้อสอบเก่า", vault=DocType.Vault.EXAM
        )
        cn200 = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        cn201 = Course.objects.create(code="CN201", name_en="Data Structures")
        cls.batches = {
            n: Batch.objects.create(department=cls.cn, number=n) for n in (21, 22, 23)
        }
        cls.cn200 = {
            n: BatchCourse.objects.create(batch=batch, course=cn200)
            for n, batch in cls.batches.items()
        }
        cls.cn201_cn22 = BatchCourse.objects.create(
            batch=cls.batches[22], course=cn201
        )

    @classmethod
    def make_document(cls, batch_course, *, title, doc_type=None, status="published"):
        return Document.objects.create(
            batch_course=batch_course,
            doc_type=doc_type or cls.summary,
            uploader=cls.uploader,
            title=title,
            description="-",
            status=status,
        )

    @classmethod
    def make_department(cls, code="CE", *, is_active=True):
        return Department.objects.create(
            code=code, name_th="วิศวกรรมโยธา", name_en="Civil Engineering", is_active=is_active
        )


PDF_BYTES = b"%PDF-1.4\n% fake sheet\n%%EOF\n"


def pdf_file(content=PDF_BYTES, *, name="cn200-midterm.pdf", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


TEST_MEDIA_ROOT = tempfile.mkdtemp()


def stored_file_count():
    return sum(len(files) for _, _, files in os.walk(TEST_MEDIA_ROOT))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class UploadTestCase(TestCase):
    """ภาค CN มีรุ่น CN21 เรียน CN200 และภาค ME มีรุ่น ME21 เรียน CN200 เช่นกัน"""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_materials", stdout=StringIO())
        cls.summary = DocType.objects.get(code="summary")
        cls.exam = DocType.objects.get(code="exam")
        cls.midterm = ExamPeriod.objects.get(code="midterm")
        cls.cn = Department.objects.create(
            code="CN", name_th="วิศวกรรมคอมพิวเตอร์", name_en="Computer Engineering"
        )
        cls.me = Department.objects.create(
            code="ME", name_th="วิศวกรรมเครื่องกล", name_en="Mechanical Engineering"
        )
        course = Course.objects.create(code="CN200", name_en="Discrete Mathematics")
        cls.cn21 = Batch.objects.create(department=cls.cn, number=21)
        cls.me21 = Batch.objects.create(department=cls.me, number=21)
        cls.cn21_cn200 = BatchCourse.objects.create(batch=cls.cn21, course=course)
        cls.me21_cn200 = BatchCourse.objects.create(batch=cls.me21, course=course)
        cls.student = User.objects.create_user(
            email="6610000000@student.tu.ac.th",
            password="correct-horse-battery-staple",
            nickname="Ton",
            department=cls.cn,
            pdpa_consent_at=timezone.now(),
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


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

        # Approval rules (US-9): sheets need either role, exams need both
        for role in (cls.role_moderator, cls.role_super_admin):
            DocTypeRequiredRole.objects.create(
                doc_type=cls.doc_type_summary, role=role, mode=DocTypeRequiredRole.Mode.ANY
            )
            DocTypeRequiredRole.objects.create(
                doc_type=cls.doc_type_exam, role=role, mode=DocTypeRequiredRole.Mode.ALL
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

    def create_exam_of_batch(self, number):
        batch = Batch.objects.create(department=self.dept_cn, number=number)
        batch_course = BatchCourse.objects.create(batch=batch, course=self.course_cn)
        return self.create_document(batch_course=batch_course, doc_type=self.doc_type_exam)
