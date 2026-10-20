from django.core.exceptions import ValidationError
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