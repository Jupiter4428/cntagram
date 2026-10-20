from .models import Department


def department_list():
    return Department.objects.order_by("code")


def active_department_list():
    """ภาควิชาที่เปิดใช้งานอยู่ (ใช้เป็นตัวเลือกตอนสมัครสมาชิก)"""
    return Department.objects.filter(is_active=True).order_by("code")