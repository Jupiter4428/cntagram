from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import LoginForm
from .services import (
    clear_login_failures,
    is_login_rate_limited,
    record_login_failure,
)


def _client_ip(request):
    """Return the direct peer address without trusting spoofable proxy headers."""
    return request.META.get("REMOTE_ADDR", "")


def _safe_login_redirect(request):
    """Return an internal `next` target, or the configured home page."""
    redirect_to = request.POST.get("next") or request.GET.get("next")
    if redirect_to and url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect_to
    return resolve_url(settings.LOGIN_REDIRECT_URL)


@require_GET
def home(request):
    """Public landing page for guests and authenticated users."""
    return render(request, "accounts/home.html")


@require_GET
def register(request):
    """Public registration entry point owned by the registration story."""
    return render(request, "accounts/register.html")


@require_http_methods(["GET", "POST"])
def login(request):
    """Authenticate a user while throttling repeated failures."""
    if request.user.is_authenticated:
        return redirect(_safe_login_redirect(request))

    if request.method == "GET":
        return render(
            request,
            "accounts/login.html",
            {"form": LoginForm(request=request), "next": request.GET.get("next", "")},
        )

    username = request.POST.get("username", "")
    client_ip = _client_ip(request)
    if is_login_rate_limited(identifier=username, client_ip=client_ip):
        form = LoginForm(request=request, initial={"username": username})
        response = render(
            request,
            "accounts/login.html",
            {
                "form": form,
                "next": request.POST.get("next", ""),
                "rate_limited": True,
            },
            status=429,
        )
        response["Retry-After"] = str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        return response

    form = LoginForm(request=request, data=request.POST)
    if form.is_valid():
        clear_login_failures(identifier=username, client_ip=client_ip)
        auth_login(request, form.get_user())
        return redirect(_safe_login_redirect(request))

    if username and request.POST.get("password"):
        record_login_failure(identifier=username, client_ip=client_ip)

    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": request.POST.get("next", "")},
    )


@require_POST
def logout(request):
    """End the current session; CSRF middleware protects this POST endpoint."""
    auth_logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)
