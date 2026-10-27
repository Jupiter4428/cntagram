"""fixture ที่เทสต์ของ materials ใช้ร่วมกันทั้งชั้น selector, form, service และ view

SearchTestCase สำหรับค้นหา / เปิดอ่านเอกสาร (US-7) และ UploadTestCase สำหรับอัปโหลด (US-5)
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

from catalog.models import Batch, BatchCourse, Course, Department

from ..models import DocType, Document, ExamPeriod

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
