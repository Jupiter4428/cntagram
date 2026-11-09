"""Data models for webboard discussion forum."""

from django.conf import settings
from django.db import models


class BoardCategory(models.Model):
    """Category room for grouping webboard discussion threads."""

    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="สลัก")
    description = models.TextField(blank=True, verbose_name="คำอธิบายหมวดหมู่")
    icon = models.CharField(
        max_length=50,
        default="💬",
        verbose_name="ไอคอนเรโทร",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="ลำดับการแสดงผล",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="สร้างเมื่อ",
    )

    class Meta:
        verbose_name = "หมวดหมู่เว็บบอร์ด"
        verbose_name_plural = "หมวดหมู่เว็บบอร์ด"
        ordering = ["order", "id"]

    def __str__(self):
        """Return the category name with its icon."""
        return f"{self.icon} {self.name}"


class Thread(models.Model):
    """Discussion thread posted by an authenticated student."""

    category = models.ForeignKey(
        BoardCategory,
        on_delete=models.CASCADE,
        related_name="threads",
        verbose_name="หมวดหมู่",
    )
    course = models.ForeignKey(
        "catalog.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webboard_threads",
        verbose_name="วิชาที่เกี่ยวข้อง",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webboard_threads",
        verbose_name="ผู้เขียน",
    )
    title = models.CharField(max_length=200, verbose_name="หัวข้อกระทู้")
    content = models.TextField(verbose_name="เนื้อหากระทู้")
    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="ยอดเข้าชม",
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="ปักหมุดกระทู้",
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name="ล็อกกระทู้",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="สร้างเมื่อ",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="แก้ไขล่าสุด",
    )

    class Meta:
        verbose_name = "กระทู้สนทนา"
        verbose_name_plural = "กระทู้สนทนา"
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        """Return thread title with category prefix."""
        return f"[{self.category.name}] {self.title}"

    @property
    def is_edited(self) -> bool:
        """Return True if updated_at is more than 1 second after created_at."""
        if not self.updated_at or not self.created_at:
            return False
        return (self.updated_at - self.created_at).total_seconds() > 1


class Post(models.Model):
    """Reply comment on a discussion thread."""

    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="กระทู้",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webboard_posts",
        verbose_name="ผู้ตอบ",
    )
    content = models.TextField(verbose_name="ข้อความตอบกลับ")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="ตอบเมื่อ",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="แก้ไขล่าสุด",
    )

    class Meta:
        verbose_name = "ความคิดเห็นตอบกระทู้"
        verbose_name_plural = "ความคิดเห็นตอบกระทู้"
        ordering = ["created_at"]

    def __str__(self):
        """Return brief post description."""
        return f"Reply #{self.id} on {self.thread.title}"

    @property
    def is_edited(self) -> bool:
        """Return True if updated_at is more than 1 second after created_at."""
        if not self.updated_at or not self.created_at:
            return False
        return (self.updated_at - self.created_at).total_seconds() > 1
