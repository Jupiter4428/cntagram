"""ฟอร์มของ materials รับค่าอย่างเดียว การอ่าน/เขียนทำผ่าน selectors / services"""

from django import forms

from catalog.models import Batch, BatchCourse, Department

from .models import Approval, DocType, ExamPeriod


class ExamPeriodChoiceField(forms.ModelChoiceField):
    """แสดงชื่อช่วงสอบภาษาไทยในตัวกรองค้นหา"""

    def label_from_instance(self, obj):
        return obj.name_th


class SearchForm(forms.Form):
    """ค้นหาเอกสาร (GET) ด้วยรหัสวิชา + ตัวกรอง
    ภาค/รุ่น/ประเภท/ช่วงสอบ/ปี พ.ศ. (US-7, US-11)

    cleaned_data ส่งเข้า selectors.search_documents(**cleaned_data) ได้เลย
    """

    course_code = forms.CharField(
        label="รหัสวิชา",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages={
            "required": "กรุณาระบุรหัสวิชา",
            "max_length": "รหัสวิชาต้องไม่เกิน %(limit_value)d ตัวอักษร",
        },
    )
    department = forms.ModelChoiceField(
        label="ภาควิชา",
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="ทุกภาค",
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "ภาควิชาที่เลือกไม่ถูกต้อง"},
    )
    batch = forms.ModelChoiceField(
        label="รุ่น",
        queryset=Batch.objects.filter(department__is_active=True),  # ให้ตรงกับรายการภาค
        required=False,
        empty_label="ทุกรุ่น",
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "รุ่นที่เลือกไม่ถูกต้อง"},
    )
    doc_type = forms.ModelChoiceField(
        label="ประเภท",
        queryset=DocType.objects.order_by("code"),
        required=False,
        empty_label="ทุกประเภท",
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "ประเภทที่เลือกไม่ถูกต้อง"},
    )

    exam_period = ExamPeriodChoiceField(
        label="ช่วงสอบ",
        queryset=ExamPeriod.objects.order_by("pk"),
        required=False,
        empty_label="ทุกช่วงสอบ",
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "ช่วงสอบที่เลือกไม่ถูกต้อง"},
    )
    exam_year_be = forms.IntegerField(
        label="ปี พ.ศ.",
        min_value=2500,
        max_value=2700,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        error_messages={
            "min_value": "ปีต้องอยู่ในช่วง พ.ศ. 2500–2700",
            "max_value": "ปีต้องอยู่ในช่วง พ.ศ. 2500–2700",
            "invalid": "กรุณากรอกปี พ.ศ. เป็นตัวเลข",
        },
    )

    def clean(self):
        """เลือกทั้งภาคและรุ่น รุ่นต้องอยู่ในภาคนั้น (ไม่งั้นผลจะว่างโดยไม่รู้สาเหตุ)"""
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        batch = cleaned_data.get("batch")
        if department and batch and batch.department_id != department.pk:
            self.add_error(
                "batch", f"รุ่น {batch.code} ไม่ได้อยู่ในภาค {department.code}"
            )
        return cleaned_data


class UploadForm(forms.Form):
    """อัปโหลดชีท (US-5) cleaned_data ยกเว้น disclaimer
    ส่งเข้า services.upload_document ได้เลย

    batch_course รับได้ทุกภาค โดยตั้งใจ: view เช็กภาคของผู้ใช้ก่อนดูผลฟอร์ม
    และ service เช็กซ้ำ จึงตอบ 403 เมื่อมีคนแก้ request ข้ามภาค (ไม่ใช่แค่ฟอร์มไม่ผ่าน)
    """

    batch_course = forms.ModelChoiceField(
        label="วิชา",
        queryset=BatchCourse.objects.all(),
        error_messages={
            "required": "กรุณาเลือกวิชา",
            "invalid_choice": "วิชาที่เลือกไม่ถูกต้อง",
        },
    )
    doc_type = forms.ModelChoiceField(
        label="ประเภท",
        queryset=DocType.objects.order_by("code"),
        error_messages={
            "required": "กรุณาเลือกประเภทเอกสาร",
            "invalid_choice": "ประเภทเอกสารที่เลือกไม่ถูกต้อง",
        },
    )
    title = forms.CharField(
        label="ชื่อเอกสาร",
        max_length=200,
        error_messages={
            "required": "กรุณาระบุชื่อเอกสาร",
            "max_length": "ชื่อเอกสารต้องมีความยาวไม่เกิน %(limit_value)d ตัวอักษร",
        },
    )
    description = forms.CharField(
        label="รายละเอียด",
        widget=forms.Textarea,
        required=False,
    )
    exam_period = forms.ModelChoiceField(
        label="ช่วงสอบ",
        queryset=ExamPeriod.objects.all(),
        required=False,
        error_messages={
            "invalid_choice": "ช่วงสอบที่เลือกไม่ถูกต้อง",
        },
    )
    exam_year_be = forms.IntegerField(
        label="ปี พ.ศ.",
        min_value=2500,
        max_value=2700,
        required=False,
        error_messages={
            "min_value": "ปี พ.ศ. ต้องไม่น้อยกว่า %(limit_value)d",
            "max_value": "ปี พ.ศ. ต้องไม่เกิน %(limit_value)d",
            "invalid": "กรุณาระบุปี พ.ศ. เป็นตัวเลข",
        },
    )
    file = forms.FileField(
        label="ไฟล์ PDF",
        error_messages={
            "required": "กรุณาแนบไฟล์ PDF",
            "empty": "ไฟล์ที่แนบว่างเปล่า",
            "invalid": "ไฟล์ที่แนบไม่ถูกต้อง",
        },
    )
    disclaimer = forms.BooleanField(
        label="ฉันยืนยันว่าไฟล์นี้ไม่ละเมิดลิขสิทธิ์ของผู้อื่น",
        required=True,
        error_messages={
            "required": "กรุณายืนยันว่าไฟล์นี้ไม่ละเมิดลิขสิทธิ์",
        },
    )


