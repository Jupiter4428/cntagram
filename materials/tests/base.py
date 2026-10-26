"""fixture ที่เทสต์ค้นหา / เปิดอ่านเอกสาร (US-7) ใช้ร่วมกันทั้งชั้น selector, form และ view"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Batch, BatchCourse, Course, Department

from ..models import DocType, Document

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
