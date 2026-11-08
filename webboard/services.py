"""Business logic mutations and services for the webboard domain."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from webboard.models import BoardCategory, Post, Thread


@transaction.atomic
def create_thread(
    *,
    author,
    category: BoardCategory,
    title: str,
    content: str,
    course=None,
) -> Thread:
    """Create a new discussion thread and save it to the database."""
    cleaned_title = title.strip()
    cleaned_content = content.strip()

    if not cleaned_title:
        raise ValidationError({"title": "กรุณาระบุหัวข้อกระทู้"})

    if not cleaned_content:
        raise ValidationError({"content": "กรุณาระบุเนื้อหากระทู้"})

    thread = Thread.objects.create(
        author=author,
        category=category,
        course=course,
        title=cleaned_title,
        content=cleaned_content,
    )
    return thread


@transaction.atomic
def create_post(
    *,
    thread: Thread,
    author,
    content: str,
) -> Post:
    """Create a reply post under a thread, verifying it is not locked."""
    if thread.is_locked:
        raise ValidationError("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้ตอบข้อความเพิ่ม")

    cleaned_content = content.strip()
    if not cleaned_content:
        raise ValidationError({"content": "กรุณาระบุข้อความตอบกลับ"})

    post = Post.objects.create(
        thread=thread,
        author=author,
        content=cleaned_content,
    )
    return post


def increment_thread_views(*, thread_id: int) -> None:
    """Increment thread view count atomically using an F expression."""
    Thread.objects.filter(pk=thread_id).update(
        views_count=F("views_count") + 1,
    )


@transaction.atomic
def toggle_thread_pin(*, thread: Thread, actor) -> bool:
    """Toggle the pinned status of a thread by a staff member."""
    if not (actor.is_staff or actor.is_superuser):
        raise PermissionDenied("เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถปักหมุดกระทู้ได้")

    thread.is_pinned = not thread.is_pinned
    thread.save(update_fields=["is_pinned"])
    return thread.is_pinned


@transaction.atomic
def toggle_thread_lock(*, thread: Thread, actor) -> bool:
    """Toggle the locked status of a thread by a staff member."""
    if not (actor.is_staff or actor.is_superuser):
        raise PermissionDenied("เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถล็อกกระทู้ได้")

    thread.is_locked = not thread.is_locked
    thread.save(update_fields=["is_locked"])
    return thread.is_locked


@transaction.atomic
def delete_thread(*, thread: Thread, actor) -> None:
    """Delete a thread if the actor is its author or a staff member."""
    if not (actor == thread.author or actor.is_staff or actor.is_superuser):
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการลบกระทู้นี้")

    thread.delete()


@transaction.atomic
def delete_post(*, post: Post, actor) -> None:
    """Delete a reply post if the actor is its author or a staff member."""
    if not (actor == post.author or actor.is_staff or actor.is_superuser):
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการลบความคิดเห็นนี้")

    post.delete()
