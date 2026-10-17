# catalog/forms.py
from django import forms
from .models import Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['code', 'name_th', 'name_en', 'is_active']
        labels = {
            'code': 'รหัสภาควิชา',
            'name_th': 'ชื่อภาษาไทย',
            'name_en': 'ชื่อภาษาอังกฤษ',
            'is_active': 'เปิดใช้งาน',
        }
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น CN, CE'}),
            'name_th': forms.TextInput(attrs={'class': 'form-control'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        # Normalize ตัดช่องว่างและแปลงเป็นตัวพิมพ์ใหญ่
        code = self.cleaned_data.get('code', '').strip().upper()

        # ตรวจสอบว่ารหัสซ้ำหรือไม่
        qs = Department.objects.filter(code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("รหัสภาควิชานี้มีอยู่ในระบบแล้ว")

        return code