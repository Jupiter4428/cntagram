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
