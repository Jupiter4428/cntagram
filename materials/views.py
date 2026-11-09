from django.contrib import messages
from django.contrib.auth.decorators import login_not_required, login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

import zipfile

from catalog.models import Batch
from portal.permissions import super_admin_required

from . import selectors
from .approval_ui import attach_approval_ui
from .forms import (
    BulkImportForm,
    DocumentEditForm,
    DocumentNewVersionForm,
    HideDocumentForm,
    ReviewForm,
    SearchForm,
    UploadForm,
)
from .models import Document, max_upload_mb
from .services import (
    add_document_version,
    bulk_import_documents_from_csv,
    delete_document,
    ensure_can_upload_to,
    file_too_large_message,
    hide_document,
    review_document,
    update_document_info,
    upload_document,
)


def vault(request):
    """หน้าค้นหาเอกสารด้วยรหัสวิชา รวมผลจากทุกรุ่นในหน้าเดียว (US-7)"""
    form = SearchForm(request.GET or None)
    documents = (
        selectors.search_documents(**form.cleaned_data) if form.is_valid() else None
    )
    return render(
        request, "materials/vault.html", {"form": form, "documents": documents}
    )


def document_detail(request, document_id):
    """หน้าเอกสาร + preview PDF (เอกสารที่ไม่ published ตอบ 404)"""
    document = get_object_or_404(
        selectors.published_document_with_download_count(),
        pk=document_id,
    )
    can_hide = selectors.can_hide_document(document=document, user=request.user)
    can_manage = selectors.can_edit_document(document=document, user=request.user)
    return render(
        request,
        "materials/document_detail.html",
        {
            "document": document,
            "download_count": document.download_count,
            "download_url": (
                reverse("materials:document_download", args=[document.pk])
                if document.current_version
                else None
            ),
            "can_hide": can_hide,
            "hide_form": HideDocumentForm() if can_hide else None,
            "can_manage": can_manage,
        },
    )


def open_document_pdf(document):
    """Open a document's current PDF after its caller has checked access rights."""
    version = document.current_version
    # TODO(US-21): enforce virus scan status before serving any document file.
    if version is None:
        raise Http404("Document has no file")
    try:
        stream = default_storage.open(version.storage_path, "rb")
    except (OSError, ValueError):
        raise Http404("Document file unavailable")
    return stream, version


