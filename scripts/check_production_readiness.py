"""Read-only deployment readiness checks; never prints secret values.

Run with: python scripts/check_production_readiness.py
Supply the actual Render environment variables to the process.
"""

import os
import sys
from urllib.parse import urlparse


def check(environ):
    issues = []
    if environ.get("DEBUG", "").strip().lower() not in {"false", "0", "no", "off"}:
        issues.append("DEBUG must explicitly be False")
    secret = environ.get("SECRET_KEY", "")
    if len(secret) < 50 or secret.startswith("django-insecure-"):
        issues.append("SECRET_KEY must be a strong non-development value")
    hosts = [
        h.strip() for h in environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()
    ]
    if not hosts or "*" in hosts:
        issues.append(
            "ALLOWED_HOSTS must contain explicit production hosts (no wildcard)"
        )
    if not environ.get("DATABASE_URL", "").startswith(("postgres://", "postgresql://")):
        issues.append("DATABASE_URL must point to PostgreSQL")
    origins = [
        o.strip()
        for o in environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
        if o.strip()
    ]
    if not origins or any(urlparse(o).scheme != "https" for o in origins):
        issues.append("CSRF_TRUSTED_ORIGINS must list HTTPS origins")
    media = environ.get("MEDIA_ROOT", "")
    if not media:
        issues.append("MEDIA_ROOT must be set to a verified persistent storage path")
    return issues


if __name__ == "__main__":
    problems = check(os.environ)
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        print("Readiness check failed; no environment values were printed.")
        sys.exit(1)
    print("PASS: deployment configuration checks passed.")
    print(
        "NOTE: Disk persistence, HTTPS and backup restore need separate verification."
    )
