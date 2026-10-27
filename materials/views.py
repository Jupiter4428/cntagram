from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_http_methods

from catalog.models import Batch

from . import selectors
from .approval_ui import attach_approval_ui
from .forms import ReviewForm, SearchForm, UploadForm
from .models import Document, max_upload_mb
from .services import ensure_can_upload_to, review_document, upload_document


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


def _inline_pdf_response(document):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดของเอกสารแบบ inline (ไม่มี Direct URL) ผู้เรียกต้องตรวจสิทธิ์มาก่อนแล้ว"""
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
@xframe_options_sameorigin  # ให้ <iframe> ในหน้าเอกสารของเว็บเราเองแสดงได้
def document_preview(request, document_id):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดของเอกสาร published แบบ inline ผ่าน view ที่ตรวจสิทธิ์"""
    document = get_object_or_404(selectors.published_documents(), pk=document_id)
    return _inline_pdf_response(document)


@login_required
@xframe_options_sameorigin  # ให้ <iframe> ในหน้าพิจารณาของเว็บเราเองแสดงได้
def approval_document_preview(request, document_id):
    """ส่งไฟล์ PDF ของเอกสารที่รอพิจารณา (pending) ให้ผู้ตรวจที่มีสิทธิ์เท่านั้น (US-6, #100)

    สิทธิ์และสถานะตัดสินที่ selectors.get_document_for_review: ผู้ใช้ทั่วไป, Moderator ภาคอื่น,
    ผู้อัปโหลดเอง, เอกสารที่ไม่ใช่ pending หรือที่ตนพิจารณาไปแล้ว ตอบ 404 เหมือนกันหมด
    จึงไม่เปิดเผยว่ามีเอกสารนั้นอยู่ (ใช้ document_preview ไม่ได้ เพราะรับเฉพาะ published)
    """
    try:
        document = selectors.get_document_for_review(document_id=document_id, user=request.user)
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ หรือคุณไม่มีสิทธิ์เข้าถึง")
    return _inline_pdf_response(document)


def _add_service_errors(form, exc):
    """error ของ service ที่ key ไม่ตรงช่องในฟอร์ม (เช่น size_bytes จาก model) แสดงเป็น non-field"""
    if not hasattr(exc, "error_dict"):
        form.add_error(None, exc)
        return
    for field, errors in exc.message_dict.items():
        form.add_error(field if field in form.fields else None, errors)


@login_required
@require_GET
def approval_queue(request):
    """Display pending documents waiting for review by the moderator (US-6)."""
    if not selectors.can_review_any(user=request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    documents = attach_approval_ui(
        selectors.pending_documents_for_moderator(user=request.user), request.user
    )
    return render(request, "materials/approval_queue.html", {"documents": documents})


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
            "batches": selectors.upload_batches(department=department),
            "max_upload_mb": max_upload_mb(),
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
        for bc in selectors.upload_batch_courses(batch=batch)
    ]
    return JsonResponse({"courses": courses})


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

    attach_approval_ui([document], request.user)
    form = ReviewForm(request.POST or None)
    status = 200
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
        except PermissionDenied as err:
            # บอกเหตุผลบนฟอร์ม (เช่น ข้อสอบรุ่นเก่าให้ Super Admin เท่านั้น) แต่ยังตอบ 403
            form.add_error(None, str(err))
            status = 403
        else:
            messages.success(request, f"บันทึกผลการพิจารณาเอกสาร '{document.title}' เรียบร้อยแล้ว")
            return redirect("materials:approval_queue")

    return render(
        request,
        "materials/approval_review.html",
        {"document": document, "form": form},
        status=status,
    )
