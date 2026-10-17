"""การเขียนข้อมูลของ materials ตาม ADR 0002"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import Role
from catalog.models import SystemSetting

from .models import Approval, DocType, DocTypeRequiredRole, Document


@transaction.atomic
def approve_document(*, document, approver):
    """บันทึกการอนุมัติของ approver แล้วเปลี่ยนเป็น published เมื่อครบตามกฎ

    กฎมาจาก doc_type_required_role ยกเว้นข้อสอบรุ่นเก่า (<= legacy_batch_max)
    ที่ Super Admin ตัดสินคนเดียว
    """
    # ล็อกแถวก่อน กันผู้อนุมัติ 2 ฝ่ายกดพร้อมกันแล้วต่างคนต่างไม่เห็นอีกฝ่าย
    document = (
        Document.objects.select_for_update()
        .select_related("doc_type", "batch_course__batch")
        .get(pk=document.pk)
    )
    if document.status != Document.Status.PENDING:
        raise ValidationError("Only pending documents can be approved")
    required_roles, require_all = _approval_rule(document)
    # moderator ใช้สิทธิ์ได้เฉพาะภาคที่ตัวเองดูแล role อื่น department เป็น NULL
    department_id = document.batch_course.batch.department_id
    held = {
        ur.role_id
        for ur in approver.user_roles.all()
        if ur.department_id in (None, department_id)
    }
    eligible = [r for r in required_roles if r.pk in held]
    if not eligible:
        raise PermissionDenied("You cannot approve this document")
    # คนที่มีหลาย role ให้นับเป็นฝ่ายที่ยังไม่มีใครอนุมัติก่อน ไม่งั้นกฎ all จะไม่มีวันครบ
    approved_ids = _approved_role_ids(document)
    role = next((r for r in eligible if r.pk not in approved_ids), eligible[0])
    if document.approvals.filter(approver=approver).exists():
        raise ValidationError("You have already decided on this document")
    Approval.objects.create(
        document=document,
        approver=approver,
        approver_role=role,
        decision=Approval.Decision.APPROVED,
    )
    if _rule_satisfied(document, required_roles, require_all):
        document.status = Document.Status.PUBLISHED
        document.save(update_fields=["status", "updated_at"])
    return document


def _approval_rule(document):
    """คืน (role ที่อนุมัติได้, ต้องครบทุก role หรือไม่)"""
    rules = list(document.doc_type.required_roles.select_related("role"))
    roles = [rule.role for rule in rules]
    if _is_legacy_exam(document):
        return [r for r in roles if r.code == Role.SUPER_ADMIN], False
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


def _rule_satisfied(document, required_roles, require_all):
    approved = _approved_role_ids(document)
    required_ids = {r.pk for r in required_roles}
    if require_all:
        return required_ids <= approved
    return bool(required_ids & approved)
