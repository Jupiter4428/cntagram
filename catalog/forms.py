"""ฟอร์มของ US-4 รับค่าอย่างเดียว การบันทึกทำผ่าน services"""
from django import forms


class BatchForm(forms.Form):
    number = forms.IntegerField(label="เลขรุ่น", min_value=1, max_value=32767)  # PositiveSmallIntegerField


class BatchCourseForm(forms.Form):
    """เพิ่มวิชาเข้ารุ่น ถ้ารหัสวิชายังไม่มีในระบบ ต้องกรอกชื่ออังกฤษเพื่อสร้างวิชาใหม่"""

    code = forms.CharField(label="รหัสวิชา", max_length=10)
    name_en = forms.CharField(label="ชื่อวิชา (อังกฤษ)", max_length=150, required=False)
    name_th = forms.CharField(label="ชื่อวิชา (ไทย)", max_length=150, required=False)
