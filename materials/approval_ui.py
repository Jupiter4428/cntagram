"""Presentation-only approval state for Issue #73 (US-9).

Call attach_approval_ui(documents, user) in the approval queue view, and
attach_approval_ui([document], user) in the review view.
The server-side review_document service remains the authority for permissions.
"""
from types import SimpleNamespace


from accounts.models import Role, UserRole
from materials.models import Approval
from materials.selectors import approval_progress_for


def attach_approval_ui(documents, user):
    """Attach display state in bulk, avoiding a per-document query."""
    documents = list(documents)
    if not documents:
        return documents

    progress_by_id = approval_progress_for(documents=documents)
    # Moderator roles are department-scoped. Never grant UI permission
    # based on a role held for a different department.
    user_role_pairs = set(
        UserRole.objects.filter(user=user).values_list(
            "role__code", "department_id"
        )
    )

    already_reviewed = set(
        Approval.objects.filter(document__in=documents, approver=user)
        .values_list("document_id", flat=True)
    )
    for document in documents:
        progress = progress_by_id[document.pk]
        missing = progress.missing_roles
        department_id = document.batch_course.batch.department_id
        eligible = any(
            (role.code, None) in user_role_pairs
            or (role.code, department_id) in user_role_pairs
            or (user.is_superuser and role.code == Role.SUPER_ADMIN)
            for role in missing
        )
        if not progress.approvable:
            reason = "เอกสารนี้ยังไม่สามารถพิจารณาได้"
        elif document.uploader_id == user.pk:
            reason = "ไม่สามารถอนุมัติเอกสารที่ตนอัปโหลด"
        elif document.pk in already_reviewed:
            reason = "คุณได้พิจารณาเอกสารนี้แล้ว"
        elif not eligible:
            if any(role.code == Role.SUPER_ADMIN for role in missing) and not any(
                role.code == Role.MODERATOR for role in missing
            ):
                reason = "รอ Super Admin พิจารณา (Moderator ไม่มีสิทธิ์)"
            else:
                reason = "คุณไม่มีบทบาทที่ยังต้องอนุมัติเอกสารนี้"
        else:
            reason = ""

        document.approval_ui = SimpleNamespace(
            approved_roles=progress.approved_roles,
            missing_roles=missing,
            require_all=progress.require_all,
            can_review=not reason,
            reason=reason,
        )
    return documents
