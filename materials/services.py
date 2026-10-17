"""การเขียนข้อมูลของ materials ตาม ADR 0002"""
import hashlib
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.db import transaction

from .models import DocType, Document, ExamDetail, max_upload_mb

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
    # ภาควิชาล็อกตามสังกัด: ส่ง batch_course ของภาคอื่นมาเอง = แก้ request ข้ามภาค
    if batch_course.batch.department_id != uploader.department_id:
        raise PermissionDenied("อัปโหลดได้เฉพาะรุ่น/วิชาในภาควิชาของตัวเอง")
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
