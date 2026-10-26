from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from catalog.models import Batch

from .forms import UploadForm
from .models import MAX_UPLOAD_BYTES
from .selectors import upload_batch_courses, upload_batches
from .services import ensure_can_upload_to, upload_document


@login_required
def vault(request):
    """Protected entry point for the document vault."""
    return render(request, "materials/vault.html")


def _add_service_errors(form, exc):
    """error ของ service ที่ key ไม่ตรงช่องในฟอร์ม (เช่น size_bytes จาก model) แสดงเป็น non-field"""
    if not hasattr(exc, "error_dict"):
        form.add_error(None, exc)
        return
    for field, errors in exc.message_dict.items():
        form.add_error(field if field in form.fields else None, errors)


@login_required
@require_http_methods(["GET", "POST"])
def upload(request):
    """ฟอร์มอัปโหลดชีท (US-5) ภาควิชาล็อกตามสังกัดของผู้ใช้

    PermissionDenied จาก service (แก้ request ข้ามภาค) ปล่อยให้ Django ตอบ 403
    """
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = {k: v for k, v in form.cleaned_data.items() if k != "disclaimer"}
        try:
            upload_document(uploader=request.user, **data)
        except ValidationError as exc:
            _add_service_errors(form, exc)
        else:
            return redirect("materials:upload_done")
    department = request.user.department
    return render(
        request,
        "materials/upload.html",
        {
            "form": form,
            "department": department,
            "batches": upload_batches(department=department),
            # เพดานของ DB (ไม่ query เพิ่ม) ใช้เช็กเบื้องต้นฝั่งหน้าจอ ค่าจริงตาม system_setting server เช็กซ้ำเสมอ
            "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        },
    )


@login_required
@require_GET
def upload_done(request):
    return render(request, "materials/upload_done.html")


@login_required
@require_GET
def upload_course_options(request, batch_id):
    """JSON วิชาในรุ่น ให้ dropdown ต่อเนื่องของฟอร์มอัปโหลด (เฉพาะรุ่นในภาคของตัวเอง)"""
    batch = get_object_or_404(Batch, pk=batch_id)
    ensure_can_upload_to(user=request.user, batch=batch)
    courses = [
        {"id": bc.pk, "code": bc.course.code, "name": bc.course.display_name}
        for bc in upload_batch_courses(batch=batch)
    ]
    return JsonResponse({"courses": courses})
