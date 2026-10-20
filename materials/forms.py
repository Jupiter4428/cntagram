from django import forms

from .models import Approval


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

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{classes} is-invalid".strip()
