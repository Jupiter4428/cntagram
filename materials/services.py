from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q

from accounts.models import Role, UserRole
from catalog.models import SystemSetting

from .models import Approval, DocType, DocTypeRequiredRole, Document


@transaction.atomic
def review_document(*, document, approver, decision, reason=None):
    """พิจารณาอนุมัติหรือปฏิเสธเอกสารโดย Moderator หรือ Super Admin (US-6)

    ใครพิจารณาได้และต้องครบกี่ฝ่ายมาจาก doc_type_required_role (US-9)
    """
    locked_doc = (
        Document.objects.select_for_update()
        .select_related("batch_course__batch", "doc_type")
        .get(pk=document.pk)
    )

    if locked_doc.uploader_id == approver.id:
        raise PermissionDenied("ผู้อัปโหลดไม่สามารถอนุมัติหรือปฏิเสธเอกสารของตนเองได้")

    if locked_doc.status != Document.Status.PENDING:
        raise ValidationError("พิจารณาได้เฉพาะเอกสารที่รออนุมัติ")

    legacy = _is_legacy_exam(locked_doc)
    required_roles, require_all = _approval_rule(locked_doc, legacy)
    eligible = _eligible_roles(locked_doc, approver, required_roles)
    if not eligible:
        if legacy:
            raise PermissionDenied("ข้อสอบของรุ่นนี้ให้ Super Admin เท่านั้นเป็นผู้พิจารณา")
        raise PermissionDenied("คุณไม่มีสิทธิ์พิจารณาเอกสารของภาควิชานี้")
    if locked_doc.approvals.filter(approver=approver).exists():
        raise ValidationError("คุณพิจารณาเอกสารนี้ไปแล้ว")

    # คนที่มีหลาย role ให้นับเป็นฝ่ายที่ยังไม่มีใครอนุมัติก่อน ไม่งั้นกฎ all จะไม่มีวันครบ
    approved_ids = _approved_role_ids(locked_doc)
    approver_role = next((r for r in eligible if r.pk not in approved_ids), eligible[0])

    approval = Approval.objects.create(
        document=locked_doc,
        approver=approver,
        approver_role=approver_role,
        decision=decision,
        reason=reason if decision == Approval.Decision.REJECTED else (reason or None),
    )

    if decision == Approval.Decision.APPROVED:
        if _rule_satisfied(approved_ids | {approver_role.pk}, required_roles, require_all):
            locked_doc.status = Document.Status.PUBLISHED
            locked_doc.save(update_fields=["status", "updated_at"])
    elif decision == Approval.Decision.REJECTED:
        locked_doc.status = Document.Status.REJECTED
        locked_doc.save(update_fields=["status", "updated_at"])

    return approval


def _approval_rule(document, legacy):
    """คืน (role ที่พิจารณาได้, ต้องครบทุก role หรือไม่) จาก doc_type_required_role

    ยกเว้นข้อสอบรุ่นเก่า (<= legacy_batch_max) ที่ Super Admin ตัดสินคนเดียว
    """
    rules = list(document.doc_type.required_roles.select_related("role"))
    roles = [rule.role for rule in rules]
    if legacy:
        return [role for role in roles if role.code == Role.SUPER_ADMIN], False
    return roles, any(rule.mode == DocTypeRequiredRole.Mode.ALL for rule in rules)


def _is_legacy_exam(document):
    legacy_max = SystemSetting.get_int(SystemSetting.LEGACY_BATCH_MAX, 23)
    return (
        document.doc_type.vault == DocType.Vault.EXAM
        and document.batch_course.batch.number <= legacy_max
    )


def _approved_role_ids(document):
    return set(
        document.approvals.filter(decision=Approval.Decision.APPROVED).values_list(
            "approver_role_id", flat=True
        )
    )


def _rule_satisfied(approved, required_roles, require_all):
    required_ids = {role.pk for role in required_roles}
    if require_all:
        return required_ids <= approved
    return bool(required_ids & approved)


def _eligible_roles(document, approver, required_roles):
    """role ในกฎที่ approver ถืออยู่ (moderator นับเฉพาะภาคที่ดูแล, superuser นับเป็น super_admin)"""
    department_id = document.batch_course.batch.department_id
    held = set(
        UserRole.objects.filter(user=approver)
        .filter(Q(department__isnull=True) | Q(department_id=department_id))
        .values_list("role_id", flat=True)
    )
    return [
        role
        for role in required_roles
        if role.pk in held or (approver.is_superuser and role.code == Role.SUPER_ADMIN)
    ]
