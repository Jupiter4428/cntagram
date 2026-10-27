from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_http_methods

from . import selectors
from .forms import ReviewForm, SearchForm
from .models import Document
from .services import review_document


@login_required
def vault(request):
    """หน้าค้นหาเอกสารด้วยรหัสวิชา รวมผลจากทุกรุ่นในหน้าเดียว (US-7)"""
    form = SearchForm(request.GET or None)
    documents = selectors.search_documents(**form.cleaned_data) if form.is_valid() else None
    return render(request, "materials/vault.html", {"form": form, "documents": documents})


@login_required
def document_detail(request, document_id):
    """หน้าเอกสาร + preview PDF (เอกสารที่ไม่ published ตอบ 404)"""
    document = get_object_or_404(selectors.published_documents(), pk=document_id)
    return render(request, "materials/document_detail.html", {"document": document})


@login_required
@xframe_options_sameorigin  # ให้ <iframe> ในหน้าเอกสารของเว็บเราเองแสดงได้
def document_preview(request, document_id):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดแบบ inline ผ่าน view ที่ตรวจสิทธิ์ (ไม่มี Direct URL)"""
    document = get_object_or_404(selectors.published_documents(), pk=document_id)
    version = document.current_version
    # TODO(US-21): ยังไม่เช็ก version.scan_status เพราะยังไม่มีตัวสแกน (ทุกไฟล์ค้างที่ pending)
    # เมื่อ US-21 มาถึง ต้องไม่ส่งไฟล์ที่ infected และตรวจว่าเป็น PDF จริงก่อนตอบ application/pdf
    if version is None:
        raise Http404("ยังไม่มีไฟล์ของเอกสารนี้")
    try:
        file = default_storage.open(version.storage_path, "rb")
    except OSError:  # ไม่พบไฟล์ หรือ path ใช้เปิดไม่ได้ ตอบ 404 แทน 500
        raise Http404("ไม่พบไฟล์ของเอกสารนี้")
    return FileResponse(
        file, content_type="application/pdf", filename=version.original_name
    )


@login_required
@require_GET
def approval_queue(request):
    """Display pending documents waiting for review by the moderator (US-6)."""
    if not selectors.can_review_any(user=request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    documents = selectors.pending_documents_for_moderator(user=request.user)
    return render(request, "materials/approval_queue.html", {"documents": documents})


@login_required
@require_http_methods(["GET", "POST"])
def approval_review(request, document_id):
    """Review a single document submission (approve/reject) (US-6)."""
    if not selectors.can_review_any(user=request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    try:
        document = selectors.get_document_for_review(document_id=document_id, user=request.user)
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ หรือคุณไม่มีสิทธิ์เข้าถึง")

    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            review_document(
                document=document,
                approver=request.user,
                decision=form.cleaned_data["decision"],
                reason=form.cleaned_data.get("reason"),
            )
        except ValidationError as err:
            form.add_error(None, err)
        else:
            messages.success(request, f"บันทึกผลการพิจารณาเอกสาร '{document.title}' เรียบร้อยแล้ว")
            return redirect("materials:approval_queue")

    return render(
        request, "materials/approval_review.html", {"document": document, "form": form}
    )
