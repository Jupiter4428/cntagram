"""ฟอร์มของ materials รับค่าอย่างเดียว การอ่าน/เขียนทำผ่าน selectors / services"""
from django import forms

from catalog.models import Batch, Department

from .models import DocType


class SearchForm(forms.Form):
    """ค้นหาเอกสาร (GET) ด้วยรหัสวิชา + ตัวกรอง ภาค/รุ่น/ประเภท (US-7)

    cleaned_data ส่งเข้า selectors.search_documents(**cleaned_data) ได้เลย
    """

    course_code = forms.CharField(label="รหัสวิชา", max_length=10, widget=forms.TextInput(attrs={"class": "form-control"}))
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
