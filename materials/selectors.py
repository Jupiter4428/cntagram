"""การอ่านข้อมูลของ materials (ค้นหา / เปิดอ่านเอกสาร / สถิติอัปโหลด) ตาม ADR 0002"""
import datetime

from django.db.models import Count, DateField, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Document, DocumentVersion


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


def uploaded_file_count() -> int:
    """จำนวนไฟล์ที่อัปโหลดเข้าระบบทั้งหมด นับทุกเวอร์ชัน (ใช้ในหน้า Dashboard ของ Super Admin)"""
    return DocumentVersion.objects.count()


def monthly_uploads(*, today=None, months=6) -> list[dict]:
    """ไฟล์ที่อัปโหลดต่อเดือน (นับทุกเวอร์ชัน) ย้อนหลัง `months` เดือนรวมเดือนนี้ เดือนที่ไม่มีเป็น 0

    `percent` เทียบกับเดือนที่มากที่สุด ใช้เป็นความสูงแท่งกราฟ
    """
    today = today or timezone.localdate()
    month_starts = []
    year, month = today.year, today.month
    for _ in range(months):
        month_starts.insert(0, datetime.date(year, month, 1))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    counts = dict(
        DocumentVersion.objects.filter(uploaded_at__date__gte=month_starts[0])
        .annotate(month=TruncMonth("uploaded_at", output_field=DateField()))
        .values("month")
        .annotate(count=Count("pk"))
        .values_list("month", "count")
    )
    peak = max(counts.values(), default=0)
    return [
        {
            "month": start,
            "count": counts.get(start, 0),
            "percent": round(counts.get(start, 0) * 100 / peak) if peak else 0,
        }
        for start in month_starts
    ]
