"""AppConfig for webboard application."""

from django.apps import AppConfig


class WebboardConfig(AppConfig):
    """Application configuration for webboard."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "webboard"
    verbose_name = "เว็บบอร์ดเด็กวิศวะ"
