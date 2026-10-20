from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import Role, UserRole


def super_admin_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not UserRole.objects.filter(user=request.user, role__code=Role.SUPER_ADMIN).exists():
            raise PermissionDenied("เฉพาะ Super Admin เท่านั้นที่สามารถเข้าถึงได้")
        return view_func(request, *args, **kwargs)

    return _wrapped_view