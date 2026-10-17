from functools import wraps
from django.core.exceptions import PermissionDenied
from accounts.models import Role, UserRole


def super_admin_required(view_func):
  """Decorator สำหรับตรวจสอบว่า User มี role เป็น super_admin หรือไม่

  ถ้าไม่ใช่ Super Admin จะ raise PermissionDenied (HTTP 403 Forbidden)
  """

  @wraps(view_func)
  def _wrapped_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
      raise PermissionDenied("กรุณาเข้าสู่ระบบ")

    # สืบค้นข้ามตาราง ForeignKey ไปยังฟิลด์ของ Role
    role_field = "code" if hasattr(Role, "code") else "name"
    filter_kwargs = {
        "user": request.user,
        f"role__{role_field}": "super_admin",
    }

    is_super_admin = UserRole.objects.filter(**filter_kwargs).exists()

    if not is_super_admin:
      raise PermissionDenied("เฉพาะ Super Admin เท่านั้นที่สามารถเข้าถึงได้")

    return view_func(request, *args, **kwargs)

  return _wrapped_view