def _pdf_response(document, *, as_attachment=False):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดของเอกสาร (ไม่มี Direct URL)

    ผู้เรียกต้องตรวจสิทธิ์มาก่อนแล้ว
    """
    file, version = open_document_pdf(document)
    response = FileResponse(
        file,
        as_attachment=as_attachment,
        content_type="application/pdf",
        filename=version.original_name,
    )
    if as_attachment:
        response["Cache-Control"] = "private, no-store"
    return response


@xframe_options_sameorigin  # ให้ <iframe> ในหน้าเอกสารของเว็บเราเองแสดงได้
def document_preview(request, document_id):
    """ส่งไฟล์ PDF เวอร์ชันล่าสุดของเอกสาร published แบบ inline

    ผ่าน view ที่ตรวจสิทธิ์
    """
    document = get_object_or_404(selectors.published_documents(), pk=document_id)
    return _pdf_response(document)


@xframe_options_sameorigin  # ให้ <iframe> ในหน้าพิจารณาของเว็บเราเองแสดงได้
def approval_document_preview(request, document_id):
    """ส่งไฟล์ PDF ของเอกสารที่รอพิจารณา (pending)
    ให้ผู้ตรวจที่มีสิทธิ์เท่านั้น (US-6, #100)

    สิทธิ์และสถานะตัดสินที่ selectors.get_document_for_review:
    ผู้ใช้ทั่วไป, Moderator ภาคอื่น,
    ผู้อัปโหลดเอง, เอกสารที่ไม่ใช่ pending หรือที่ตนพิจารณาไปแล้ว ตอบ 404 เหมือนกันหมด
    จึงไม่เปิดเผยว่ามีเอกสารนั้นอยู่
    (ใช้ document_preview ไม่ได้ เพราะรับเฉพาะ published)
    """
    try:
        document = selectors.get_document_for_review(
            document_id=document_id, user=request.user
        )
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ หรือคุณไม่มีสิทธิ์เข้าถึง")
    return _pdf_response(document)


@require_GET
def approval_document_download(request, document_id):
    """ดาวน์โหลดไฟล์ PDF ของเอกสารที่รอพิจารณา (pending)
    สำหรับผู้ตรวจที่มีสิทธิ์เท่านั้น (Moderator ประจำภาค หรือ Super Admin)
    """
    try:
        document = selectors.get_document_for_review(
            document_id=document_id, user=request.user
        )
    except Document.DoesNotExist:
        raise Http404("ไม่พบเอกสารนี้ในระบบ หรือคุณไม่มีสิทธิ์เข้าถึง")
    return _pdf_response(document, as_attachment=True)


def _add_service_errors(form, exc):
    """error ของ service ที่ key ไม่ตรงช่องในฟอร์ม
    (เช่น size_bytes จาก model) แสดงเป็น non-field
    """
    if not hasattr(exc, "error_dict"):
        form.add_error(None, exc)
        return
    for field, errors in exc.message_dict.items():
        form.add_error(field if field in form.fields else None, errors)


@require_GET
def approval_queue(request):
    """Display pending documents waiting for review by the moderator (US-6)."""
    if not selectors.can_review_any(user=request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    documents = attach_approval_ui(
        selectors.pending_documents_for_moderator(user=request.user), request.user
    )
    return render(request, "materials/approval_queue.html", {"documents": documents})


@require_http_methods(["GET", "POST"])
def upload(request):
    """ฟอร์มอัปโหลดชีท (US-5) ภาควิชาล็อกตามสังกัดของผู้ใช้

    เช็กภาคของวิชาก่อนดูผล is_valid() ให้ request ที่แก้ข้ามภาคได้ 403 เสมอ
    แม้ช่องอื่นจะผิดด้วย (cleaned_data มีช่องที่ผ่านแล้วแม้ฟอร์มรวมไม่ผ่าน)
    """
    form = UploadForm(request.POST or None, request.FILES or None)
    if getattr(
        request, "upload_too_large", False
    ):  # MaxSizeUploadHandler ข้ามไฟล์ไปแล้ว
        form.fields["file"].error_messages["required"] = file_too_large_message()
    is_valid = request.method == "POST" and form.is_valid()
    batch_course = form.cleaned_data.get("batch_course") if form.is_bound else None
    if batch_course:
        ensure_can_upload_to(user=request.user, batch=batch_course.batch)
    if is_valid:
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


@require_GET
def upload_done(request):
    """หน้าหลังอัปโหลดสำเร็จ แจ้งว่าเอกสารรออนุมัติ (US-5)"""
    return render(request, "materials/upload_done.html")


@require_GET
def upload_course_options(request, batch_id):
    """JSON วิชาในรุ่น ให้ dropdown ต่อเนื่องของฟอร์มอัปโหลด
    (เฉพาะรุ่นในภาคของตัวเอง)
    """
    batch = get_object_or_404(Batch, pk=batch_id)
    ensure_can_upload_to(user=request.user, batch=batch)
    courses = [
        {"id": bc.pk, "code": bc.course.code, "name": bc.course.display_name}
        for bc in selectors.upload_batch_courses(batch=batch)
    ]
    return JsonResponse({"courses": courses})


@require_http_methods(["GET", "POST"])
def approval_review(request, document_id):
    """Review a single document submission (approve/reject) (US-6)."""
    if not selectors.can_review_any(user=request.user):
        raise PermissionDenied("เฉพาะผู้ดูแลเท่านั้นที่สามารถเข้าถึงได้")

    try:
        document = selectors.get_document_for_review(
            document_id=document_id, user=request.user
        )
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
            # บอกเหตุผลบนฟอร์ม (เช่น ข้อสอบรุ่นเก่าให้ Super Admin เท่านั้น)
            # แต่ยังตอบ 403
            form.add_error(None, str(err))
            status = 403
        else:
            messages.success(
                request, f"บันทึกผลการพิจารณาเอกสาร '{document.title}' เรียบร้อยแล้ว"
            )
            return redirect("materials:approval_queue")

    return render(
        request,
        "materials/approval_review.html",
        {"document": document, "form": form},
        status=status,
    )


@require_http_methods(["GET", "POST"])
def report_document_view(request, document_id):
    from .forms import ReportForm
    from .services import report_document

    if not request.user.is_authenticated:
        raise PermissionDenied
    document = get_object_or_404(selectors.published_documents(), pk=document_id)
    form = ReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            report_document(
                document=document, reporter=request.user, **form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "ส่งรายงานเรียบร้อยแล้ว")
            return redirect("materials:document_detail", document_id=document.pk)
    return render(
        request, "materials/report_document.html", {"form": form, "document": document}
    )


@require_GET
def open_reports(request):
    from portal.permissions import can_moderate_content

    if not can_moderate_content(request.user):
        raise PermissionDenied
    return render(
        request,
        "materials/open_reports.html",
        {
            "reports": selectors.open_reports_for_reviewer(user=request.user),
            "takedowns": selectors.open_takedown_requests_for_reviewer(
                user=request.user
            ),
        },
    )


@login_not_required
@require_http_methods(["GET", "POST"])
def public_takedown(request):
    from django.conf import settings
    from . import services as materials_services
    from .forms import TakedownRequestForm
    from .services import submit_takedown_request

    if request.method == "POST":
        ip = request.META.get("REMOTE_ADDR", "")
        if materials_services.is_takedown_rate_limited(ip):
            response = render(
                request,
                "materials/public_takedown.html",
                {
                    "form": TakedownRequestForm(),
                    "rate_limited": True,
                },
                status=429,
            )
            response["Retry-After"] = str(settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS)
            return response
        materials_services.record_takedown_attempt(ip)
    form = TakedownRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        takedown = submit_takedown_request(**form.cleaned_data)
        request.session["last_takedown_reference"] = str(takedown.reference)
        return redirect("materials:takedown_submitted")
    return render(request, "materials/public_takedown.html", {"form": form})


@require_http_methods(["GET", "POST"])
@super_admin_required
def resolve_report_view(request, kind, report_id):
    from .forms import ResolveReportForm
    from .services import resolve_report

    report = selectors.get_report_for_resolution(kind=kind, report_id=report_id)
    form = ResolveReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            resolve_report(
                kind=kind, report_id=report_id, actor=request.user, **form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "บันทึกผลการตัดสินแล้ว")
            return redirect("materials:review_reports")
    return render(
        request,
        "materials/resolve_report.html",
        {
            "report": report,
            "form": form,
            "kind": kind,
        },
    )


@require_GET
@super_admin_required
def review_reports(request):
    from datetime import timedelta
    from django.utils import timezone

    status = request.GET.get("status", "open")
    reports, takedowns = selectors.review_all_reports(status=status)
    deadline = timezone.now() - timedelta(hours=72)
    return render(
        request,
        "materials/review_reports.html",
        {
            "reports": reports,
            "takedowns": takedowns,
            "deadline": deadline,
            "status": status,
        },
    )


@login_not_required
@require_GET
def takedown_submitted(request):
    reference = request.session.pop("last_takedown_reference", None)
    if not reference:
        return redirect("materials:public_takedown")
    return render(
        request, "materials/takedown_submitted.html", {"reference": reference}
    )


@require_http_methods(["POST"])
def document_hide(request, document_id):
    """ซ่อนไฟล์ที่เผยแพร่แล้วแต่มีปัญหา (US-15)"""
    document = get_object_or_404(Document, pk=document_id)
    if not selectors.can_hide_document(document=document, user=request.user):
        raise PermissionDenied("คุณไม่มีสิทธิ์ซ่อนเอกสารนี้")

    form = HideDocumentForm(request.POST)
    if not form.is_valid():
        reason_err = form.errors.get("reason")
        err_msg = reason_err[0] if reason_err else "ข้อมูลไม่ถูกต้อง"
        messages.error(request, err_msg)
        return redirect("materials:document_detail", document_id=document.pk)

    try:
        hide_document(
            document=document,
            user=request.user,
            reason=form.cleaned_data["reason"],
        )
    except ValidationError as err:
        messages.error(request, str(err))
        return redirect("materials:document_detail", document_id=document.pk)

    messages.success(request, f"ซ่อนเอกสาร '{document.title}' เรียบร้อยแล้ว")
    return redirect("materials:vault")


@super_admin_required
@require_http_methods(["GET", "POST"])
def bulk_import(request):
    """หน้าสำหรับ Super Admin นำเข้าเอกสารเดิมจำนวนมากด้วย CSV และไฟล์ ZIP (US-17)"""
    summary = None
    has_run = False
    dry_run = True

    if request.method == "POST":
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            zip_file = form.cleaned_data["zip_file"]
            dry_run = form.cleaned_data["dry_run"]

            try:
                csv_content = csv_file.read().decode("utf-8-sig")
            except Exception:
                try:
                    csv_content = csv_file.read().decode("cp874")
                except Exception as e:
                    form.add_error("csv_file", f"ไม่สามารถถอดรหัสไฟล์ CSV ได้: {e}")
                    csv_content = None

            if csv_content is not None:
                try:
                    with zipfile.ZipFile(zip_file) as zf:
                        summary = bulk_import_documents_from_csv(
                            csv_content=csv_content,
                            zip_archive=zf,
                            user=request.user,
                            dry_run=dry_run,
                        )
                        has_run = True
                except zipfile.BadZipFile:
                    form.add_error("zip_file", "ไฟล์ ZIP เสียหายหรือไม่ถูกต้อง")
                except Exception as e:
                    form.add_error(None, f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
    else:
        form = BulkImportForm()

    return render(
        request,
        "materials/bulk_import.html",
        {
            "form": form,
            "summary": summary,
            "has_run": has_run,
            "dry_run": dry_run,
        },
    )


@login_required
def document_edit(request, document_id):
    """หน้าแก้ไขชื่อและคำอธิบายเอกสารโดยเจ้าของ (US-16)"""
    document = get_object_or_404(
        Document.objects.select_related("batch_course__course", "uploader"),
        pk=document_id,
    )
    if not selectors.can_edit_document(document=document, user=request.user):
        raise PermissionDenied("คุณไม่มีสิทธิ์จัดการเอกสารนี้")

    if request.method == "POST":
        form = DocumentEditForm(request.POST)
        if form.is_valid():
            try:
                update_document_info(
                    document=document,
                    actor=request.user,
                    title=form.cleaned_data["title"],
                    description=form.cleaned_data["description"],
                )
                messages.success(request, "บันทึกการแก้ไขข้อมูลเอกสารเรียบร้อยแล้ว")
                if document.status == Document.Status.PUBLISHED:
                    return redirect(
                        "materials:document_detail",
                        document_id=document.pk,
                    )
                return redirect("accounts:home")
            except ValidationError as exc:
                for field, msg in exc.message_dict.items():
                    form.add_error(field if field in form.fields else None, msg)
    else:
        form = DocumentEditForm(
            initial={
                "title": document.title,
                "description": document.description,
            }
        )

    return render(
        request,
        "materials/document_edit.html",
        {
            "document": document,
            "form": form,
        },
    )


@login_required
def document_new_version(request, document_id):
    """หน้าส่งไฟล์ PDF เวอร์ชันใหม่ของเอกสารโดยเจ้าของ (US-16)"""
    document = get_object_or_404(
        Document.objects.select_related("batch_course__course", "uploader"),
        pk=document_id,
    )
    if not selectors.can_edit_document(document=document, user=request.user):
        raise PermissionDenied("คุณไม่มีสิทธิ์จัดการเอกสารนี้")

    if request.method == "POST":
        form = DocumentNewVersionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                add_document_version(
                    document=document,
                    actor=request.user,
                    file=form.cleaned_data["file"],
                )
                messages.success(request, "อัปโหลดเอกสารเวอร์ชันใหม่เรียบร้อยแล้ว")
                if document.status == Document.Status.PUBLISHED:
                    return redirect(
                        "materials:document_detail",
                        document_id=document.pk,
                    )
                return redirect("accounts:home")
            except ValidationError as exc:
                for field, msg in exc.message_dict.items():
                    form.add_error(field if field in form.fields else None, msg)
    else:
        form = DocumentNewVersionForm()

    return render(
        request,
        "materials/document_new_version.html",
        {
            "document": document,
            "form": form,
        },
    )


@login_required
@require_POST
def document_delete(request, document_id):
    """ลบเอกสารและไฟล์ที่เกี่ยวข้องทั้งหมดโดยเจ้าของ (US-16)"""
    document = get_object_or_404(
        Document.objects.select_related("batch_course__course", "uploader"),
        pk=document_id,
    )
    if not selectors.can_edit_document(document=document, user=request.user):
        raise PermissionDenied("คุณไม่มีสิทธิ์จัดการเอกสารนี้")

    course_code = document.batch_course.course.code
    delete_document(document=document, actor=request.user)
    messages.success(request, "ลบเอกสารเรียบร้อยแล้ว")
    return redirect(f"{reverse('materials:vault')}?course_code={course_code}")
