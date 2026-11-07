import time
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils.crypto import salted_hmac

from accounts.models import PollVote, Role, ShoutboxMessage, UserRole

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
        # UNIQUE ที่ชนได้มีแค่ email กับ student_id
        # ซึ่งได้มาจาก email จึงแจ้งที่ช่อง email
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


def _login_window_index():
    """Return the fixed login throttle window number."""
    return int(time.time()) // settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS


def _login_failure_keys(*, identifier, client_ip):
    """Build non-PII cache keys for login identity bucket and client IP bucket.

    The window number is part of the key so each bucket is a fixed window:
    DatabaseCache.incr() resets the key's expiry, which would otherwise
    make the window slide with every failure.
    """
    ident = (identifier or "").strip().casefold()
    ip = (client_ip or "unknown").strip()
    window = _login_window_index()
    id_hash = salted_hmac(LOGIN_RATE_LIMIT_SALT, ident).hexdigest()
    ip_hash = salted_hmac(LOGIN_RATE_LIMIT_SALT, ip).hexdigest()
    return (
        f"login-failures:id:{id_hash}:{window}",
        f"login-failures:ip:{ip_hash}:{window}",
    )


def is_login_rate_limited(*, identifier, client_ip):
    """Return whether either the identity bucket or the network IP bucket is full."""
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
    """Clear identity failures after a successful login (keeps IP failures)."""
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


def _register_window_index():
    return int(time.time()) // settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS


def _register_attempt_key(client_ip):
    digest = salted_hmac(
        "accounts.register-throttle", client_ip or "unknown"
    ).hexdigest()
    bucket = _register_window_index()
    return f"register-attempts:{digest}:{bucket}"


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
    """ผู้ใช้ลบบัญชีตัวเองตาม PDPA (US-13):

    ถอด role ทั้งหมดแล้วล้างข้อมูลด้วย anonymize()
    """
    if not user.check_password(password):
        raise ValidationError(
            {
                "password": "รหัสผ่านไม่ถูกต้อง"
            }  # nosec B105: ชื่อฟิลด์ของฟอร์ม ไม่ใช่รหัสผ่าน
        )
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


def _delete_account_failure_key(*, user_id):
    digest = salted_hmac(
        "accounts.delete-account-rate-limit",
        str(user_id),
    ).hexdigest()
    return f"delete-account-failures:{digest}"


def is_delete_account_rate_limited(*, user_id):
    key = _delete_account_failure_key(user_id=user_id)
    attempts = cache.get(key, 0)
    return attempts >= settings.LOGIN_RATE_LIMIT_ATTEMPTS


def record_delete_account_failure(*, user_id):
    key = _delete_account_failure_key(user_id=user_id)
    timeout = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    if cache.add(key, 1, timeout=timeout):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        return 1


def clear_delete_account_failures(*, user_id):
    key = _delete_account_failure_key(user_id=user_id)
    cache.delete(key)


VISITOR_COUNTER_KEY = "site:visitor_count"
VISITOR_COUNTER_BASE = 38


def record_home_visit():
    """เพิ่มตัวนับการเปิดหน้า (cache ไม่รับประกัน atomic) และคืนเลข 6 หลัก"""
    first_visit = VISITOR_COUNTER_BASE + 1
    if cache.add(VISITOR_COUNTER_KEY, first_visit, timeout=None):
        total = first_visit
    else:
        total = cache.incr(VISITOR_COUNTER_KEY)
    return f"{total:06d}"


POLL_QUESTION = "วิชาไหนโหดสุดเทอมนี้"
POLL_CHOICES = (
    ("math", "Engineering Math / Calculus"),
    ("dsa", "Data Structures & Algorithms"),
    ("circuit", "Circuit Analysis / Physics"),
)


def get_weekly_poll():
    """Return durable poll totals and percentages."""
    vote_counts = dict(
        PollVote.objects.values("choice")
        .annotate(n=Count("pk"))
        .values_list("choice", "n")
    )
    total_votes = sum(vote_counts.values())
    choices = []
    for key, label in POLL_CHOICES:
        votes = vote_counts.get(key, 0)
        choices.append(
            {
                "key": key,
                "label": label,
                "votes": votes,
                "percent": round(votes * 100 / total_votes) if total_votes else 0,
            }
        )
    return {"question": POLL_QUESTION, "total": total_votes, "choices": choices}


def record_poll_vote(*, user, choice_key):
    """Persist one vote per user; the database enforces uniqueness."""
    if choice_key not in dict(POLL_CHOICES):
        raise ValidationError("Invalid poll choice")
    try:
        with transaction.atomic():
            PollVote.objects.create(user=user, choice=choice_key)
    except IntegrityError:
        return False, get_weekly_poll()
    return True, get_weekly_poll()


SHOUTBOX_MAX_MESSAGES = 30
DEFAULT_SHOUTBOX_MESSAGES = (
    {"author": "[CN21] พี่บอย", "text": "น้องๆ อย่าลืมทวนวงจรไฟฟ้านะ"},
    {"author": "[CN23] น้ำหวาน", "text": "ขอบคุณสำหรับชีทแคลคูลัสค่า!"},
    {"author": "[ME22] ก้อง", "text": "ใครมีแนวข้อสอบ Thermo ฝากอัปหน่อย"},
    {"author": "[CE24] เต้ย", "text": "สู้ๆ กับมิดเทอมทุกคนครับ"},
)


def get_shoutbox_messages():
    """Return the newest 30 persisted messages, or demo content when empty."""
    messages = list(
        ShoutboxMessage.objects.select_related("user__department").order_by(
            "-created_at", "-pk"
        )[:SHOUTBOX_MAX_MESSAGES]
    )
    if not messages:
        return list(DEFAULT_SHOUTBOX_MESSAGES)
    messages.reverse()
    return [
        {
            "author": (
                f"[{msg.user.department.code if msg.user.department else 'Member'}] "
                f"{msg.user.nickname}"
            ),
            "text": msg.text,
        }
        for msg in messages
    ]


def add_shoutbox_message(*, user, text):
    """Persist a validated message and return the newest 30."""
    clean_text = (text or "").strip()
    if not clean_text or len(clean_text) > 200:
        raise ValidationError("Message must contain 1–200 characters")
    ShoutboxMessage.objects.create(user=user, text=clean_text)
    return get_shoutbox_messages()
