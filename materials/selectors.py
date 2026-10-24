"""การอ่านข้อมูลของ materials ตาม ADR 0002"""
import datetime

from django.db.models import Count, DateField
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import DocumentVersion


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
