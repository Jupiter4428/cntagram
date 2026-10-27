from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_http_methods

from catalog.models import Batch
from .forms import SearchForm, UploadForm
from .models import MAX_UPLOAD_BYTES
from .selectors import (
    published_documents,
    search_documents,
    upload_batch_courses,
    upload_batches,
)
from .services import ensure_can_upload_to, upload_document


@login_required
def vault(request):
    """หน้าค้นหาเอกสารด้วยรหัสวิชา รวมผลจากทุกรุ่นในหน้าเดียว (US-7)"""
    form = SearchForm(request.GET or None)
    documents = search_documents(**form.cleaned_data) if form.is_valid() else None
    return render(request, "materials/vault.html", {"form": form, "documents": documents})


@login_required
def document_detail(request, document_id):
    """หน้าเอกสาร + preview PDF (เอกสารที่ไม่ published ตอบ 404)"""
    document = get_object_or_404(published_documents(), pk=document_id)
    return render(request, "materials/document_detail.html", {"document": document})


@login_required
@xframe_options_sameorigin  # ให้ <iframe> ในหน้าเอกสารของเว็บเราเองแสดงได้
def document_preview(request, document_id):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดแบบ inline ผ่าน view ที่ตรวจสิทธิ์ (ไม่มี Direct URL)"""
    document = get_object_or_404(published_documents(), pk=document_id)
    version = document.current_version
    if version is None:
        raise Http404("ยังไม่มีไฟล์ของเอกสารนี้")
    try:
        file = default_storage.open(version.storage_path, "rb")
    except OSError:
        raise Http404("ไม่พบไฟล์ของเอกสารนี้")
    return FileResponse(
        file, content_type="application/pdf", filename=version.original_name
    )


@login_required
@require_http_methods(["GET", "POST"])
def upload(request):
    """หน้าฟอร์มอัปโหลดชีท (US-5)"""
    user = request.user
    department = user.department

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = upload_document(
                user=user,
                department=department,
                batch_course=form.cleaned_data["batch_course"],
                doc_type=form.cleaned_data["doc_type"],
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                file=form.cleaned_data["file"],
                exam_period=form.cleaned_data.get("exam_period"),
                exam_year_be=form.cleaned_data.get("exam_year_be"),
            )
            request.session["last_uploaded_doc_id"] = document.pk
            return redirect("materials:upload_done")
    else:
        form = UploadForm()

    return render(
        request,
        "materials/upload.html",
        {
            "form": form,
            "department": department,
            "batches": upload_batches(department=department),
            "max_upload_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        },
    )


@login_required
@require_GET
def upload_done(request):
    """หน้าแสดงผลเมื่ออัปโหลดชีทสำเร็จ"""
    return render(request, "materials/upload_done.html")


@login_required
@require_GET
def upload_course_options(request, batch_id):
    """API ดึงรายวิชาตามรุ่น"""
    user = request.user
    courses = upload_batch_courses(user=user, batch_id=batch_id)
    return JsonResponse({"courses": list(courses)})