import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_not_required, login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from portal.permissions import is_super_admin, super_admin_required

from . import selectors, services
from .forms import (
    AvatarUploadForm,
    DeleteAccountForm,
    LoginForm,
    ModeratorAssignmentForm,
    PollVoteForm,
    RegisterForm,
    ShoutboxForm,
)
from .models import PollVote, Role, UserRole

User = get_user_model()


def _client_ip(request):
    """Return the direct peer address without trusting spoofable proxy headers.

    Security Note (Refs #42 / #47):
    Do NOT read raw X-Forwarded-For headers from the client directly because clients
    can easily spoof them. When deploying behind a reverse proxy (e.g. Nginx,
    Cloudflare), configure the proxy to rewrite REMOTE_ADDR with the verified client IP
    (e.g. Nginx set_real_ip_from / real_ip_header, or trusted ProxyFix middleware).
    """
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


@login_not_required
@require_GET
def home(request):
    """Public landing page; Super Admins get their own admin index."""
    if is_super_admin(request.user):
        dashboard = selectors.admin_dashboard(page=request.GET.get("page"))
        return render(request, "accounts/index_admin.html", {"dashboard": dashboard})

    has_visited = bool(request.COOKIES.get("has_visited_home"))
    if not has_visited:
        visitor_digits = services.record_home_visit()
    else:
        visitor_digits = services.get_home_visit_count()

    poll = selectors.get_weekly_poll()
    has_voted = (
        request.user.is_authenticated
        and PollVote.objects.filter(user=request.user).exists()
    )
    show_form = not has_voted  # A query parameter must never re-enable voting.

    # UI Prototype variants (Refs .claude/skills/prototype/UI.md)
    variant = request.GET.get("variant", "A").upper()
    variant_labels = {
        "A": "A",
        "B": "B",
        "C": "C",
    }
    if variant not in variant_labels:
        variant = "A"

    variants_order = ["A", "B", "C"]
    curr_idx = variants_order.index(variant)
    prev_variant = variants_order[(curr_idx - 1) % len(variants_order)]
    next_variant = variants_order[(curr_idx + 1) % len(variants_order)]

    response = render(
        request,
        "accounts/index.html",
        {
            "visitor_digits": visitor_digits,
            "poll": poll,
            "has_voted_poll": has_voted,
            "show_poll_form": show_form,
            "shoutbox_messages": selectors.get_shoutbox_messages(),
            "variant": variant,
            "current_variant_label": variant_labels[variant],
            "prev_variant": prev_variant,
            "next_variant": next_variant,
        },
    )
    if not has_visited:
        response.set_cookie("has_visited_home", "1", httponly=True, samesite="Lax")
    return response


@login_required
@require_POST
def poll_vote(request):
    """Validate the choice and enforce one durable vote per account."""
    form = PollVoteForm(request.POST)
    success = False
    if form.is_valid():
        success, poll = services.record_poll_vote(
            user=request.user, choice_key=form.cleaned_data["choice"]
        )
    else:
        poll = selectors.get_weekly_poll()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "includes/_poll_results.html", {"poll": poll}, request=request
        )
        return JsonResponse(
            {
                "ok": success,
                "poll": poll,
                "html": html,
                "has_voted": PollVote.objects.filter(user=request.user).exists(),
            },
            status=200 if success else 400,
        )
    return redirect("accounts:home")


@login_required
@require_POST
def shoutbox_post(request):
    """Validate community shoutbox posts through a Django form."""
    form = ShoutboxForm(request.POST)
    success = form.is_valid()
    if success:
        services.add_shoutbox_message(
            user=request.user, text=form.cleaned_data["message"]
        )
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": success,
                "messages": selectors.get_shoutbox_messages(),
            },
            status=200 if success else 400,
        )
    return redirect("accounts:home")


@login_not_required
@require_http_methods(["GET", "POST"])
def register(request):
    """Register a new student account with a faculty email (US-1)."""
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        client_ip = _client_ip(request)
        if services.is_register_rate_limited(client_ip):
            response = render(
                request,
                "accounts/register.html",
                {
                    "form": RegisterForm(),
                    "rate_limited": True,
                },
                status=429,
            )
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


def _login_response(request, form, *, retry_after=None):
    response = render(
        request,
        "accounts/login.html",
        {"form": form},
        status=429 if retry_after else 200,
    )
    if retry_after:
        response["Retry-After"] = retry_after
    return response


