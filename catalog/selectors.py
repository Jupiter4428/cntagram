"""การอ่านข้อมูลของ catalog (รุ่น / วิชาในรุ่น) ตาม ADR 0002"""
from django.db.models import Count, QuerySet

from .models import Batch, BatchCourse


def batch_list(*, department) -> QuerySet[Batch]:
    """รุ่นทั้งหมดของภาค เรียงตามเลขรุ่น พร้อม course_count (จำนวนวิชาในรุ่น)

    ใช้ course_count เช็กก่อนแสดงปุ่มลบได้โดยไม่ต้อง query ทีละรุ่น
    """
    return (
        Batch.objects.filter(department=department)
        .annotate(course_count=Count("batch_courses"))
        .order_by("number")
    )


def batch_course_list(*, batch) -> QuerySet[BatchCourse]:
    """วิชาในรุ่น เรียงตามรหัสวิชา โหลด course มาด้วยเพื่อกัน N+1"""
    return (
        BatchCourse.objects.filter(batch=batch)
        .select_related("course")
        .order_by("course__code")
    )
