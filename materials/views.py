from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from accounts.models import Role, UserRole

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
    is_authorized = request.user.is_superuser or UserRole.objects.filter(
        user=request.user, role__code__in=[Role.MODERATOR, Role.SUPER_ADMIN]
    ).exists()
    if not is_authorized:
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
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            review_document(
                document=document,
                approver=request.user,
                decision=form.cleaned_data["decision"],
                reason=form.cleaned_data.get("reason"),
            )
        except ValidationError as e:
            form.add_error(None, e)
        except PermissionDenied as e:
            # บอกเหตุผลบนฟอร์ม (เช่น ข้อสอบรุ่นเก่าให้ Super Admin เท่านั้น) แต่ยังตอบ 403
            form.add_error(None, str(e))
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
