"""การอ่านข้อมูลของ materials (ค้นหา / เปิดอ่านเอกสาร / อัปโหลด / ตรวจสอบสิทธิ์และการอนุมัติ) ตาม ADR 0002"""
from django.db.models import Q, QuerySet

from catalog.models import Batch, BatchCourse

from accounts.models import Role, UserRole
from portal.permissions import is_super_admin

from .models import Document


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


def is_reviewer_for(*, user, department_id):
    """ตรวจสอบว่าผู้ใช้มีสิทธิ์ตรวจเอกสารของภาควิชานี้หรือไม่ (Super Admin หรือ Moderator ประจำภาค)"""
    if not user or not user.is_authenticated:
        return False
    return is_super_admin(user) or UserRole.objects.filter(
        user=user, role__code=Role.MODERATOR, department_id=department_id
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
