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


def home(request):
    return render(request, "base.html")


def login(request):
    if request.user.is_authenticated:
        return redirect("accounts:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("accounts:home")
    return render(request, "accounts/login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("accounts:home")


def register(request):
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