"""Admin configuration for webboard models."""

from django.contrib import admin
from webboard.models import BoardCategory, Post, Thread


@admin.register(BoardCategory)
class BoardCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for BoardCategory."""

    list_display = ("name", "slug", "icon", "order", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    """Admin configuration for Thread."""

    list_display = (
        "id",
        "title",
        "category",
        "author",
        "is_pinned",
        "is_locked",
        "views_count",
        "created_at",
    )
    list_filter = ("category", "is_pinned", "is_locked", "created_at")
    search_fields = ("title", "content", "author__nickname", "author__email")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post."""

    list_display = ("id", "thread", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__nickname", "author__email")
