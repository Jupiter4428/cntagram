"""template tag ให้ app อื่นแสดงตัวเลขของ materials ได้โดยไม่ต้อง import materials (ADR 0001)"""
from django import template

from .. import selectors

register = template.Library()


@register.simple_tag
def uploaded_file_count():
    """จำนวนไฟล์ที่อัปโหลดทั้งหมด (ทุกเวอร์ชัน) ใช้ในการ์ดของหน้า Dashboard"""
    return selectors.uploaded_file_count()


@register.simple_tag
def monthly_uploads():
    """ไฟล์ที่อัปโหลดต่อเดือน ย้อนหลัง 6 เดือน ใช้กับ `{% monthly_uploads as rows %}`"""
    return selectors.monthly_uploads()
