from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import Document, DocType, DocumentVersion, ExamDetail, ExamPeriod


@admin.register(DocType)
class DocTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name_th", "vault"]


@admin.register(ExamPeriod)
class ExamPeriodAdmin(admin.ModelAdmin):
    list_display = ["code", "name_th"]


class ExamDetailFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        # หน้าเพิ่ม document ยังไม่มี pk ExamDetail.clean() จึงเช็กคลังไม่ได้ ต้องเช็กที่นี่
        doc_type = self.instance.doc_type if self.instance.doc_type_id else None
        has_detail = any(
            form.cleaned_data and not form.cleaned_data.get("DELETE")
            for form in self.forms
        )
        if has_detail and doc_type and doc_type.vault != DocType.Vault.EXAM:
            raise ValidationError("exam_detail is only allowed for exam documents")


class ExamDetailInline(admin.StackedInline):
    model = ExamDetail
    formset = ExamDetailFormSet


class DocumentVersionInline(admin.TabularInline):
    """ดูได้อย่างเดียว ไฟล์ต้องเข้าทางหน้าอัปโหลดซึ่งตรวจไฟล์และคำนวณ hash ให้"""

    model = DocumentVersion
    fields = [
        "version_no",
        "original_name",
        "size_bytes",
        "sha256",
        "scan_status",
        "storage_path",
        "uploaded_at",
    ]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "batch_course", "doc_type", "uploader", "status", "created_at"]
    list_filter = ["status", "doc_type"]
    list_select_related = [
        "batch_course__batch__department",
        "batch_course__course",
        "doc_type",
        "uploader",
    ]
    search_fields = ["title"]
    autocomplete_fields = ["batch_course", "uploader"]
    inlines = [ExamDetailInline, DocumentVersionInline]
