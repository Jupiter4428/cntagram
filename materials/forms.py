"""ฟอร์มของ materials รับค่าอย่างเดียว การอ่าน/เขียนทำผ่าน selectors / services"""
from django import forms

from catalog.models import Batch, BatchCourse, Department

from .models import Approval, DocType, ExamPeriod


class SearchForm(forms.Form):
    """ค้นหาเอกสาร (GET) ด้วยรหัสวิชา + ตัวกรอง ภาค/รุ่น/ประเภท (US-7)

    cleaned_data ส่งเข้า selectors.search_documents(**cleaned_data) ได้เลย
    """

    course_code = forms.CharField(
        label="รหัสวิชา",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages={"required": "กรุณาระบุรหัสวิชา"},
    )
    department = forms.ModelChoiceField(
        label="ภาควิชา",
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="ทุกภาค",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    batch = forms.ModelChoiceField(
        label="รุ่น",
        queryset=Batch.objects.filter(department__is_active=True),  # ให้ตรงกับรายการภาค
        required=False,
        empty_label="ทุกรุ่น",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    doc_type = forms.ModelChoiceField(
        label="ประเภท",
        queryset=DocType.objects.order_by("code"),
        required=False,
        empty_label="ทุกประเภท",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        """เลือกทั้งภาคและรุ่น รุ่นต้องอยู่ในภาคนั้น (ไม่งั้นผลจะว่างโดยไม่รู้สาเหตุ)"""
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        batch = cleaned_data.get("batch")
        if department and batch and batch.department_id != department.pk:
            self.add_error("batch", f"รุ่น {batch.code} ไม่ได้อยู่ในภาค {department.code}")
        return cleaned_data


class UploadForm(forms.Form):
    """อัปโหลดชีท (US-5) cleaned_data ยกเว้น disclaimer ส่งเข้า services.upload_document ได้เลย

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
        error_messages={
            "required": "กรุณาระบุรายละเอียด",
        },
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
            "min_value": "ปี พ.ศ. ต้องไม่น้อยกว่า %(limit_value)s",
            "max_value": "ปี พ.ศ. ต้องไม่เกิน %(limit_value)s",
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

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        reason = (cleaned_data.get("reason") or "").strip()

        if decision == Approval.Decision.REJECTED and not reason:
            self.add_error("reason", "กรุณาระบุเหตุผลเมื่อปฏิเสธเอกสาร")

        cleaned_data["reason"] = reason or None
        return cleaned_data
