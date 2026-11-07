"""Template tag ให้ app อื่นแสดงตัวเลขของ materials.

แสดงผลได้โดยไม่ต้อง import materials (ADR 0001)
"""

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


@register.simple_tag
def my_documents(user):
    """ไฟล์ที่ผู้ใช้อัปโหลด ใช้กับ `{% my_documents request.user as docs %}`"""
    return selectors.user_documents(user=user)


@register.simple_tag
def moderator_pending(user):
    """จำนวนไฟล์รออนุมัติของภาคที่ Moderator ดูแล.

    ใช้กับ `{% moderator_pending request.user as pending %}`
    """
    return selectors.moderator_pending_summary(user=user)


@register.simple_tag
def pending_documents_without_rules():
    """สรุปเอกสาร pending ที่ไม่มีกฎอนุมัติ ใช้เตือน Super Admin บน Dashboard."""
    return selectors.pending_documents_without_rules_summary()
