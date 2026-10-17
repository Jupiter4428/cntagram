# Create your views here.
# catalog/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from accounts.permissions import super_admin_required
from .models import Department
from .forms import DepartmentForm

@super_admin_required
def department_list(request):
    """แสดงรายการภาควิชาทั้งหมด"""
    departments = Department.objects.all()
    return render(request, "catalog/department_list.html", {"departments": departments})

@super_admin_required
def department_create(request):
    """เพิ่มภาควิชาใหม่"""
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
    """แก้ไขข้อมูลภาควิชา"""
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f"แก้ไขภาควิชา {dept.code} สำเร็จแล้ว")
            return redirect("catalog:department_list")
    else:
        form = DepartmentForm(instance=dept)
    return render(request, "catalog/department_form.html", {"form": form, "title": "แก้ไขภาควิชา", "dept": dept})

@super_admin_required
def department_delete(request, pk):
    """ลบภาควิชา พร้อมดักจับ ProtectedError ตามเงื่อนไข PROTECT"""
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        try:
            code = dept.code
            dept.delete()
            messages.success(request, f"ลบภาควิชา {code} สำเร็จแล้ว")
        except ProtectedError:
            # แจ้งเตือนภาษาไทยตามตัวอย่างใน Acceptance Criteria
            messages.error(request, "ลบไม่ได้ เพราะยังมีรุ่น/วิชาอยู่ในภาคนี้")
        return redirect("catalog:department_list")
    return render(request, "catalog/department_confirm_delete.html", {"dept": dept})