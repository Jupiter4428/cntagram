"""หน้าจัดการรุ่นและวิชาในรุ่น (US-4) เฉพาะ Super Admin"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Role

from .forms import BatchCourseForm, BatchForm
from .models import Batch, BatchCourse, Department
from .selectors import batch_course_list, batch_list
from .services import (
    add_course_to_batch,
    create_batch,
    delete_batch,
    remove_course_from_batch,
)


def is_super_admin(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.user_roles.filter(role__code=Role.SUPER_ADMIN).exists()
    )


def super_admin_required(view_func):
    """guest ไปหน้า login, ผู้ใช้ที่ไม่ใช่ Super Admin ได้ 403"""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_super_admin(request.user):
            raise PermissionDenied("เฉพาะ Super Admin เท่านั้น")
        return view_func(request, *args, **kwargs)

    return wrapped


@super_admin_required
def batch_manage(request, department_code):
    """รายการรุ่นของภาค + ฟอร์มเพิ่มรุ่น"""
    department = get_object_or_404(Department, code=department_code.upper())
    form = BatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            batch = create_batch(department=department, number=form.cleaned_data["number"])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"เพิ่มรุ่น {batch.code} แล้ว")
            return redirect("catalog:batch_manage", department_code=department.code)
    return render(
        request,
        "catalog/batch_manage.html",
        {
            "department": department,
            "departments": Department.objects.filter(is_active=True),
            "batches": batch_list(department=department),
            "form": form,
        },
    )


@super_admin_required
@require_POST
def batch_delete(request, batch_id):
    batch = get_object_or_404(Batch, pk=batch_id)
    try:
        delete_batch(batch=batch)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, f"ลบรุ่น {batch.code} แล้ว")
    return redirect("catalog:batch_manage", department_code=batch.department.code)


@super_admin_required
def batch_course_manage(request, batch_id):
    """วิชาในรุ่น + ฟอร์มเพิ่มวิชา"""
    batch = get_object_or_404(Batch, pk=batch_id)
    form = BatchCourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            batch_course = add_course_to_batch(batch=batch, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"เพิ่มวิชา {batch_course.course.code} แล้ว")
            return redirect("catalog:batch_course_manage", batch_id=batch.pk)
    return render(
        request,
        "catalog/batch_course_manage.html",
        {"batch": batch, "batch_courses": batch_course_list(batch=batch), "form": form},
    )


@super_admin_required
@require_POST
def batch_course_remove(request, batch_course_id):
    batch_course = get_object_or_404(BatchCourse, pk=batch_course_id)
    try:
        remove_course_from_batch(batch_course=batch_course)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    else:
        messages.success(request, f"ถอดวิชา {batch_course.course.code} แล้ว")
    return redirect("catalog:batch_course_manage", batch_id=batch_course.batch_id)
