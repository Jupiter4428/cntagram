"""การเขียนข้อมูลของ materials ตาม ADR 0002"""
import hashlib
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.db import transaction

from . import selectors
from .models import Approval, DocType, Document, ExamDetail, max_upload_mb

PDF_MIME = "application/pdf"
PDF_MAGIC = b"%PDF-"


def _storage_path(batch_course, doc_type):
    batch = batch_course.batch
    return (
        f"vault/{batch.department.code}/{batch.number}/{batch_course.course.code}/"
        f"{doc_type.code}/{uuid.uuid4().hex}.pdf"
    )


def _validate_pdf(file):
    """รับเฉพาะ PDF: MIME ที่ browser ส่งมาต้องเป็น PDF และ magic bytes ต้องขึ้นต้นด้วย %PDF-

    MIME ปลอมได้ฝั่ง client จึงต้องเช็ก magic bytes ของเนื้อไฟล์จริงด้วย
    """
    limit_mb = max_upload_mb()
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError({"file": f"ไฟล์ต้องมีขนาดไม่เกิน {limit_mb} MB"})
    file.seek(0)
    header = file.read(len(PDF_MAGIC))
    file.seek(0)
    if file.content_type != PDF_MIME or header != PDF_MAGIC:
        raise ValidationError({"file": "รับเฉพาะไฟล์ PDF เท่านั้น"})


def _sha256(file):
    digest = hashlib.sha256()
    for chunk in file.chunks():
        digest.update(chunk)
    file.seek(0)
    return digest.hexdigest()


def ensure_can_upload_to(*, user, batch):
    """ภาควิชาล็อกตามสังกัด: เลือก/ส่งรุ่นของภาคอื่นมาเอง = แก้ request ข้ามภาค → 403"""
    if batch.department_id != user.department_id:
        raise PermissionDenied("อัปโหลดได้เฉพาะรุ่น/วิชาในภาควิชาของตัวเอง")


def upload_document(
    *,
    uploader,
    batch_course,
    doc_type,
    title,
    description,
    file,
    exam_period=None,
    exam_year_be=None,
):
    """อัปโหลดชีทใหม่ (US-5): สร้าง Document สถานะ pending พร้อมเวอร์ชันแรก

    ประเภทที่อยู่คลังข้อสอบต้องระบุช่วงสอบ + ปี พ.ศ. (เก็บใน ExamDetail)
    ไฟล์เก็บที่ vault/{ภาค}/{เลขรุ่น}/{รหัสวิชา}/{ประเภท}/{uuid}.pdf
    """
    ensure_can_upload_to(user=uploader, batch=batch_course.batch)
    is_exam = doc_type.vault == DocType.Vault.EXAM
    if is_exam:
        missing = {
            field: "ข้อสอบเก่าต้องระบุช่วงสอบและปี พ.ศ."
            for field, value in (
                ("exam_period", exam_period),
                ("exam_year_be", exam_year_be),
            )
            if value is None
        }
        if missing:
            raise ValidationError(missing)
    _validate_pdf(file)
    sha256 = _sha256(file)
    storage_path = default_storage.save(_storage_path(batch_course, doc_type), file)
    try:
        with transaction.atomic():
            document = Document.objects.create(
                batch_course=batch_course,
                doc_type=doc_type,
                uploader=uploader,
                title=title,
                description=description,
            )
            document.add_version(
                storage_path=storage_path,
                original_name=file.name,
                size_bytes=file.size,
                sha256=sha256,
            )
            if is_exam:
                exam_detail = ExamDetail(
                    document=document,
                    exam_period=exam_period,
                    exam_year_be=exam_year_be,
                )
                exam_detail.full_clean()
                exam_detail.save()
    except Exception:
        # บันทึก DB ไม่สำเร็จ ลบไฟล์ทิ้ง ไม่ให้มีไฟล์กำพร้าค้างใน storage
        default_storage.delete(storage_path)
        raise
    return document


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

    if locked_doc.status != Document.Status.PENDING:
        raise ValidationError("เอกสารนี้ถูกพิจารณาไปแล้ว")

    if locked_doc.uploader_id == approver.id:
        raise PermissionDenied("ผู้อัปโหลดไม่สามารถอนุมัติหรือปฏิเสธเอกสารของตนเองได้")

    rule = selectors.approval_rule(document=locked_doc)
    eligible = selectors.eligible_roles(document=locked_doc, user=approver, roles=rule.roles)
    if not eligible:
        if rule.legacy:
            raise PermissionDenied("ข้อสอบของรุ่นนี้ให้ Super Admin เท่านั้นเป็นผู้พิจารณา")
        raise PermissionDenied("คุณไม่มีสิทธิ์พิจารณาเอกสารของภาควิชานี้")

    if locked_doc.approvals.filter(approver=approver).exists():
        raise ValidationError("คุณพิจารณาเอกสารนี้ไปแล้ว")

    # คนที่มีหลาย role ให้นับเป็นฝ่ายที่ยังไม่มีใครอนุมัติก่อน ไม่งั้นกฎ all จะไม่มีวันครบ
    approved_ids = selectors.approved_role_ids(document=locked_doc)
    approver_role = next((r for r in eligible if r.pk not in approved_ids), eligible[0])

    approval = Approval.objects.create(
        document=locked_doc,
        approver=approver,
        approver_role=approver_role,
        decision=decision,
        reason=reason,
    )

    if decision == Approval.Decision.APPROVED:
        if not selectors.missing_roles(rule=rule, approved_ids=approved_ids | {approver_role.pk}):
            locked_doc.status = Document.Status.PUBLISHED
            locked_doc.save(update_fields=["status", "updated_at"])
    elif decision == Approval.Decision.REJECTED:
        locked_doc.status = Document.Status.REJECTED
        locked_doc.save(update_fields=["status", "updated_at"])

    return approval
