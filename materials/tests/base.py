"""fixture ที่เทสต์อัปโหลด (US-5) ใช้ร่วมกันทั้งชั้น service และ view"""
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

from ..models import DocType, ExamPeriod

User = get_user_model()

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
