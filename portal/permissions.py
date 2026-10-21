from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

# อยู่ใน portal ไม่ import app ใด เพื่อให้ทุก app (รวม catalog) เรียกใช้ได้โดยไม่ขัด ADR 0001
SUPER_ADMIN = "super_admin"


def is_super_admin(user):
    return user.is_authenticated and user.user_roles.filter(role__code=SUPER_ADMIN).exists()


def super_admin_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_super_admin(request.user):
            raise PermissionDenied("เฉพาะ Super Admin เท่านั้นที่สามารถเข้าถึงได้")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
