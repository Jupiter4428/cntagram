"""การอ่านข้อมูลของ materials (ค้นหา / เปิดอ่านเอกสาร / อัปโหลด / ตรวจสอบสิทธิ์และการอนุมัติ / สถิติอัปโหลด) ตาม ADR 0002"""
import datetime
from collections import defaultdict
from typing import NamedTuple

from django.db.models import Count, DateField, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.utils import timezone

from catalog.models import Batch, BatchCourse, SystemSetting

from accounts.models import Role, UserRole
from portal.permissions import is_super_admin

from .models import Approval, DocType, DocTypeRequiredRole, Document, DocumentVersion


def published_documents():
    """เอกสารที่ผู้ใช้ทั่วไปเห็นได้ (เฉพาะ published) พร้อมข้อมูลที่หน้าเว็บต้องใช้ กัน N+1"""
    return Document.objects.filter(status=Document.Status.PUBLISHED).select_related(
        "batch_course__batch__department",
        "batch_course__course",
        "doc_type",
        "uploader",
    )


def search_documents(*, course_code, department=None, batch=None, doc_type=None):
    """เอกสาร published ของรหัสวิชานี้จากทุกรุ่น กรองเพิ่มด้วย ภาค/รุ่น/ประเภท ได้

    เทียบรหัสแบบตรงตัว (Course.code เก็บเป็นตัวพิมพ์ใหญ่) จึงใช้ UQ index ของ course.code ได้
    รหัสรุ่นไม่ได้เก็บใน DB จึงกรองรุ่นผ่าน batch_course__batch
    """
    conditions = Q(batch_course__course__code=course_code.strip().upper())
    if department is not None:
        conditions &= Q(batch_course__batch__department=department)
    if batch is not None:
        conditions &= Q(batch_course__batch=batch)
    if doc_type is not None:
        conditions &= Q(doc_type=doc_type)
    return (
        published_documents()
        .filter(conditions)
        .order_by(
            "batch_course__batch__department__code",
            "batch_course__batch__number",
            "-created_at",
        )
    )


def upload_batches(*, department) -> QuerySet[Batch]:
    """รุ่นที่ผู้ใช้อัปโหลดเข้าได้ = รุ่นในภาคของตัวเอง เรียงตามเลขรุ่น"""
    return Batch.objects.filter(department=department).order_by("number")


def upload_batch_courses(*, batch) -> QuerySet[BatchCourse]:
    """วิชาในรุ่นสำหรับ dropdown ต่อเนื่อง (รุ่น → วิชา)

    BatchCourseManager select_related course ให้อยู่แล้ว จึงไม่มี N+1
    """
    return BatchCourse.objects.filter(batch=batch).order_by("course__code")


def can_review_any(*, user):
    """ตรวจสอบว่าผู้ใช้เป็น Super Admin หรือ Moderator ของภาควิชาใดๆ หรือไม่"""
    if not user or not user.is_authenticated:
        return False
    return is_super_admin(user) or UserRole.objects.filter(
        user=user, role__code=Role.MODERATOR
    ).exists()


def pending_documents_for_moderator(*, user):
    """ดึงรายการเอกสารรออนุมัติ (pending) ของภาควิชาที่ผู้ใช้ดูแล (หรือทุกภาคถ้าเป็น Super Admin)

    ไม่รวมไฟล์ที่ตนเองเป็นผู้อัปโหลด และไม่รวมไฟล์ที่ตนเองพิจารณาไปแล้ว
    """
    if not user or not user.is_authenticated:
        return Document.objects.none()

    if is_super_admin(user):
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
        qs.exclude(uploader=user)
        .exclude(approvals__approver=user)
        .select_related(
            "batch_course__batch__department",
            "batch_course__course",
            "doc_type",
            "uploader",
        )
        .prefetch_related("versions")
        .order_by("-created_at")
    )


def get_document_for_review(*, document_id, user):
    """ดึงข้อมูลเอกสารสำหรับพิจารณา (เฉพาะ pending และผู้ใช้มีสิทธิ์ตรวจ) ไม่พบโยน Document.DoesNotExist"""
    return pending_documents_for_moderator(user=user).get(pk=document_id)


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


def eligible_roles(*, document, user, roles):
    """role ในกฎที่ user ใช้พิจารณาเอกสารนี้ได้ (moderator นับเฉพาะภาคที่ดูแล)"""
    department_id = document.batch_course.batch.department_id
    held = set(
        UserRole.objects.filter(user=user)
        .filter(Q(department__isnull=True) | Q(department_id=department_id))
        .values_list("role_id", flat=True)
    )
    return [role for role in roles if role.pk in held]


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
