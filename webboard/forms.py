"""Input forms and validators for webboard threads and reply posts."""

from catalog.models import Course
from django import forms
from webboard.models import BoardCategory


class ThreadForm(forms.Form):
    """Form for composing and validating a new discussion thread."""

    category = forms.ModelChoiceField(
        queryset=BoardCategory.objects.all(),
        label="หมวดหมู่ห้องสนทนา",
        empty_label="-- เลือกหมวดหมู่ --",
        widget=forms.Select(attrs={"class": "form-select retro-field"}),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all().order_by("code"),
        required=False,
        label="วิชาที่เกี่ยวข้อง (ระบุหรือไม่ก็ได้)",
        empty_label="-- ไม่ระบุวิชาเฉพาะ --",
        widget=forms.Select(attrs={"class": "form-select retro-field"}),
    )
    title = forms.CharField(
        max_length=200,
        label="หัวข้อกระทู้",
        error_messages={"required": "กรุณาระบุหัวข้อกระทู้"},
        widget=forms.TextInput(
            attrs={
                "class": "form-control retro-field",
                "placeholder": "ระบุหัวข้อที่ต้องการพูดคุย...",
            }
        ),
    )
    content = forms.CharField(
        label="เนื้อหากระทู้",
        error_messages={"required": "กรุณาระบุเนื้อหากระทู้"},
        widget=forms.Textarea(
            attrs={
                "id": "thread-content-textarea",
                "class": "form-control retro-field",
                "rows": 8,
                "placeholder": "พิมพ์เนื้อหา หรือเลือกสติ๊กเกอร์ MSN และแทรก GIF...",
            }
        ),
    )

    def clean_title(self):
        """Ensure title is not whitespace only."""
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("กรุณาระบุหัวข้อกระทู้")
        return title

    def clean_content(self):
        """Ensure content is not whitespace only."""
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("กรุณาระบุเนื้อหากระทู้")
        return content


class PostForm(forms.Form):
    """Form for replying to an existing discussion thread."""

    content = forms.CharField(
        label="ข้อความตอบกลับ",
        error_messages={"required": "กรุณาระบุข้อความตอบกลับ"},
        widget=forms.Textarea(
            attrs={
                "id": "reply-content-textarea",
                "class": "form-control retro-field",
                "rows": 4,
                "placeholder": "พิมพ์ข้อความตอบกลับ เลือกสติ๊กเกอร์ หรือแทรก GIF...",
            }
        ),
    )

    def clean_content(self):
        """Ensure reply content is not whitespace only."""
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("กรุณาระบุข้อความตอบกลับ")
        return content
