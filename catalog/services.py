"""การเขียนข้อมูลของ catalog (รุ่น / วิชาในรุ่น) ตาม ADR 0002

ทุกฟังก์ชันแจ้งความผิดพลาดด้วย ValidationError ข้อความภาษาไทย ให้ view นำไปแสดงได้เลย
การเช็กสิทธิ์ Super Admin ทำที่ view (permission เดียวกับหน้าภาควิชาของ US-3)
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from .models import Batch, BatchCourse, Course


def _batch_exists_error(batch):
    return ValidationError(f"รุ่น {batch.code} มีอยู่แล้ว")


def _batch_has_courses_error(batch):
    return ValidationError(
        f"ลบรุ่น {batch.code} ไม่ได้ เพราะยังมีรายวิชาอยู่ในรุ่นนี้ กรุณาถอดวิชาออกก่อน"
    )


def _course_in_batch_error(batch, course):
    return ValidationError(f"วิชา {course.code} อยู่ในรุ่น {batch.code} แล้ว")


def create_batch(*, department, number):
    """สร้างรุ่นใหม่ในภาค เช่น ภาค CN + 21 → รุ่น CN21 (รหัสรุ่นประกอบให้เอง ไม่ต้องกรอก)"""
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValidationError("เลขรุ่นต้องเป็นจำนวนเต็มตั้งแต่ 1 ขึ้นไป")

    batch = Batch(department=department, number=number)
    if Batch.objects.filter(department=department, number=number).exists():
        raise _batch_exists_error(batch)
    try:
        # savepoint ถ้าอีกคนสร้างรุ่นเดียวกันตัดหน้า UQ จะกันไว้ และ transaction หลักยังใช้ต่อได้
        with transaction.atomic():
            batch.save()
    except IntegrityError:
        raise _batch_exists_error(batch)
    return batch


@transaction.atomic
def delete_batch(*, batch):
    """ลบรุ่น ได้เฉพาะรุ่นที่ยังไม่มีวิชาผูกอยู่"""
    if batch.batch_courses.exists():
        raise _batch_has_courses_error(batch)
    try:
        with transaction.atomic():
            batch.delete()
    except ProtectedError:
        # มีวิชาถูกผูกเข้ามาระหว่างที่เช็กด้านบน
        raise _batch_has_courses_error(batch)


def _get_or_create_course(*, code, name_en, name_th):
    """หาวิชาจากรหัส ถ้ายังไม่มีจึงสร้างใหม่ (ต้องมีชื่ออังกฤษ)"""
    course = Course.objects.filter(code=code).first()
    if course is not None:
        return course
    if not (name_en or "").strip():
        raise ValidationError(
            f"ยังไม่มีวิชา {code} ในระบบ กรุณากรอกชื่อวิชาภาษาอังกฤษเพื่อสร้างวิชาใหม่"
        )
    course = Course(code=code, name_en=name_en.strip(), name_th=name_th)
    course.full_clean(validate_unique=False)
    try:
        with transaction.atomic():
            course.save()
    except IntegrityError:
        # อีกคนสร้างรหัสนี้ตัดหน้า ใช้วิชาที่เขาสร้าง
        return Course.objects.get(code=code)
    return course


@transaction.atomic
def add_course_to_batch(*, batch, code, name_en="", name_th=None):
    """ผูกวิชาเข้ารุ่น

    ถ้ารหัสวิชานี้มีในระบบแล้ว ใช้วิชาเดิม (ไม่สร้างซ้ำ ไม่แก้ชื่อเดิม) เพื่อให้ทุกรุ่น
    ชี้ไปที่วิชาเดียวกัน (3NF) ถ้ายังไม่มีจึงสร้างใหม่ ซึ่งต้องมีชื่อภาษาอังกฤษ
    """
    # normalize แบบเดียวกับ Course.save() เพื่อใช้ค้นหาวิชาเดิม
    probe = Course(code=code or "")
    probe._normalize()
    if not probe.code:
        raise ValidationError("กรุณากรอกรหัสวิชา")

    course = _get_or_create_course(code=probe.code, name_en=name_en, name_th=name_th)

    if BatchCourse.objects.filter(batch=batch, course=course).exists():
        raise _course_in_batch_error(batch, course)
    try:
        with transaction.atomic():
            return BatchCourse.objects.create(batch=batch, course=course)
    except IntegrityError:
        raise _course_in_batch_error(batch, course)


@transaction.atomic
def remove_course_from_batch(*, batch_course):
    """ถอดวิชาออกจากรุ่น (ข้อมูลวิชาใน Course ยังอยู่ เพราะรุ่นอื่นอาจใช้ร่วมกัน)

    ถอดไม่ได้ถ้ามีชีทอัปโหลดเข้าวิชาในรุ่นนี้แล้ว (FK จาก document เป็น PROTECT)
    """
    try:
        with transaction.atomic():
            batch_course.delete()
    except ProtectedError:
        raise ValidationError(
            f"ถอดวิชา {batch_course.course.code} ออกจากรุ่น {batch_course.batch.code} "
            "ไม่ได้ เพราะมีเอกสารอัปโหลดอยู่ในวิชานี้แล้ว"
        )
