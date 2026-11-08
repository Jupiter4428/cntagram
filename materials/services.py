"""การเขียนข้อมูลของ materials ตาม ADR 0002"""

import csv
import hashlib
import io
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from catalog.models import Batch, BatchCourse
from portal.permissions import is_super_admin

from . import selectors
from .models import (
    Approval,
    DocType,
    Document,
    DownloadLog,
    ExamDetail,
    ExamPeriod,
    max_upload_bytes,
    max_upload_mb,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def record_download(*, document, user):
    """Persist a protected download in the service layer."""
    return DownloadLog.objects.create(document=document, user=user)


PDF_MIME = "application/pdf"
PDF_MAGIC = b"%PDF-"


def _storage_path(batch_course, doc_type):
    """path ใน storage ตั้งชื่อไฟล์ด้วย uuid ไม่ใช้ชื่อที่ผู้ใช้ส่งมา จึงเดา path หรือชนกันไม่ได้"""  # noqa: E501
    batch = batch_course.batch
    return (
        f"vault/{batch.department.code}/{batch.number}/{batch_course.course.code}/"
        f"{doc_type.code}/{uuid.uuid4().hex}.pdf"
    )


def file_too_large_message():
    """ข้อความเมื่อไฟล์เกิน max_upload_mb ใช้ทั้งที่ service และตอน upload handler ข้ามไฟล์"""  # noqa: E501
    return f"ไฟล์ต้องมีขนาดไม่เกิน {max_upload_mb()} MB"


def validate_pdf_bytes(*, content: bytes, max_bytes: Optional[int] = None):
    """ตรวจสอบขนาดและ header %PDF- ของเนื้อหาไฟล์แบบไบนารี"""
    if max_bytes is None:
        max_bytes = max_upload_bytes()
    if len(content) > max_bytes:
        raise ValidationError({"file": file_too_large_message()})
    if not content.startswith(PDF_MAGIC):
        raise ValidationError({"file": "รับเฉพาะไฟล์ PDF เท่านั้น"})


def _validate_pdf(file):
    """รับเฉพาะ PDF: MIME ที่ browser ส่งมาต้องเป็น PDF
    และ magic bytes ต้องขึ้นต้นด้วย %PDF-

    MIME ปลอมได้ฝั่ง client จึงต้องเช็ก magic bytes ของเนื้อไฟล์จริงด้วย
    """
    if file.size > max_upload_bytes():
        raise ValidationError({"file": file_too_large_message()})
    file.seek(0)
    header = file.read(len(PDF_MAGIC))
    file.seek(0)
    if file.content_type != PDF_MIME or header != PDF_MAGIC:
        raise ValidationError({"file": "รับเฉพาะไฟล์ PDF เท่านั้น"})


def _sha256(file):
    """hash ของเนื้อไฟล์ทีละ chunk แล้ว seek กลับต้นไฟล์ให้ storage อ่านต่อได้"""
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
    if selectors.file_in_vault(sha256=sha256):
        raise ValidationError({"file": "ไฟล์นี้มีอยู่ในคลังแล้ว"})
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
        # ถ้าลบไม่ได้ให้ log path ไว้ตามเก็บทีหลัง error ที่ต้องส่งต่อคือของ DB
        try:
            default_storage.delete(storage_path)
        except Exception:  # storage อื่น (เช่น S3) โยน error คนละชนิดกับ OSError
            logger.exception("Could not remove orphaned upload %s", storage_path)
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
    eligible = selectors.eligible_roles(
        document=locked_doc, user=approver, roles=rule.roles
    )
    if not eligible:
        if rule.legacy:
            raise PermissionDenied(
                "ข้อสอบของรุ่นนี้ให้ Super Admin เท่านั้นเป็นผู้พิจารณา"
            )
        raise PermissionDenied("คุณไม่มีสิทธิ์พิจารณาเอกสารของภาควิชานี้")

    if locked_doc.approvals.filter(approver=approver).exists():
        raise ValidationError("คุณพิจารณาเอกสารนี้ไปแล้ว")

    # คนที่มีหลาย role ให้นับเป็นฝ่ายที่ยังไม่มีใครอนุมัติก่อน ไม่งั้นกฎ all จะไม่มีวันครบ  # noqa: E501
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
        if not selectors.missing_roles(
            rule=rule, approved_ids=approved_ids | {approver_role.pk}
        ):
            locked_doc.status = Document.Status.PUBLISHED
            locked_doc.save(update_fields=["status", "updated_at"])
    elif decision == Approval.Decision.REJECTED:
        locked_doc.status = Document.Status.REJECTED
        locked_doc.save(update_fields=["status", "updated_at"])

    return approval


@transaction.atomic
def hide_document(*, document, user, reason):
    """ซ่อนไฟล์ที่เผยแพร่แล้วแต่มีปัญหา (US-15)

    Moderator (เฉพาะภาคของตน) และ Super Admin (ทุกภาค)
    สามารถสั่งซ่อนเอกสารที่เป็น published พร้อมบันทึกเหตุผล
    """
    cleaned_reason = (reason or "").strip()
    if not cleaned_reason:
        raise ValidationError({"reason": "กรุณาระบุเหตุผลในการซ่อนเอกสาร"})

    locked_doc = (
        Document.objects.select_for_update()
        .select_related("batch_course__batch")
        .get(pk=document.pk)
    )

    if not selectors.can_hide_document(document=locked_doc, user=user):
        raise PermissionDenied("คุณไม่มีสิทธิ์ซ่อนเอกสารนี้")

    if locked_doc.status != Document.Status.PUBLISHED:
        raise ValidationError("สามารถซ่อนได้เฉพาะเอกสารที่เผยแพร่แล้วเท่านั้น")

    locked_doc.status = Document.Status.HIDDEN
    locked_doc.save(update_fields=["status", "updated_at"])
    return locked_doc


@dataclass
class BulkImportItemResult:
    row_num: int
    status: str  # "imported", "skipped", "failed"
    message: str
    file_path: str = ""
    title: str = ""
    document_id: Optional[int] = None


@dataclass
class BulkImportSummary:
    total_rows: int = 0
    imported_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    results: List[BulkImportItemResult] = field(default_factory=list)


def validate_bulk_import_row(
    *,
    row: dict,
    files_dir: Optional[str] = None,
    zip_archive=None,
):
    """ตรวจสอบความถูกต้องของข้อมูล 1 แถวใน CSV และคืนค่าอ็อบเจกต์ที่เกี่ยวข้อง

    คืนค่า dict ที่มี:
    - batch_course
    - doc_type
    - title
    - description
    - exam_period
    - exam_year_be
    - file_bytes
    - filename
    - sha256
    หากพบข้อผิดพลาด จะ raise ValidationError
    """
    file_path = (row.get("file_path") or "").strip()
    dept_code = (row.get("department") or "").strip()
    batch_num_str = (row.get("batch") or "").strip()
    course_code = (row.get("course") or "").strip()
    doc_type_code = (row.get("doc_type") or "").strip()
    title = (row.get("title") or "").strip()
    description = (row.get("description") or "").strip()
    exam_period_code = (row.get("exam_period") or "").strip()
    exam_year_be_str = (row.get("exam_year_be") or "").strip()

    errors = {}

    if not file_path:
        errors["file_path"] = "กรุณาระบุ file_path"
    if not dept_code:
        errors["department"] = "กรุณาระบุรหัสภาควิชา"
    if not batch_num_str:
        errors["batch"] = "กรุณาระบุเลขรุ่น"
    if not course_code:
        errors["course"] = "กรุณาระบุรหัสวิชา"
    if not doc_type_code:
        errors["doc_type"] = "กรุณาระบุประเภทเอกสาร"
    if not title:
        errors["title"] = "กรุณาระบุชื่อเอกสาร"

    if errors:
        raise ValidationError(errors)

    try:
        batch_num = int(batch_num_str)
    except ValueError:
        raise ValidationError({"batch": f"เลขรุ่นไม่ถูกต้อง ({batch_num_str})"})

    # ตรวจสอบ BatchCourse
    try:
        batch = Batch.objects.select_related("department").get(
            department__code=dept_code, number=batch_num
        )
    except Batch.DoesNotExist:
        raise ValidationError(
            {"batch": f"ไม่พบรุ่น {dept_code}{batch_num} ในภาควิชา {dept_code}"}
        )

    try:
        batch_course = BatchCourse.objects.select_related(
            "course", "batch", "batch__department"
        ).get(batch=batch, course__code=course_code)
    except BatchCourse.DoesNotExist:
        raise ValidationError(
            {"course": f"ไม่พบวิชา {course_code} ในรุ่น {dept_code}{batch_num}"}
        )

    # ตรวจสอบ DocType
    try:
        doc_type = DocType.objects.get(code=doc_type_code)
    except DocType.DoesNotExist:
        raise ValidationError({"doc_type": f"ไม่พบประเภทเอกสารรหัส {doc_type_code}"})

    is_exam = doc_type.vault == DocType.Vault.EXAM
    exam_period = None
    exam_year_be = None

    if is_exam:
        exam_errors = {}
        if not exam_period_code:
            exam_errors["exam_period"] = "ข้อสอบเก่าต้องระบุช่วงสอบ (midterm/final)"
        else:
            try:
                exam_period = ExamPeriod.objects.get(code=exam_period_code)
            except ExamPeriod.DoesNotExist:
                exam_errors["exam_period"] = f"ไม่พบช่วงสอบรหัส {exam_period_code}"

        if not exam_year_be_str:
            exam_errors["exam_year_be"] = "ข้อสอบเก่าต้องระบุปี พ.ศ."
        else:
            try:
                exam_year_be = int(exam_year_be_str)
                if not (2500 <= exam_year_be <= 2700):
                    exam_errors["exam_year_be"] = "ปี พ.ศ. ต้องอยู่ระหว่าง 2500 - 2700"
            except ValueError:
                exam_errors["exam_year_be"] = f"ปี พ.ศ. ไม่ถูกต้อง ({exam_year_be_str})"

        if exam_errors:
            raise ValidationError(exam_errors)

    # อ่านไฟล์และตรวจสอบ
    file_bytes = None
    if zip_archive:
        norm_path = file_path.replace("\\", "/").lstrip("/")
        try:
            file_bytes = zip_archive.read(norm_path)
        except KeyError:
            base_name = os.path.basename(norm_path)
            matching = [n for n in zip_archive.namelist() if n.endswith(base_name)]
            if len(matching) == 1:
                file_bytes = zip_archive.read(matching[0])
            else:
                raise ValidationError({"file_path": f"ไม่พบไฟล์ {file_path} ใน ZIP"})
    elif files_dir:
        abs_file_path = os.path.abspath(os.path.join(files_dir, file_path))
        if not os.path.isfile(abs_file_path):
            raise ValidationError(
                {"file_path": f"ไม่พบไฟล์ที่พาธ {file_path} (ในโฟลเดอร์ {files_dir})"}
            )
        try:
            with open(abs_file_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            raise ValidationError({"file_path": f"ไม่สามารถอ่านไฟล์ได้: {e}"})
    else:
        raise ValidationError({"file_path": "ไม่ได้ระบุแหล่งที่อยู่ของไฟล์"})

    validate_pdf_bytes(content=file_bytes)
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    filename = os.path.basename(file_path.replace("\\", "/"))

    return {
        "batch_course": batch_course,
        "doc_type": doc_type,
        "title": title,
        "description": description,
        "exam_period": exam_period,
        "exam_year_be": exam_year_be,
        "file_bytes": file_bytes,
        "filename": filename,
        "sha256": sha256,
    }


def bulk_import_documents_from_csv(
    *,
    csv_content: str,
    user,
    files_dir: Optional[str] = None,
    zip_archive=None,
    dry_run: bool = False,
) -> BulkImportSummary:
    """ประมวลผลนำเข้าเอกสารจำนวนมากจาก CSV (US-17)

    - เฉพาะ Super Admin เท่านั้นที่เรียกใช้ได้
    - dry_run = True: ตรวจสอบความถูกต้องทุกแถวและรายงานโดยไม่เขียน DB หรือ storage
    - dry_run = False: บันทึกเอกสารจริงในสถานะ PUBLISHED (พร้อมบันทึก storage)
    - แถวที่ผิดพลาดจะถูกข้ามและรายงานใน Summary (Skip & Report)
    - ไฟล์ที่มี sha256 ตรงกับเอกสารที่มีอยู่แล้วในระบบจะถูกข้าม (Skip)
    """
    if not is_super_admin(user):
        raise ValidationError("เฉพาะ Super Admin เท่านั้นที่สามารถนำเข้าเอกสารได้")

    summary = BulkImportSummary()
    reader = csv.DictReader(io.StringIO(csv_content))

    for idx, row in enumerate(reader, start=2):  # start=2 considering header is line 1
        summary.total_rows += 1
        raw_file_path = (row.get("file_path") or "").strip()
        raw_title = (row.get("title") or "").strip()

        try:
            validated = validate_bulk_import_row(
                row=row, files_dir=files_dir, zip_archive=zip_archive
            )
        except ValidationError as e:
            summary.failed_count += 1
            if hasattr(e, "message_dict"):
                err_msg = "; ".join(
                    f"{k}: {', '.join(v)}" for k, v in e.message_dict.items()
                )
            else:
                err_msg = ", ".join(e.messages)
            summary.results.append(
                BulkImportItemResult(
                    row_num=idx,
                    status="failed",
                    message=err_msg,
                    file_path=raw_file_path,
                    title=raw_title,
                )
            )
            continue

        sha256 = validated["sha256"]
        if selectors.file_in_vault(sha256=sha256):
            summary.skipped_count += 1
            summary.results.append(
                BulkImportItemResult(
                    row_num=idx,
                    status="skipped",
                    message="ไฟล์ซ้ำ (มีอยู่ในคลังแล้ว)",
                    file_path=raw_file_path,
                    title=validated["title"],
                )
            )
            continue

        if dry_run:
            summary.imported_count += 1
            summary.results.append(
                BulkImportItemResult(
                    row_num=idx,
                    status="imported",
                    message="ผ่านการตรวจสอบ (Dry run)",
                    file_path=raw_file_path,
                    title=validated["title"],
                )
            )
            continue

        # Real Run: เขียนไฟล์ลง storage และสร้าง Document สถานะ PUBLISHED
        batch_course = validated["batch_course"]
        doc_type = validated["doc_type"]
        file_bytes = validated["file_bytes"]
        filename = validated["filename"]
        title = validated["title"]
        description = validated["description"]
        exam_period = validated["exam_period"]
        exam_year_be = validated["exam_year_be"]

        storage_target = _storage_path(batch_course, doc_type)
        storage_path = default_storage.save(storage_target, ContentFile(file_bytes))

        try:
            with transaction.atomic():
                document = Document.objects.create(
                    batch_course=batch_course,
                    doc_type=doc_type,
                    uploader=user,
                    title=title,
                    description=description,
                    status=Document.Status.PUBLISHED,
                )
                document.add_version(
                    storage_path=storage_path,
                    original_name=filename,
                    size_bytes=len(file_bytes),
                    sha256=sha256,
                )
                if doc_type.vault == DocType.Vault.EXAM:
                    exam_detail = ExamDetail(
                        document=document,
                        exam_period=exam_period,
                        exam_year_be=exam_year_be,
                    )
                    exam_detail.full_clean()
                    exam_detail.save()

            summary.imported_count += 1
            summary.results.append(
                BulkImportItemResult(
                    row_num=idx,
                    status="imported",
                    message="นำเข้าสำเร็จ",
                    file_path=raw_file_path,
                    title=title,
                    document_id=document.pk,
                )
            )
        except Exception as e:
            try:
                default_storage.delete(storage_path)
            except Exception:
                logger.exception("Could not remove orphaned upload %s", storage_path)
            summary.failed_count += 1
            summary.results.append(
                BulkImportItemResult(
                    row_num=idx,
                    status="failed",
                    message=f"ข้อผิดพลาดระหว่างบันทึกข้อมูล: {e}",
                    file_path=raw_file_path,
                    title=title,
                )
            )

    return summary
