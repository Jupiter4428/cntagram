from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_http_methods

from portal.permissions import can_review

from .forms import ReviewForm
from .models import Document
from .selectors import get_document_for_review, pending_documents_for_moderator
from .services import review_document


@login_required
def vault(request):
    """Protected entry point for the document vault."""
    return render(request, "materials/vault.html")


@login_required
@require_GET
def approval_queue(request):
    """Display pending documents waiting for review by the moderator (US-6)."""
    if not can_review(request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    documents = pending_documents_for_moderator(user=request.user)
    return render(request, "materials/approval_queue.html", {"documents": documents})


@login_required
@require_http_methods(["GET", "POST"])
def approval_review(request, document_id):
    """Review a single document submission (approve/reject) (US-6)."""
    try:
        document = get_document_for_review(document_id=document_id, user=request.user)
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ")

    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review_document(
            document=document,
            approver=request.user,
            decision=form.cleaned_data["decision"],
            reason=form.cleaned_data.get("reason"),
        )
        messages.success(request, f"บันทึกผลการพิจารณาเอกสาร '{document.title}' เรียบร้อยแล้ว")
        return redirect("materials:approval_queue")

    return render(
        request, "materials/approval_review.html", {"document": document, "form": form}
    )


@login_required
@require_GET
@xframe_options_sameorigin
def approval_preview(request, document_id):
    """ส่ง PDF เวอร์ชันปัจจุบันแบบ inline ให้ผู้พิจารณา ฝังใน iframe ของหน้าพิจารณา (#69)

    รูปแบบเดียวกับ document_preview ของ US-7 แต่เปิดไฟล์ pending ได้ เพราะตรวจสิทธิ์ตามภาคแทน
    """
    try:
        document = get_document_for_review(document_id=document_id, user=request.user)
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ")

    version = document.current_version
    # TODO(US-21): ยังไม่เช็ก version.scan_status และยังไม่ตรวจว่าเป็น PDF จริงก่อนตอบ application/pdf
    if version is None:
        raise Http404("ยังไม่มีไฟล์ของเอกสารนี้")
    try:
        file = default_storage.open(version.storage_path, "rb")
    except OSError:  # ไม่พบไฟล์ หรือ path ใช้เปิดไม่ได้ ตอบ 404 แทน 500
        raise Http404("ไม่พบไฟล์ของเอกสารนี้")
    return FileResponse(file, content_type="application/pdf", filename=version.original_name)
