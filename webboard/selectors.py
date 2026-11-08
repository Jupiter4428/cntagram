"""Selectors for read-only database queries on the webboard."""

from django.db.models import Count, Q, QuerySet
from webboard.models import BoardCategory, Post, Thread


def list_board_categories() -> QuerySet[BoardCategory]:
    """Return all board categories annotated with total thread counts."""
    return BoardCategory.objects.annotate(
        threads_count=Count("threads", distinct=True)
    ).order_by("order", "id")


def get_category_by_slug(slug: str) -> BoardCategory | None:
    """Return a single board category by its unique slug, or None."""
    return BoardCategory.objects.filter(slug=slug).first()


def list_threads(
    *,
    category_slug: str | None = None,
    course_code: str | None = None,
    search_query: str | None = None,
) -> QuerySet[Thread]:
    """Return threads filtered by category, course, or query, ordered by pin."""
    queryset = (
        Thread.objects.select_related("category", "course", "author")
        .annotate(posts_count=Count("posts", distinct=True))
        .order_by("-is_pinned", "-created_at")
    )

    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    if course_code:
        queryset = queryset.filter(course__code__iexact=course_code)

    if search_query:
        query = search_query.strip()
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    return queryset


def get_thread_by_id(thread_id: int) -> Thread | None:
    """Return a thread by its primary key with related entities, or None."""
    return (
        Thread.objects.select_related("category", "course", "author")
        .filter(pk=thread_id)
        .first()
    )


def list_posts_for_thread(thread_id: int) -> QuerySet[Post]:
    """Return all posts belonging to a thread ordered chronologically."""
    return (
        Post.objects.filter(thread_id=thread_id)
        .select_related("author")
        .order_by("created_at")
    )


def get_post_by_id(post_id: int) -> Post | None:
    """Return a single post with author and thread loaded, or None."""
    return Post.objects.select_related("author", "thread").filter(pk=post_id).first()