@login_not_required
@require_http_methods(["GET", "POST"])
def login(request):
    """Authenticate a user while throttling repeated failures."""
    if request.user.is_authenticated:
        return redirect(_safe_login_redirect(request))

    form = LoginForm(
        data=request.POST if request.method == "POST" else None,
        initial={"next": request.GET.get("next", "")},
    )

    # Throttle only counts submissions that pass form validation;
    # invalid forms never reach authenticate().
    if request.method == "POST" and form.is_valid():
        attempt = services.attempt_login(
            identifier=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
            client_ip=_client_ip(request),
        )
        if attempt.user:
            auth_login(request, attempt.user)
            return redirect(
                _safe_login_redirect(request, form.cleaned_data.get("next", ""))
            )
        if attempt.rate_limited:
            form.add_error(
                None, "ลองเข้าสู่ระบบหลายครั้งเกินไป กรุณารอสักครู่แล้วลองอีกครั้ง"
            )
            return _login_response(
                request, form, retry_after=str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
            )
        form.add_error(None, form.get_invalid_login_error())

    return _login_response(request, form)


@login_not_required
@require_POST
def logout(request):
    """End the current session; CSRF middleware protects this POST endpoint."""
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """ผู้ใช้ขอลบบัญชีตัวเองตาม PDPA หลังยืนยันรหัสผ่านแล้วออกจากระบบ (US-13)"""
    if services.is_delete_account_rate_limited(user_id=request.user.pk):
        response = render(
            request,
            "accounts/delete_account.html",
            {"form": DeleteAccountForm(), "rate_limited": True},
            status=429,
        )
        response["Retry-After"] = str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        return response

    form = DeleteAccountForm(request.POST or None)
    if form.is_bound and form.is_valid():
        try:
            services.delete_own_account(
                user=request.user, password=form.cleaned_data["password"]
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict") and "password" in exc.message_dict:
                services.record_delete_account_failure(user_id=request.user.pk)
                if services.is_delete_account_rate_limited(user_id=request.user.pk):
                    response = render(
                        request,
                        "accounts/delete_account.html",
                        {"form": form, "rate_limited": True},
                        status=429,
                    )
                    response["Retry-After"] = str(
                        settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
                    )
                    return response
            form.add_error(None, exc)
        else:
            services.clear_delete_account_failures(user_id=request.user.pk)
            auth_logout(request)
            messages.success(request, "ลบบัญชีของคุณเรียบร้อยแล้ว")
            return redirect("accounts:home")
    return render(request, "accounts/delete_account.html", {"form": form})


@super_admin_required
@require_http_methods(["GET", "POST"])
def moderator_manage(request):
    """หน้าแต่งตั้งและแสดงรายชื่อ Moderator (เฉพาะ Super Admin)"""
    form = ModeratorAssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user, dept = form.cleaned_data["user"], form.cleaned_data["department"]
        try:
            services.assign_moderator(
                user=user, department=dept, granted_by=request.user
            )
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
        else:
            messages.success(
                request,
                f"แต่งตั้ง {user.email} เป็น Moderator ภาควิชา {dept.code} สำเร็จแล้ว",
            )
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
    messages.success(
        request,
        f"ถอดถอน {user_email} จากการเป็น Moderator ภาควิชา {dept_code} สำเร็จแล้ว",
    )
    return redirect("accounts:moderator_manage")


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    """หน้าจัดการข้อมูลส่วนตัวและอัปโหลดรูปโปรไฟล์."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            services.delete_user_avatar(user=request.user)
            messages.success(request, "ลบรูปโปรไฟล์เรียบร้อยแล้ว")
            return redirect("accounts:profile")

        form = AvatarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                services.update_user_avatar(
                    user=request.user, file=form.cleaned_data["avatar"]
                )
            except ValidationError as exc:
                form.add_error("avatar", exc)
            else:
                messages.success(request, "อัปเดตรูปโปรไฟล์เรียบร้อยแล้ว")
                return redirect("accounts:profile")
    else:
        form = AvatarUploadForm()

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "user": request.user,
        },
    )


@login_required
@require_GET
def user_avatar(request, user_id):
    """เสิร์ฟรูปภาพโปรไฟล์ของผู้ใช้ผ่าน storage โดยตรง (ADR 0003)."""
    user = get_object_or_404(User, pk=user_id, is_active=True)
    if not user.avatar or not default_storage.exists(user.avatar):
        raise Http404("Avatar not found")

    content_type, _ = mimetypes.guess_type(user.avatar)
    if not content_type:
        content_type = "image/jpeg"

    file_stream = default_storage.open(user.avatar, "rb")
    response = FileResponse(file_stream, content_type=content_type)
    response["Cache-Control"] = "private, no-cache"
    return response
