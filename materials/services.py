from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import Role, UserRole

from . import selectors
from .models import Approval, DocType, Document


@transaction.atomic
def review_document(*, document, approver, decision, reason=None):
    """พิจารณาอนุมัติหรือปฏิเสธเอกสารโดย Moderator หรือ Super Admin (US-6)"""
    locked_doc = (
        Document.objects.select_for_update()
        .select_related("batch_course__batch", "doc_type")
        .get(pk=document.pk)
    )

    if locked_doc.status != Document.Status.PENDING:
        raise ValidationError("เอกสารนี้ถูกพิจารณาไปแล้ว")

    if locked_doc.uploader_id == approver.id:
        raise PermissionDenied("ผู้อัปโหลดไม่สามารถอนุมัติหรือปฏิเสธเอกสารของตนเองได้")

    if locked_doc.approvals.filter(approver=approver).exists():
        raise ValidationError("คุณพิจารณาเอกสารนี้ไปแล้ว")

    doc_dept_id = locked_doc.batch_course.batch.department_id

    if not selectors.is_reviewer_for(user=approver, department_id=doc_dept_id):
        raise PermissionDenied("คุณไม่มีสิทธิ์พิจารณาเอกสารของภาควิชานี้")

    is_moderator = UserRole.objects.filter(
        user=approver, role__code=Role.MODERATOR, department_id=doc_dept_id
    ).exists()

    approver_role = Role.objects.get(
        code=Role.MODERATOR if is_moderator else Role.SUPER_ADMIN
    )

    approval = Approval.objects.create(
        document=locked_doc,
        approver=approver,
        approver_role=approver_role,
        decision=decision,
        reason=reason,
    )

    if decision == Approval.Decision.APPROVED:
        if locked_doc.doc_type.vault == DocType.Vault.LECTURE:
            locked_doc.status = Document.Status.PUBLISHED
            locked_doc.save(update_fields=["status", "updated_at"])
        # หมายเหตุ: เอกสารข้อสอบ (vault == EXAM) ต้องรอการอนุมัติทั้ง Moderator และ Super Admin ตาม US-9 จึงคงสถานะ PENDING ไว้
    elif decision == Approval.Decision.REJECTED:
        locked_doc.status = Document.Status.REJECTED
        locked_doc.save(update_fields=["status", "updated_at"])

    return approval
