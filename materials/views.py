from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.db.models import Count
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import SearchForm
from .selectors import published_documents, search_documents


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
    document = published_documents().annotate(download_count=Count("download_logs")).get(pk=document.pk)
    return render(request, "materials/document_detail.html", {
        "document": document,
        "download_count": document.download_count,
        "download_url": reverse("materials:document_download", args=[document.pk]) if document.current_version else None,
    })


@login_required
@xframe_options_sameorigin  # ให้ <iframe> ในหน้าเอกสารของเว็บเราเองแสดงได้
def document_preview(request, document_id):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดแบบ inline ผ่าน view ที่ตรวจสิทธิ์ (ไม่มี Direct URL)"""
    document = get_object_or_404(published_documents(), pk=document_id)
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
