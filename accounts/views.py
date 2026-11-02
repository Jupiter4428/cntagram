from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from portal.permissions import is_super_admin, super_admin_required

from . import selectors, services
from .forms import LoginForm, ModeratorAssignmentForm, RegisterForm
from .models import Role, UserRole
from .services import attempt_login


def _client_ip(request):
    """Return the direct peer address without trusting spoofable proxy headers."""
    return request.META.get("REMOTE_ADDR", "")


def _safe_login_redirect(request, next_url=""):
    """Return an internal `next` target, or the configured home page."""
    redirect_to = next_url or request.GET.get("next")
    if redirect_to and url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect_to
    return resolve_url(settings.LOGIN_REDIRECT_URL)


@require_GET
def home(request):
    """Public landing page; Super Admins get their own admin index."""
    if is_super_admin(request.user):
        dashboard = selectors.admin_dashboard(page=request.GET.get("page"))
        return render(request, "accounts/index_admin.html", {"dashboard": dashboard})
    return render(request, "accounts/index.html")


@require_http_methods(["GET", "POST"])
def register(request):
    """Register a new student account with a faculty email (US-1)."""
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        client_ip = _client_ip(request)
        if services.is_register_rate_limited(client_ip):
            response = render(request, "accounts/register.html", {
                "form": RegisterForm(), "rate_limited": True,
            }, status=429)
            response["Retry-After"] = str(settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS)
            return response
        services.record_register_attempt(client_ip)

    form = RegisterForm(request.POST if request.method == "POST" else None)
    if form.is_bound and form.is_valid():
        data = form.cleaned_data
        try:
            services.register_user(
                email=data["email"],
                password=data["password"],
                nickname=data["nickname"],
                department=data["department"],
                pdpa_consent_at=timezone.now(),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ")
            return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login(request):
    """Authenticate a user while throttling repeated failures."""
    if request.user.is_authenticated:
        return redirect(_safe_login_redirect(request))

    next_url = request.POST.get("next") or request.GET.get("next", "")
    form = LoginForm(
        data=request.POST if request.method == "POST" else None,
        initial={"next": next_url},
    )
    status = 200
    retry_after = None

    if request.method == "POST":
        client_ip = _client_ip(request)
        identifier = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        attempt = services.attempt_login(
            identifier=identifier,
            password=password,
            client_ip=client_ip,
        )
        if attempt.user:
            auth_login(request, attempt.user)
            return redirect(_safe_login_redirect(request, next_url))
        elif attempt.rate_limited:
            form.add_error(
                None,
                "ลองเข้าสู่ระบบหลายครั้งเกินไป กรุณารอสักครู่แล้วลองอีกครั้ง (Too many failed login attempts)",
            )
            status = 429
            retry_after = str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        elif form.is_valid():
            form.add_error(
                None,
                "Please enter a correct email and password. Note that both fields may be case-sensitive.",
            )

    response = render(
        request,
        "accounts/login.html",
        {"form": form, "next": next_url},
        status=status,
    )
    if retry_after:
        response["Retry-After"] = retry_after
    return response


@require_POST
def logout(request):
    """End the current session; CSRF middleware protects this POST endpoint."""
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


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
