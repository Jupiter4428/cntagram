from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import Role, UserRole

from .models import Approval, DocType, Document


@transaction.atomic
def review_document(*, document, approver, decision, reason=None):
    """พิจารณาอนุมัติหรือปฏิเสธเอกสารโดย Moderator หรือ Super Admin (US-6)"""
    locked_doc = (
        Document.objects.select_for_update()
        .select_related("batch_course__batch", "doc_type")
        .get(pk=document.pk)
    )

    if locked_doc.uploader_id == approver.id:
        raise PermissionDenied("ผู้อัปโหลดไม่สามารถอนุมัติหรือปฏิเสธเอกสารของตนเองได้")

    doc_dept_id = locked_doc.batch_course.batch.department_id

    is_super_admin = approver.is_superuser or UserRole.objects.filter(
        user=approver, role__code=Role.SUPER_ADMIN
    ).exists()

    is_moderator = UserRole.objects.filter(
        user=approver, role__code=Role.MODERATOR, department_id=doc_dept_id
    ).exists()

    if not (is_super_admin or is_moderator):
        raise PermissionDenied("คุณไม่มีสิทธิ์พิจารณาเอกสารของภาควิชานี้")

    if is_moderator:
        approver_role, _ = Role.objects.get_or_create(
            code=Role.MODERATOR, defaults={"name_th": "ผู้ดูแลเนื้อหา"}
        )
    else:
        approver_role, _ = Role.objects.get_or_create(
            code=Role.SUPER_ADMIN, defaults={"name_th": "ผู้ดูแลระบบ"}
        )

    approval = Approval.objects.create(
        document=locked_doc,
        approver=approver,
        approver_role=approver_role,
        decision=decision,
        reason=reason if decision == Approval.Decision.REJECTED else (reason or None),
    )

    if decision == Approval.Decision.APPROVED:
        if locked_doc.doc_type.vault == DocType.Vault.LECTURE:
            locked_doc.status = Document.Status.PUBLISHED
            locked_doc.save(update_fields=["status", "updated_at"])
    elif decision == Approval.Decision.REJECTED:
        locked_doc.status = Document.Status.REJECTED
        locked_doc.save(update_fields=["status", "updated_at"])

    return approval
