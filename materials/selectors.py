from typing import NamedTuple

from django.core.exceptions import PermissionDenied

from accounts.models import Role, UserRole
from catalog.models import SystemSetting

from .models import Approval, DocType, DocTypeRequiredRole, Document


class ApprovalRule(NamedTuple):
    roles: list
    require_all: bool
    legacy: bool


class ApprovalProgress(NamedTuple):
    approved_roles: list
    missing_roles: list  # require_all=False: ขาดอีก 1 คนจาก role ใดก็ได้ในรายการ
    require_all: bool


def approval_rule(*, document):
    """กฎอนุมัติของเอกสารจาก doc_type_required_role (US-9)

    ยกเว้นข้อสอบรุ่นเก่า (<= legacy_batch_max) ที่ Super Admin ตัดสินคนเดียว
    """
    rules = list(document.doc_type.required_roles.select_related("role"))
    roles = [rule.role for rule in rules]
    if _is_legacy_exam(document):
        return ApprovalRule([r for r in roles if r.code == Role.SUPER_ADMIN], False, True)
    return ApprovalRule(
        roles, any(rule.mode == DocTypeRequiredRole.Mode.ALL for rule in rules), False
    )


def approved_role_ids(*, document):
    return set(
        document.approvals.filter(decision=Approval.Decision.APPROVED).values_list(
            "approver_role_id", flat=True
        )
    )


def approval_progress(*, document):
    """role ที่อนุมัติแล้วและ role ที่ยังรอ ให้หน้าคิว/หน้าพิจารณาแสดงสถานะ (US-9)"""
    rule = approval_rule(document=document)
    approved = approved_role_ids(document=document)
    approved_roles = [r for r in rule.roles if r.pk in approved]
    if rule.require_all:
        missing = [r for r in rule.roles if r.pk not in approved]
    else:
        missing = [] if approved_roles else rule.roles
    return ApprovalProgress(approved_roles, missing, rule.require_all)


def _is_legacy_exam(document):
    if document.doc_type.vault != DocType.Vault.EXAM:
        return False
    legacy_max = SystemSetting.get_int(SystemSetting.LEGACY_BATCH_MAX, 23)
    return document.batch_course.batch.number <= legacy_max


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
