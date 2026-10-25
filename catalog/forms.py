from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from .models import Batch, BatchCourse, Course, Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["code", "name_th", "name_en", "is_active"]
        error_messages = {
            "code": {
                "unique": "รหัสภาควิชานี้มีอยู่ในระบบแล้ว",
            },
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["department", "number"]
        labels = {"department": "ภาควิชา", "number": "เลขรุ่น"}
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "รุ่นนี้มีอยู่แล้ว",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # เพิ่มรุ่นได้เฉพาะภาคที่เปิดใช้งาน
        self.fields["department"].queryset = Department.objects.filter(is_active=True)
        self.fields["department"].empty_label = "- เลือกภาควิชา -"


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "name_th", "name_en"]
        labels = {"code": "รหัสวิชา", "name_th": "ชื่อไทย", "name_en": "ชื่ออังกฤษ"}
        error_messages = {
            "code": {
                "unique": "รหัสวิชานี้มีอยู่ในระบบแล้ว",
            },
        }


class BatchCourseForm(forms.ModelForm):
    """ผูกวิชาที่มีอยู่แล้วเข้ารุ่น วิชาเดียวจึงใช้ร่วมได้หลายรุ่นโดยไม่สร้างซ้ำ"""

    class Meta:
        model = BatchCourse
        fields = ["course"]
        labels = {"course": "วิชา"}
        error_messages = {
            "course": {
                "invalid_choice": "วิชานี้อยู่ในรุ่นนี้แล้ว",
            },
        }

    def __init__(self, *args, batch, **kwargs):
        super().__init__(*args, instance=BatchCourse(batch=batch), **kwargs)
        # ให้เลือกได้เฉพาะวิชาที่ยังไม่อยู่ในรุ่นนี้ กันผูกซ้ำ
        self.fields["course"].queryset = Course.objects.exclude(batch_courses__batch=batch)
        self.fields["course"].empty_label = "- เลือกวิชา -"
