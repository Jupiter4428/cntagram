from collections import defaultdict
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
    approvable: bool  # False = ไม่ใช่ pending หรือกฎไม่มี role ที่อนุมัติได้ (ค้างจนกว่าจะแก้กฎ)


def approval_rule(*, document):
    """กฎอนุมัติของเอกสารจาก doc_type_required_role (US-9)

    ยกเว้นข้อสอบรุ่นเก่า (<= legacy_batch_max) ที่ Super Admin ตัดสินคนเดียว
    """
    rules = list(
        document.doc_type.required_roles.select_related("role").order_by("role_id")
    )
    return _rule_from(document, rules, _legacy_batch_max([document]))


def approved_role_ids(*, document):
    """role_id ที่อนุมัติเอกสารนี้แล้ว"""
    return set(
        document.approvals.filter(decision=Approval.Decision.APPROVED).values_list(
            "approver_role_id", flat=True
        )
    )


def missing_roles(*, rule, approved_ids):
    """role ในกฎที่ยังขาด ([] = ครบตามกฎแล้ว ถ้ากฎมี role)

    กฎที่ไม่มี role ก็ได้ [] เหมือนกัน แต่ไม่มีใครผ่านการตรวจสิทธิ์ใน service จึงไม่มีทาง published
    """
    if rule.require_all:
        return [r for r in rule.roles if r.pk not in approved_ids]
    if any(r.pk in approved_ids for r in rule.roles):
        return []
    return rule.roles


def approval_progress(*, document):
    """role ที่อนุมัติแล้วและ role ที่ยังรอ ของเอกสาร 1 ชิ้น ให้หน้าพิจารณาแสดงสถานะ (US-9)"""
    return approval_progress_for(documents=[document])[document.pk]


def approval_progress_for(*, documents):
    """สถานะอนุมัติของหลายเอกสาร (หน้าคิว) คืน {document.pk: ApprovalProgress}

    ไม่เกิน 3 query ไม่ว่ากี่เอกสาร เอกสารควร select_related "doc_type", "batch_course__batch" มาแล้ว
    เอกสารที่ไม่ใช่ pending จะได้ missing_roles = []
    """
    documents = list(documents)
    rules_by_type = defaultdict(list)
    for rule in (
        DocTypeRequiredRole.objects.filter(doc_type_id__in={d.doc_type_id for d in documents})
        .select_related("role")
        .order_by("role_id")
    ):
        rules_by_type[rule.doc_type_id].append(rule)
    approved_by_doc = defaultdict(set)
    for document_id, role_id in Approval.objects.filter(
        document__in=documents, decision=Approval.Decision.APPROVED
    ).values_list("document_id", "approver_role_id"):
        approved_by_doc[document_id].add(role_id)
    legacy_max = _legacy_batch_max(documents)
    progress = {}
    for d in documents:
        rule = _rule_from(d, rules_by_type[d.doc_type_id], legacy_max)
        approved = approved_by_doc[d.pk]
        pending = d.status == Document.Status.PENDING
        progress[d.pk] = ApprovalProgress(
            approved_roles=[r for r in rule.roles if r.pk in approved],
            missing_roles=missing_roles(rule=rule, approved_ids=approved) if pending else [],
            require_all=rule.require_all,
            approvable=pending and bool(rule.roles),
        )
    return progress


def _rule_from(document, rules, legacy_max):
    roles = [rule.role for rule in rules]
    if _is_exam(document) and document.batch_course.batch.number <= legacy_max:
        return ApprovalRule(
            roles=[r for r in roles if r.code == Role.SUPER_ADMIN], require_all=False, legacy=True
        )
    return ApprovalRule(
        roles=roles,
        require_all=any(rule.mode == DocTypeRequiredRole.Mode.ALL for rule in rules),
        legacy=False,
    )


def _legacy_batch_max(documents):
    """อ่าน system_setting เฉพาะเมื่อมีข้อสอบ (None = ไม่มีข้อสอบ ไม่ต้องใช้)"""
    if not any(_is_exam(d) for d in documents):
        return None
    return SystemSetting.get_int(SystemSetting.LEGACY_BATCH_MAX, 23)


def _is_exam(document):
    return document.doc_type.vault == DocType.Vault.EXAM


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
