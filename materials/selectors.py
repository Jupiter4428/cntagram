"""การอ่านข้อมูลของ materials ตาม ADR 0002"""
import datetime

from django.core.exceptions import PermissionDenied
from django.db.models import Count, DateField
from django.db.models.functions import TruncMonth
from django.utils import timezone

from accounts.models import Role, UserRole

from .models import Document, DocumentVersion


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



def pending_documents_for_moderator(*, user):
    """ดึงรายการเอกสารรออนุมัติ (pending) ของภาควิชาที่ผู้ใช้ดูแล (หรือทุกภาคถ้าเป็น Super Admin)"""
    if not user.is_authenticated:
        return Document.objects.none()

    is_admin = user.is_superuser or UserRole.objects.filter(
        user=user, role__code=Role.SUPER_ADMIN
    ).exists()

    if is_admin:
        qs = Document.objects.filter(status=Document.Status.PENDING)
    else:
        moderator_dept_ids = UserRole.objects.filter(
            user=user, role__code=Role.MODERATOR, department__isnull=False
        ).values_list("department_id", flat=True)

        if not moderator_dept_ids:
            return Document.objects.none()

        qs = Document.objects.filter(
            status=Document.Status.PENDING,
            batch_course__batch__department_id__in=moderator_dept_ids,
        )

    return (
        qs.select_related(
            "batch_course__batch__department",
            "batch_course__course",
            "doc_type",
            "uploader",
        )
        .prefetch_related("versions")
        .order_by("-created_at")
    )


def get_document_for_review(*, document_id, user):
    """ดึงข้อมูลเอกสารสำหรับพิจารณา พร้อมตรวจสอบสิทธิ์ว่าผู้ใช้เป็นผู้ดูแลภาคนั้นจริง"""
    document = (
        Document.objects.select_related(
            "batch_course__batch__department",
            "batch_course__course",
            "doc_type",
            "uploader",
        )
        .prefetch_related("versions")
        .get(pk=document_id)
    )

    is_admin = user.is_superuser or UserRole.objects.filter(
        user=user, role__code=Role.SUPER_ADMIN
    ).exists()

    if not is_admin:
        doc_dept_id = document.batch_course.batch.department_id
        is_moderator = (
            user.is_authenticated
            and UserRole.objects.filter(
                user=user, role__code=Role.MODERATOR, department_id=doc_dept_id
            ).exists()
        )
        if not is_moderator:
            raise PermissionDenied("คุณไม่มีสิทธิ์เข้าถึงหรือตรวจสอบเอกสารของภาควิชานี้")

    return document
