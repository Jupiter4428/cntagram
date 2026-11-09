"""Thin views coordinating webboard requests, services, and selectors."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from portal.permissions import can_moderate_content
from webboard import selectors, services
from webboard.forms import PostEditForm, PostForm, ThreadEditForm, ThreadForm

THREADS_PER_PAGE = 15
POSTS_PER_PAGE = 20


def board_index(request):
    """Display webboard main hub with categories and recent threads."""
    query = request.GET.get("q", "").strip()
    categories = selectors.list_board_categories()
    threads_qs = selectors.list_threads(search_query=query)
    paginator = Paginator(threads_qs, THREADS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "webboard/board_index.html",
        {
            "categories": categories,
            "threads": page_obj,
            "page_obj": page_obj,
            "search_query": query,
            "active_category": None,
        },
    )


def category_threads(request, slug):
    """Display threads filtered under a specific board category."""
    category = selectors.get_category_by_slug(slug)
    if not category:
        raise Http404("ไม่พบหมวดหมู่เว็บบอร์ดที่ระบุ")

    query = request.GET.get("q", "").strip()
    categories = selectors.list_board_categories()
    threads_qs = selectors.list_threads(category_slug=slug, search_query=query)
    paginator = Paginator(threads_qs, THREADS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "webboard/board_index.html",
        {
            "categories": categories,
            "threads": page_obj,
            "page_obj": page_obj,
            "search_query": query,
            "active_category": category,
        },
    )


def thread_detail(request, pk):
    """Display thread contents, comments, and reply form."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    thread.views_count = services.increment_thread_views(
        thread_id=thread.pk, session=request.session
    )
    posts_qs = selectors.list_posts_for_thread(thread_id=thread.pk)
    paginator = Paginator(posts_qs, POSTS_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    form = PostForm()
    return render(
        request,
        "webboard/thread_detail.html",
        {
            "thread": thread,
            "posts": page_obj,
            "page_obj": page_obj,
            "form": form,
            "can_moderate": can_moderate_content(request.user),
        },
    )


@login_required
def thread_create(request):
    """Handle new discussion thread composition and validation."""
    if request.method == "POST":
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = services.create_thread(
                author=request.user,
                category=form.cleaned_data["category"],
                course=form.cleaned_data["course"],
                title=form.cleaned_data["title"],
                content=form.cleaned_data["content"],
            )
            messages.success(request, "สร้างกระทู้สำเร็จเรียบร้อยแล้ว!")
            return redirect("webboard:thread_detail", pk=thread.pk)
    else:
        initial = {}
        category_slug = request.GET.get("category")
        if category_slug:
            cat = selectors.get_category_by_slug(category_slug)
            if cat:
                initial["category"] = cat.pk
        form = ThreadForm(initial=initial)

    return render(request, "webboard/thread_create.html", {"form": form})


@login_required
@require_POST
def thread_reply(request, pk):
    """Add a new comment reply to an existing thread."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    form = PostForm(request.POST)
    if form.is_valid():
        try:
            services.create_post(
                thread=thread,
                author=request.user,
                content=form.cleaned_data["content"],
            )
            messages.success(request, "ส่งข้อความตอบกลับสำเร็จแล้ว!")
        except ValidationError as err:
            messages.error(request, str(err))
    else:
        messages.error(request, "กรุณากรอกข้อความตอบกลับให้ถูกต้อง")

    return redirect("webboard:thread_detail", pk=thread.pk)


@login_required
@require_POST
def thread_pin_toggle(request, pk):
    """Toggle thread pinned state by a content moderator."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    try:
        new_state = services.toggle_thread_pin(thread=thread, actor=request.user)
        msg = "ปักหมุดกระทู้แล้ว" if new_state else "ปลดหมุดกระทู้แล้ว"
        messages.success(request, msg)
    except PermissionDenied as err:
        messages.error(request, str(err))

    return redirect("webboard:thread_detail", pk=thread.pk)


@login_required
@require_POST
def thread_lock_toggle(request, pk):
    """Toggle thread locked state by a content moderator."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    try:
        new_state = services.toggle_thread_lock(thread=thread, actor=request.user)
        msg = "ล็อกกระทู้แล้ว" if new_state else "ปลดล็อกกระทู้แล้ว"
        messages.success(request, msg)
    except PermissionDenied as err:
        messages.error(request, str(err))

    return redirect("webboard:thread_detail", pk=thread.pk)


@login_required
@require_POST
def thread_delete(request, pk):
    """Delete a thread if permitted."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    try:
        services.delete_thread(thread=thread, actor=request.user)
        messages.success(request, "ลบกระทู้เรียบร้อยแล้ว")
    except PermissionDenied as err:
        messages.error(request, str(err))

    return redirect("webboard:board_index")


@login_required
@require_POST
def post_delete(request, pk):
    """Delete a reply post if permitted."""
    post = selectors.get_post_by_id(pk)
    if not post:
        raise Http404("ไม่พบความคิดเห็นที่ต้องการ")

    thread_pk = post.thread_id
    try:
        services.delete_post(post=post, actor=request.user)
        messages.success(request, "ลบความคิดเห็นเรียบร้อยแล้ว")
    except PermissionDenied as err:
        messages.error(request, str(err))

    return redirect("webboard:thread_detail", pk=thread_pk)


@login_required
def thread_edit(request, pk):
    """Edit an existing discussion thread if authorized and not locked."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    if request.user != thread.author:
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการแก้ไขกระทู้นี้")

    if thread.is_locked:
        raise PermissionDenied("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้แก้ไข")

    if request.method == "POST":
        form = ThreadEditForm(request.POST)
        if form.is_valid():
            try:
                services.update_thread(
                    thread=thread,
                    actor=request.user,
                    category=form.cleaned_data["category"],
                    course=form.cleaned_data["course"],
                    title=form.cleaned_data["title"],
                    content=form.cleaned_data["content"],
                )
                messages.success(request, "แก้ไขกระทู้สำเร็จเรียบร้อยแล้ว!")
                return redirect("webboard:thread_detail", pk=thread.pk)
            except (PermissionDenied, ValidationError) as err:
                messages.error(request, str(err))
    else:
        form = ThreadEditForm(
            initial={
                "category": thread.category_id,
                "course": thread.course_id,
                "title": thread.title,
                "content": thread.content,
            }
        )

    return render(
        request,
        "webboard/thread_edit.html",
        {
            "thread": thread,
            "form": form,
        },
    )


@login_required
def post_edit(request, pk):
    """Edit an existing reply post if authorized and thread is not locked."""
    post = selectors.get_post_by_id(pk)
    if not post:
        raise Http404("ไม่พบความคิดเห็นที่ต้องการ")

    if request.user != post.author:
        raise PermissionDenied("คุณไม่มีสิทธิ์ในการแก้ไขความคิดเห็นนี้")

    if post.thread.is_locked:
        raise PermissionDenied("กระทู้นี้ถูกล็อกแล้ว ไม่อนุญาตให้แก้ไขความคิดเห็น")

    if request.method == "POST":
        form = PostEditForm(request.POST)
        if form.is_valid():
            try:
                services.update_post(
                    post=post,
                    actor=request.user,
                    content=form.cleaned_data["content"],
                )
                messages.success(request, "แก้ไขความคิดเห็นสำเร็จแล้ว!")
                return redirect("webboard:thread_detail", pk=post.thread_id)
            except (PermissionDenied, ValidationError) as err:
                messages.error(request, str(err))
    else:
        form = PostEditForm(initial={"content": post.content})

    return render(
        request,
        "webboard/post_edit.html",
        {
            "post": post,
            "thread": post.thread,
            "form": form,
        },
    )