class ReviewForm(forms.Form):
    """ฟอร์มสำหรับ Moderator พิจารณาอนุมัติหรือปฏิเสธเอกสาร (US-6)"""

    DECISION_CHOICES = (
        (Approval.Decision.APPROVED, "อนุมัติ (Approve)"),
        (Approval.Decision.REJECTED, "ปฏิเสธ (Reject)"),
    )

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label="ผลการพิจารณา",
        error_messages={"required": "กรุณาเลือกผลการพิจารณา"},
    )
    reason = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "ระบุเหตุผล (บังคับกรอกกรณีปฏิเสธ)",
            }
        ),
        required=False,
        label="เหตุผลประกอบการพิจารณา",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            self.is_bound
            and self.data.get("decision") == Approval.Decision.REJECTED
            and not (self.data.get("reason") or "").strip()
        ):
            self.fields["reason"].widget.attrs.update(
                {
                    "class": "form-control is-invalid",
                    "aria-invalid": "true",
                    "aria-describedby": "reason-errors",
                }
            )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        reason = (cleaned_data.get("reason") or "").strip()

        if decision == Approval.Decision.REJECTED and not reason:
            self.add_error("reason", "กรุณาระบุเหตุผลเมื่อปฏิเสธเอกสาร")

        cleaned_data["reason"] = reason or None
        return cleaned_data


class ReportForm(forms.Form):
    reason_type = forms.ChoiceField(
        label="ประเภทรายงาน",
        choices=__import__(
            "materials.models", fromlist=["Report"]
        ).Report.Reason.choices,
    )
    reason = forms.CharField(label="เหตุผล", max_length=2000, widget=forms.Textarea)


class TakedownRequestForm(forms.Form):
    claimant_name = forms.CharField(
        label="ชื่อผู้แจ้ง",
        max_length=200,
        error_messages={"required": "กรุณาระบุชื่อ"},
    )
    contact_email = forms.EmailField(
        label="อีเมลติดต่อ",
        error_messages={
            "required": "กรุณาระบุอีเมล",
            "invalid": "รูปแบบอีเมลไม่ถูกต้อง",
        },
    )
    content_identifier = forms.CharField(
        label="รหัสวิชา / ชื่อเอกสาร / ลิงก์",
        max_length=500,
        error_messages={"required": "กรุณาระบุเนื้อหาที่ต้องการแจ้ง"},
    )
    reason = forms.CharField(
        label="เหตุผล",
        max_length=3000,
        widget=forms.Textarea,
        error_messages={"required": "กรุณาระบุเหตุผล"},
    )
    rights_confirmed = forms.BooleanField(
        label="ข้าพเจ้ายืนยันว่าเป็นเจ้าของสิทธิ์หรือผู้รับมอบอำนาจ",
        error_messages={"required": "กรุณายืนยันสิทธิ์"},
    )


class HideDocumentForm(forms.Form):
    """ฟอร์มสำหรับ Moderator / Super Admin ซ่อนไฟล์ที่เผยแพร่แล้ว (US-15)"""

    reason = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "ระบุเหตุผลในการซ่อนเอกสาร (จำเป็นต้องกรอก)",
            }
        ),
        required=True,
        label="เหตุผลในการซ่อน",
        error_messages={"required": "กรุณาระบุเหตุผลในการซ่อนเอกสาร"},
    )

    def clean_reason(self):
        reason = (self.cleaned_data.get("reason") or "").strip()
        if not reason:
            raise forms.ValidationError("กรุณาระบุเหตุผลในการซ่อนเอกสาร")
        return reason


class BulkImportForm(forms.Form):
    """ฟอร์มสำหรับ Super Admin นำเข้าเอกสารจำนวนมากด้วย CSV และไฟล์ ZIP (US-17)"""

    csv_file = forms.FileField(
        label="ไฟล์ข้อมูล CSV",
        help_text=(
            "ไฟล์ .csv ตามรูปแบบที่กำหนด (คอลัมน์: file_path, department, "
            "batch, course, doc_type, title, description, exam_period, exam_year_be)"
        ),
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
        error_messages={"required": "กรุณาเลือกไฟล์ CSV"},
    )
    zip_file = forms.FileField(
        label="ไฟล์เอกสาร ZIP",
        help_text="ไฟล์ .zip ที่บรรจุไฟล์ PDF ตามชื่อและ path ที่ระบุใน CSV",
        widget=forms.FileInput(
            attrs={"class": "form-control", "accept": ".zip,application/zip"}
        ),
        error_messages={"required": "กรุณาเลือกไฟล์ ZIP"},
    )
    dry_run = forms.BooleanField(
        label="โหมดทดลองรัน (Dry Run)",
        help_text="ตรวจสอบความถูกต้องของข้อมูลทั้งหมดโดยไม่บันทึกลงระบบ",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get("csv_file")
        if file:
            if not file.name.lower().endswith(".csv"):
                raise forms.ValidationError("กรุณาอัปโหลดไฟล์ที่มีนามสกุล .csv")
        return file

    def clean_zip_file(self):
        file = self.cleaned_data.get("zip_file")
        if file:
            if not file.name.lower().endswith(".zip"):
                raise forms.ValidationError("กรุณาอัปโหลดไฟล์ที่มีนามสกุล .zip")
        return file
