
"""การอ่านข้อมูลของ materials ตาม ADR 0002"""
from django.db.models import QuerySet

from catalog.models import Batch, BatchCourse


def upload_batches(*, department) -> QuerySet[Batch]:
    """รุ่นที่ผู้ใช้อัปโหลดเข้าได้ = รุ่นในภาคของตัวเอง เรียงตามเลขรุ่น"""
    return Batch.objects.filter(department=department).order_by("number")


def upload_batch_courses(*, batch) -> QuerySet[BatchCourse]:
    """วิชาในรุ่นสำหรับ dropdown ต่อเนื่อง (รุ่น → วิชา)

    BatchCourseManager select_related course ให้อยู่แล้ว จึงไม่มี N+1
    """
    return BatchCourse.objects.filter(batch=batch).order_by("course__code")

"""การอ่านข้อมูลของ materials (ค้นหา / เปิดอ่านเอกสาร) ตาม ADR 0002"""
from django.db.models import Q

from .models import Document


def published_documents():
    """เอกสารที่ผู้ใช้ทั่วไปเห็นได้ (เฉพาะ published) พร้อมข้อมูลที่หน้าเว็บต้องใช้ กัน N+1"""
    return Document.objects.filter(status=Document.Status.PUBLISHED).select_related(
        "batch_course__batch__department",
        "batch_course__course",
        "doc_type",
        "uploader",
    )


def search_documents(*, course_code, department=None, batch=None, doc_type=None):
    """เอกสาร published ของรหัสวิชานี้จากทุกรุ่น กรองเพิ่มด้วย ภาค/รุ่น/ประเภท ได้

    เทียบรหัสแบบตรงตัว (Course.code เก็บเป็นตัวพิมพ์ใหญ่) จึงใช้ UQ index ของ course.code ได้
    รหัสรุ่นไม่ได้เก็บใน DB จึงกรองรุ่นผ่าน batch_course__batch
    """
    conditions = Q(batch_course__course__code=course_code.strip().upper())
    if department is not None:
        conditions &= Q(batch_course__batch__department=department)
    if batch is not None:
        conditions &= Q(batch_course__batch=batch)
    if doc_type is not None:
        conditions &= Q(doc_type=doc_type)
    return (
        published_documents()
        .filter(conditions)
        .order_by(
            "batch_course__batch__department__code",
            "batch_course__batch__number",
            "-created_at",
        )
    )
