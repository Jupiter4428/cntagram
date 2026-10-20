from django.core.exceptions import PermissionDenied

from accounts.models import Role, UserRole

from .models import Document


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
