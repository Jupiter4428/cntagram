from django import forms
from .models import Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["code", "name_th", "name_en", "is_active"]
        error_messages = {
            "code": {
                "unique": "รหัสภาควิชานี้มีอยู่ในระบบแล้ว",
            },
        }