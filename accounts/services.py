from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.crypto import salted_hmac

from accounts.models import Role, UserRole

User = get_user_model()


@transaction.atomic
def register_user(*, email, password, nickname, department, pdpa_consent_at):
    """สร้างบัญชีนักศึกษาใหม่พร้อมผูก role 'student' (US-1)

    อินพุตต้องผ่าน RegisterForm มาแล้ว ถ้าขั้นใดล้มเหลวจะ rollback ทั้งหมด
    """
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            nickname=nickname,
            department=department,
            pdpa_consent_at=pdpa_consent_at,
        )
    except IntegrityError as exc:
        # สองคนสมัครอีเมลเดียวกันพร้อมกันจนผ่านเช็กซ้ำในฟอร์มทั้งคู่
        # UNIQUE ที่ชนได้มีแค่ email กับ student_id ซึ่งได้มาจาก email จึงแจ้งที่ช่อง email
        raise ValidationError({"email": "อีเมลนี้ถูกใช้สมัครแล้ว"}) from exc

    student_role = Role.objects.get(code=Role.STUDENT)
    UserRole.objects.create(user=user, role=student_role)
    return user


@dataclass(frozen=True)
class LoginAttempt:
    """Outcome of one login submission: authenticated user, throttled, or failed."""

    user: object = None
    rate_limited: bool = False


LOGIN_RATE_LIMIT_SALT = "accounts.login-rate-limit"


def _login_failure_keys(*, identifier, client_ip):
    """Build non-PII cache keys for login identity bucket and client IP bucket."""
    ident = (identifier or "").strip().casefold()
    ip = (client_ip or "unknown").strip()
    return (
        "login-failures:id:" + salted_hmac(LOGIN_RATE_LIMIT_SALT, ident).hexdigest(),
        "login-failures:ip:" + salted_hmac(LOGIN_RATE_LIMIT_SALT, ip).hexdigest(),
    )


def is_login_rate_limited(*, identifier, client_ip):
    """Return whether either the identity bucket or the network IP bucket is exhausted."""
    id_key, ip_key = _login_failure_keys(identifier=identifier, client_ip=client_ip)
    return (
        cache.get(id_key, 0) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS
        or cache.get(ip_key, 0) >= settings.LOGIN_RATE_LIMIT_IP_ATTEMPTS
    )


def _increment_failure_key(key, timeout):
    """Increment one failure counter, starting a fresh window if it expired."""
    if cache.add(key, 1, timeout=timeout):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        # The key may expire between add() and incr(). Start a fresh window.
        cache.set(key, 1, timeout=timeout)
        return 1


def record_login_failure(*, identifier, client_ip):
    """Record one failed authentication attempt for both identity and client IP."""
    id_key, ip_key = _login_failure_keys(identifier=identifier, client_ip=client_ip)
    timeout = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    _increment_failure_key(id_key, timeout)
    _increment_failure_key(ip_key, timeout)


def clear_login_failures(*, identifier, client_ip):
    """Clear identity failures after successful authentication (preserves IP failures)."""
    id_key, _ = _login_failure_keys(identifier=identifier, client_ip=client_ip)
    cache.delete(id_key)


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


def _register_attempt_key(client_ip):
    digest = salted_hmac(
        "accounts.register-throttle", client_ip or "unknown"
    ).hexdigest()
    return f"register-attempts:{digest}"


def is_register_rate_limited(client_ip):
    return (
        cache.get(_register_attempt_key(client_ip), 0)
        >= settings.REGISTER_RATE_LIMIT_ATTEMPTS
    )


def record_register_attempt(client_ip):
    key = _register_attempt_key(client_ip)
    if cache.add(key, 1, timeout=settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS)
        return 1


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


@transaction.atomic
def delete_own_account(*, user, password):
    """ผู้ใช้ลบบัญชีตัวเองตาม PDPA (US-13): ถอด role ทั้งหมดแล้วล้างข้อมูลด้วย anonymize()"""
    if not user.check_password(password):
        raise ValidationError({"password": "รหัสผ่านไม่ถูกต้อง"})
    # ล็อกแถว Super Admin กันสองคนสุดท้ายลบพร้อมกันจนไม่เหลือใคร
    super_admin_ids = list(
        UserRole.objects.select_for_update(of=("self",))
        .filter(role__code=Role.SUPER_ADMIN, user__is_active=True)
        .values_list("user_id", flat=True)
    )
    if set(super_admin_ids) == {user.pk}:
        raise ValidationError(
            "คุณเป็น Super Admin คนสุดท้าย ต้องแต่งตั้ง Super Admin คนอื่นก่อนลบบัญชี"
        )
    user.user_roles.all().delete()
    user.anonymize()


def _delete_account_failure_key(*, user_id, client_ip):
    normalized_ip = (client_ip or "unknown").strip()
    digest = salted_hmac(
        "accounts.delete-account-rate-limit",
        f"{user_id}|{normalized_ip}",
    ).hexdigest()
    return f"delete-account-failures:{digest}"


def is_delete_account_rate_limited(*, user_id, client_ip):
    key = _delete_account_failure_key(user_id=user_id, client_ip=client_ip)
    attempts = cache.get(key, 0)
    return attempts >= settings.LOGIN_RATE_LIMIT_ATTEMPTS


def record_delete_account_failure(*, user_id, client_ip):
    key = _delete_account_failure_key(user_id=user_id, client_ip=client_ip)
    timeout = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if cache.add(key, 1, timeout=timeout):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        return 1


def clear_delete_account_failures(*, user_id, client_ip):
    key = _delete_account_failure_key(user_id=user_id, client_ip=client_ip)
    cache.delete(key)
