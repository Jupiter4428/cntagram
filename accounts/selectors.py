from accounts.models import Role, UserRole


def moderator_list():
    """ดึงรายชื่อ Moderator ทั้งหมดพร้อมข้อมูลเชื่อมโยง (ป้องกัน N+1 Queries)"""
    return (
        UserRole.objects.filter(role__code=Role.MODERATOR)
        .select_related("user", "granted_by")
        .order_by("department__code", "user__email")
    )


def is_moderator_of_department(*, user, department):
    """ตรวจสอบว่าผู้ใช้เป็น Moderator ประจำภาควิชานั้นหรือไม่"""
    if not user or not user.is_authenticated:
        return False
    return UserRole.objects.filter(
        user=user,
        role__code=Role.MODERATOR,
        department=department,
    ).exists()