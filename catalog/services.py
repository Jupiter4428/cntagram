from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError

from .models import Batch


def _protected_message(error):
    # ตรวจสอบว่าสิ่งที่ติด FK PROTECT มี Batch (รุ่น) อยู่หรือไม่
    if any(isinstance(obj, Batch) for obj in error.protected_objects):
        return "ลบไม่ได้ เพราะยังมีรุ่น/วิชาอยู่ในภาคนี้"
    return "ลบไม่ได้ เพราะยังมีผู้ใช้สังกัดภาคนี้อยู่"


def delete_department(*, department):
    try:
        department.delete()
    except ProtectedError as e:
        raise ValidationError(_protected_message(e)) from e


@transaction.atomic
def delete_batch(*, batch):
    try:
        batch.delete()
    except ProtectedError as e:
        raise ValidationError(f"ลบรุ่น {batch.code} ไม่ได้ เพราะยังมีรายวิชาอยู่ในรุ่นนี้") from e


@transaction.atomic
def remove_course_from_batch(*, batch_course):
    # ลบแค่การผูก ข้อมูลวิชายังอยู่ให้รุ่นอื่นใช้ต่อ
    try:
        batch_course.delete()
    except ProtectedError as e:
        raise ValidationError(
            f"ถอดวิชา {batch_course.course.code} ไม่ได้ เพราะมีเอกสารอัปโหลดอยู่ในวิชานี้แล้ว"
        ) from e
