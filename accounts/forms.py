from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from catalog.models import Department
from catalog.selectors import active_department_list

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Authenticate against the custom email-based user model."""

    username = forms.EmailField(
        label="Student email",
        max_length=255,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "autofocus": True,
                "class": "form-control",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "class": "form-control"}
        ),
    )

    def clean_username(self):
        """Match the normalization used when user accounts are created."""
        return self.cleaned_data["username"].strip().lower()

    @property
    def submitted_username(self):
        """Raw username as submitted (usable before validation, e.g. throttling)."""
        return self.data.get("username", "") if self.is_bound else ""

    @property
    def has_credentials(self):
        """Whether both username and password were actually submitted."""
        return bool(self.submitted_username and self.data.get("password"))

    @property
    def next_url(self):
        """Untrusted `next` target: submitted value when bound, else initial."""
        source = self.data if self.is_bound else self.initial
        return source.get("next", "")


class RegisterForm(forms.ModelForm):
    """สมัครสมาชิกด้วยอีเมลนักศึกษาคณะวิศวะ (US-1)

    สืบทอด ModelForm เพื่อใช้กฎจาก accounts.models โดยไม่ duplicate
    """

    password = forms.CharField(
        label="รหัสผ่าน",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
                "placeholder": "อย่างน้อย 8 ตัวอักษร",
            }
        ),
    )
    password_confirm = forms.CharField(
        label="ยืนยันรหัสผ่าน",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "form-control",
                "placeholder": "พิมพ์รหัสผ่านอีกครั้ง",
            }
        ),
    )
    pdpa_consent = forms.BooleanField(
        label="ข้าพเจ้ายินยอมให้เก็บและใช้ข้อมูลส่วนบุคคลตามนโยบาย PDPA",
        required=True,
        error_messages={"required": "ต้องยอมรับนโยบาย PDPA ก่อนสมัครสมาชิก"},
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = ["email", "nickname", "department"]
        labels = {
            "email": "อีเมลนักศึกษา",
            "nickname": "ชื่อเล่น (แสดงแทนอีเมล)",
            "department": "ภาควิชา",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "autofocus": True,
                    "class": "form-control",
                    "placeholder": "6610xxxxxx@student.tu.ac.th",
                }
            ),
            "nickname": forms.TextInput(
                attrs={
                    "autocomplete": "nickname",
                    "class": "form-control",
                    "placeholder": "ชื่อที่ผู้อื่นจะเห็น",
                }
            ),
            "department": forms.Select(attrs={"class": "form-select"}),
        }
        error_messages = {
            "email": {
                "unique": "อีเมลนี้ถูกใช้สมัครแล้ว",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = active_department_list()
        self.fields["department"].empty_label = "-- เลือกภาควิชา --"

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email, _ = User.validate_student_email(email)
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "รหัสผ่านทั้งสองช่องไม่ตรงกัน")
        elif password:
            # ใช้ AUTH_PASSWORD_VALIDATORS (รวมถึงห้ามคล้ายอีเมล/ชื่อเล่น)
            candidate = User(
                email=cleaned_data.get("email", ""),
                nickname=cleaned_data.get("nickname", ""),
            )
            try:
                validate_password(password, user=candidate)
            except ValidationError as exc:
                self.add_error("password", exc)
        return cleaned_data

    def full_clean(self):
        super().full_clean()
        # ใส่คลาส is-invalid ของ Bootstrap ให้ช่องที่มี error
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{classes} is-invalid".strip()


class ModeratorAssignmentForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("email"),
        label="เลือกผู้ใช้",
        empty_label="-- กรุณาเลือกผู้ใช้ --",
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True).order_by("code"),
        label="เลือกภาควิชา",
        empty_label="-- กรุณาเลือกภาควิชา --",
    )
