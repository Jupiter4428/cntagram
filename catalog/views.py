from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from portal.permissions import super_admin_required
from .forms import BatchCourseForm, BatchForm, CourseForm, DepartmentForm
from .models import Batch, BatchCourse
from . import selectors, services


@super_admin_required
def department_list(request):
    departments = selectors.department_list()
    return render(request, "catalog/department_list.html", {"departments": departments})


@super_admin_required
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"เพิ่มภาควิชา {dept.code} สำเร็จแล้ว")
            return redirect("catalog:department_list")
    else:
        form = DepartmentForm()
    return render(request, "catalog/department_form.html", {"form": form, "title": "เพิ่มภาควิชา"})


@super_admin_required
def department_update(request, pk):
    dept = get_object_or_404(selectors.department_list(), pk=pk)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"แก้ไขภาควิชา {dept.code} สำเร็จแล้ว")
            return redirect("catalog:department_list")
    else:
        form = DepartmentForm(instance=dept)
    return render(request, "catalog/department_form.html", {"form": form, "title": "แก้ไขภาควิชา", "dept": dept})


@super_admin_required
def department_delete(request, pk):
    dept = get_object_or_404(selectors.department_list(), pk=pk)
    if request.method == "POST":
        code = dept.code
        try:
            services.delete_department(department=dept)
        except ValidationError as e:
            messages.error(request, e.message)
        else:
            messages.success(request, f"ลบภาควิชา {code} สำเร็จแล้ว")
        return redirect("catalog:department_list")
    return render(request, "catalog/department_confirm_delete.html", {"dept": dept})


@super_admin_required
def batch_list(request):
    batches = selectors.batch_list()
    return render(request, "catalog/batch_list.html", {"batches": batches})


@super_admin_required
def batch_create(request):
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"เพิ่มรุ่น {batch.code} สำเร็จแล้ว")
            return redirect("catalog:batch_list")
    else:
        form = BatchForm()
    return render(request, "catalog/batch_form.html", {"form": form})


@super_admin_required
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == "POST":
        code = batch.code
        try:
            services.delete_batch(batch=batch)
        except ValidationError as e:
            messages.error(request, e.message)
        else:
            messages.success(request, f"ลบรุ่น {code} สำเร็จแล้ว")
        return redirect("catalog:batch_list")
    return render(request, "catalog/batch_confirm_delete.html", {"batch": batch})


@super_admin_required
def batch_course_manage(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == "POST":
        form = BatchCourseForm(request.POST, batch=batch)
        if form.is_valid():
            batch_course = form.save()
            messages.success(request, f"เพิ่มวิชา {batch_course.course.code} เข้ารุ่น {batch.code} สำเร็จแล้ว")
            return redirect("catalog:batch_course_manage", pk=batch.pk)
    else:
        form = BatchCourseForm(batch=batch)
    batch_courses = selectors.batch_course_list(batch=batch)
    return render(
        request,
        "catalog/batch_course_manage.html",
        {"batch": batch, "batch_courses": batch_courses, "form": form},
    )


@super_admin_required
@require_POST
def batch_course_remove(request, pk, batch_course_pk):
    batch_course = get_object_or_404(BatchCourse, pk=batch_course_pk, batch_id=pk)
    code = batch_course.course.code
    try:
        services.remove_course_from_batch(batch_course=batch_course)
    except ValidationError as e:
        messages.error(request, e.message)
    else:
        messages.success(request, f"ถอดวิชา {code} ออกจากรุ่นสำเร็จแล้ว")
    return redirect("catalog:batch_course_manage", pk=pk)


@super_admin_required
def course_list(request):
    courses = selectors.course_list()
    return render(request, "catalog/course_list.html", {"courses": courses})


@super_admin_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"เพิ่มวิชา {course.code} สำเร็จแล้ว")
            return redirect("catalog:course_list")
    else:
        form = CourseForm()
    return render(request, "catalog/course_form.html", {"form": form})
