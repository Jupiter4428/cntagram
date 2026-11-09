"""Business logic mutations and services for the webboard domain."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from portal.permissions import can_moderate_content
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
    locked_thread = Thread.objects.select_for_update().get(pk=thread.pk)
    if locked_thread.is_locked:
        raise ValidationError("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้ตอบข้อความเพิ่ม")

    cleaned_content = content.strip()
    if not cleaned_content:
        raise ValidationError({"content": "กรุณาระบุข้อความตอบกลับ"})

    post = Post.objects.create(
        thread=locked_thread,
        author=author,
        content=cleaned_content,
    )
    return post


def increment_thread_views(*, thread_id: int) -> int:
    """Increment a thread view count atomically and return the current count."""
    Thread.objects.filter(pk=thread_id).update(
        views_count=F("views_count") + 1,
    )
    return Thread.objects.values_list("views_count", flat=True).get(pk=thread_id)


@transaction.atomic
def toggle_thread_pin(*, thread: Thread, actor) -> bool:
    """Toggle the pinned status of a thread by a content moderator."""
    if not can_moderate_content(actor):
        raise PermissionDenied("เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถปักหมุดกระทู้ได้")

    thread.is_pinned = not thread.is_pinned
    thread.save(update_fields=["is_pinned"])
    return thread.is_pinned


@transaction.atomic
def toggle_thread_lock(*, thread: Thread, actor) -> bool:
    """Toggle the locked status of a thread by a content moderator."""
    if not can_moderate_content(actor):
        raise PermissionDenied("เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถล็อกกระทู้ได้")

    thread.is_locked = not thread.is_locked
    thread.save(update_fields=["is_locked"])
    return thread.is_locked


@transaction.atomic
def delete_thread(*, thread: Thread, actor) -> None:
    """Delete a thread if the actor is its author or a content moderator."""
    if not (actor == thread.author or can_moderate_content(actor)):
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการลบกระทู้นี้")

    thread.delete()


@transaction.atomic
def delete_post(*, post: Post, actor) -> None:
    """Delete a reply if the actor is its author or a content moderator."""
    if not (actor == post.author or can_moderate_content(actor)):
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการลบความคิดเห็นนี้")

    post.delete()


@transaction.atomic
def update_thread(
    *,
    thread: Thread,
    actor,
    title: str,
    content: str,
    category: BoardCategory | None = None,
    course=None,
) -> Thread:
    """Update a discussion thread after verifying author and lock status."""
    locked_thread = Thread.objects.select_for_update().get(pk=thread.pk)

    if actor != locked_thread.author:
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการแก้ไขกระทู้นี้")

    if locked_thread.is_locked:
        raise PermissionDenied("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้แก้ไข")

    cleaned_title = title.strip()
    cleaned_content = content.strip()

    if not cleaned_title:
        raise ValidationError({"title": "กรุณาระบุหัวข้อกระทู้"})

    if not cleaned_content:
        raise ValidationError({"content": "กรุณาระบุเนื้อหากระทู้"})

    locked_thread.title = cleaned_title
    locked_thread.content = cleaned_content
    if category is not None:
        locked_thread.category = category
    if course is not None:
        locked_thread.course = course

    locked_thread.save()
    return locked_thread


@transaction.atomic
def update_post(
    *,
    post: Post,
    actor,
    content: str,
) -> Post:
    """Update a reply post after verifying author and parent thread lock status."""
    locked_post = (
        Post.objects.select_for_update().select_related("thread").get(pk=post.pk)
    )

    if actor != locked_post.author:
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการแก้ไขความคิดเห็นนี้")

    if locked_post.thread.is_locked:
        raise PermissionDenied("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้แก้ไขความคิดเห็น")

    cleaned_content = content.strip()
    if not cleaned_content:
        raise ValidationError({"content": "กรุณาระบุข้อความตอบกลับ"})

    locked_post.content = cleaned_content
    locked_post.save()
    return locked_post
