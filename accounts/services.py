from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac


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
