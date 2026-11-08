"""Thin views coordinating webboard requests, services, and selectors."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from webboard import selectors, services
from webboard.forms import PostForm, ThreadForm


def board_index(request):
    """Display webboard main hub with categories and recent threads."""
    query = request.GET.get("q", "").strip()
    categories = selectors.list_board_categories()
    threads = selectors.list_threads(search_query=query)
    return render(
        request,
        "webboard/board_index.html",
        {
            "categories": categories,
            "threads": threads,
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
    threads = selectors.list_threads(category_slug=slug, search_query=query)
    return render(
        request,
        "webboard/board_index.html",
        {
            "categories": categories,
            "threads": threads,
            "search_query": query,
            "active_category": category,
        },
    )


def thread_detail(request, pk):
    """Display thread contents, comments, and reply form."""
    thread = selectors.get_thread_by_id(pk)
    if not thread:
        raise Http404("ไม่พบกระทู้ที่ต้องการ")

    services.increment_thread_views(thread_id=thread.pk)
    posts = selectors.list_posts_for_thread(thread_id=thread.pk)
    form = PostForm()
    return render(
        request,
        "webboard/thread_detail.html",
        {"thread": thread, "posts": posts, "form": form},
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
    """Toggle thread pinned state by staff."""
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
    """Toggle thread locked state by staff."""
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
