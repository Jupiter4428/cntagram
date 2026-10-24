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
