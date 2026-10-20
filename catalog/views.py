from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import super_admin_required
from .forms import DepartmentForm
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