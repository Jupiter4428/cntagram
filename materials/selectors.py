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
