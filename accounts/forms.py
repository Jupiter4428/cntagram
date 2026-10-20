from django import forms
from django.contrib.auth.forms import AuthenticationForm


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

# ==========================================
# ส่วนของ US-10: ฟอร์มมอบหมาย Moderator (วางต่อท้ายล่างสุด)
# ==========================================
from django.contrib.auth import get_user_model
from catalog.models import Department

User = get_user_model()


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


# ==========================================
# US-10: Moderator Form (วางต่อท้ายล่างสุด)
# ==========================================
from django.contrib.auth import get_user_model
from catalog.models import Department

User = get_user_model()


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