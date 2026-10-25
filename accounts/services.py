from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.crypto import salted_hmac

from accounts.models import Role, UserRole


@dataclass(frozen=True)
class LoginAttempt:
    """Outcome of one login submission: authenticated user, throttled, or failed."""

    user: object = None
    rate_limited: bool = False


def _login_failure_key(*, identifier, client_ip):
    """Build a non-PII cache key for one login identity and network peer."""
    normalized_identifier = (identifier or "").strip().casefold()
    normalized_ip = (client_ip or "unknown").strip()
    digest = salted_hmac(
        "accounts.login-rate-limit",
        f"{normalized_identifier}|{normalized_ip}",
    ).hexdigest()
    return f"login-failures:{digest}"


def is_login_rate_limited(*, identifier, client_ip):
    """Return whether this identity/IP pair exhausted its failure allowance."""
    key = _login_failure_key(identifier=identifier, client_ip=client_ip)
    attempts = cache.get(key, 0)
    return attempts >= settings.LOGIN_RATE_LIMIT_ATTEMPTS


def record_login_failure(*, identifier, client_ip):
    """Record one failed authentication attempt for a fixed temporary window."""
    key = _login_failure_key(identifier=identifier, client_ip=client_ip)
    timeout = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if cache.add(key, 1, timeout=timeout):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        # The key may expire between add() and incr(). Start a fresh window.
        cache.set(key, 1, timeout=timeout)
        return 1


def clear_login_failures(*, identifier, client_ip):
    """Clear failures after a successful authentication."""
    key = _login_failure_key(identifier=identifier, client_ip=client_ip)
    cache.delete(key)


def attempt_login(*, form, client_ip):
    """Process a bound LoginForm: throttle first, then validate and record.

    The throttle check runs before validation so a blocked identity never
    reaches authenticate(), even with the correct password.
    """
    identifier = form.submitted_username
    if is_login_rate_limited(identifier=identifier, client_ip=client_ip):
        return LoginAttempt(rate_limited=True)
    if form.is_valid():
        clear_login_failures(identifier=identifier, client_ip=client_ip)
        return LoginAttempt(user=form.get_user())
    if form.has_credentials:
        record_login_failure(identifier=identifier, client_ip=client_ip)
    return LoginAttempt()


def assign_moderator(*, user, department, granted_by):
    """แต่งตั้ง Moderator ประจำภาควิชา พร้อมบันทึกผู้แต่งตั้ง"""
    user_role = UserRole(
        user=user,
        role=Role.objects.get(code=Role.MODERATOR),
        department=department,
        granted_by=granted_by,
    )
    try:
        user_role.full_clean()
        with transaction.atomic():
            user_role.save()
    except IntegrityError as e:
        raise ValidationError(
            f"{user.email} เป็น Moderator ภาควิชา {department.code} อยู่แล้ว"
        ) from e
    except ValidationError as e:
        msg_str = str(e)
        if "already has this role" in msg_str or "uq_userrole_with_dept" in msg_str:
            raise ValidationError(
                f"{user.email} เป็น Moderator ภาควิชา {department.code} อยู่แล้ว"
            ) from e
        raise
    return user_role


def remove_moderator(*, user_role):
    """ถอดถอน Moderator ออกจากภาควิชา"""
    user_role.delete()