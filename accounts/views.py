from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from portal.permissions import is_super_admin, super_admin_required
from . import selectors, services
from .forms import LoginForm, ModeratorAssignmentForm
from .models import Role, UserRole


def _client_ip(request):
    """Extract client IP from request headers or remote address."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _safe_login_redirect(request, target_url):
    """Redirect to target_url if safe, else fall back to LOGIN_REDIRECT_URL."""
    if target_url and url_has_allowed_host_and_scheme(
        target_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(target_url)
    return redirect(settings.LOGIN_REDIRECT_URL)


def _rate_limited_response(request, form):
    """Return 429 response when login attempts exceed threshold."""
    unbound_form = LoginForm(initial={"username": form.submitted_username})
    response = render(
        request,
        "accounts/login.html",
        {
            "form": unbound_form,
            "rate_limited": True,
            "retry_after_seconds": settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
            "next": request.GET.get("next") or request.POST.get("next", ""),
        },
        status=429,
    )
    response["Retry-After"] = str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    return response


@require_GET
def home(request):
    """Landing page: public for guests, personalized for authenticated users."""
    context = {"is_super_admin": is_super_admin(request.user)}
    return render(request, "accounts/home.html", context)


@require_http_methods(["GET", "POST"])
def login(request):
    """Authenticate and log in a user."""
    next_url = request.GET.get("next") or request.POST.get("next", "")
    if request.user.is_authenticated:
        return _safe_login_redirect(request, next_url)

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        attempt = services.attempt_login(form=form, client_ip=_client_ip(request))
        if attempt.rate_limited:
            return _rate_limited_response(request, form)
        if attempt.user:
            auth_login(request, attempt.user)
            return _safe_login_redirect(request, form.next_url or next_url)

    return render(request, "accounts/login.html", {"form": form, "next": next_url})


@require_POST
def logout(request):
    """Log out the current user."""
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@require_GET
def register(request):
    """Registration placeholder."""
    return render(request, "accounts/register.html")


@super_admin_required
@require_http_methods(["GET", "POST"])
def moderator_manage(request):
    """หน้าแต่งตั้งและแสดงรายชื่อ Moderator (เฉพาะ Super Admin)"""
    form = ModeratorAssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user, dept = form.cleaned_data["user"], form.cleaned_data["department"]
        try:
            services.assign_moderator(user=user, department=dept, granted_by=request.user)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
        else:
            messages.success(request, f"แต่งตั้ง {user.email} เป็น Moderator ภาควิชา {dept.code} สำเร็จแล้ว")
            return redirect("accounts:moderator_manage")
    context = {"form": form, "moderators": selectors.moderator_list()}
    return render(request, "accounts/moderator_manage.html", context)


@super_admin_required
@require_POST
def moderator_remove(request, pk):
    """ถอดถอน Moderator ออกจากภาควิชา"""
    user_role = get_object_or_404(UserRole, pk=pk, role__code=Role.MODERATOR)
    user_email = user_role.user.email
    dept_code = user_role.department.code
    services.remove_moderator(user_role=user_role)
    messages.success(request, f"ถอดถอน {user_email} จากการเป็น Moderator ภาควิชา {dept_code} สำเร็จแล้ว")
    return redirect("accounts:moderator_manage")