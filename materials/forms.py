"""ฟอร์มของ materials รับค่าอย่างเดียว การอ่าน/เขียนทำผ่าน selectors / services"""
from django import forms

from catalog.models import BatchCourse

from .models import DocType, ExamPeriod


class UploadForm(forms.Form):
    """อัปโหลดชีท (US-5) cleaned_data ยกเว้น disclaimer ส่งเข้า services.upload_document ได้เลย

    batch_course รับได้ทุกภาค โดยตั้งใจ: การเช็กว่าตรงภาคของผู้ใช้อยู่ใน service
    ซึ่งตอบ 403 เมื่อมีคนแก้ request ข้ามภาค (ไม่ใช่แค่ฟอร์มไม่ผ่าน)
    """

    batch_course = forms.ModelChoiceField(
        label="วิชา", queryset=BatchCourse.objects.all()
    )
    doc_type = forms.ModelChoiceField(
        label="ประเภท", queryset=DocType.objects.order_by("code")
    )
    title = forms.CharField(label="ชื่อเอกสาร", max_length=200)
    description = forms.CharField(label="รายละเอียด", widget=forms.Textarea)
    exam_period = forms.ModelChoiceField(
        label="ช่วงสอบ", queryset=ExamPeriod.objects.all(), required=False
    )
    exam_year_be = forms.IntegerField(
        label="ปี พ.ศ.", min_value=2500, max_value=2700, required=False
    )
    file = forms.FileField(label="ไฟล์ PDF")
    disclaimer = forms.BooleanField(
        label="ฉันยืนยันว่าไฟล์นี้ไม่ละเมิดลิขสิทธิ์ของผู้อื่น", required=True
    )
