"""URL patterns routing for webboard discussion boards."""

from django.urls import path
from webboard import views

app_name = "webboard"

urlpatterns = [
    path("", views.board_index, name="board_index"),
    path(
        "category/<slug:slug>/",
        views.category_threads,
        name="category_threads",
    ),
    path("thread/create/", views.thread_create, name="thread_create"),
    path("thread/<int:pk>/", views.thread_detail, name="thread_detail"),
    path("thread/<int:pk>/reply/", views.thread_reply, name="thread_reply"),
    path(
        "thread/<int:pk>/pin/",
        views.thread_pin_toggle,
        name="thread_pin_toggle",
    ),
    path(
        "thread/<int:pk>/lock/",
        views.thread_lock_toggle,
        name="thread_lock_toggle",
    ),
    path(
        "thread/<int:pk>/delete/",
        views.thread_delete,
        name="thread_delete",
    ),
    path(
        "thread/<int:pk>/edit/",
        views.thread_edit,
        name="thread_edit",
    ),
    path(
        "post/<int:pk>/delete/",
        views.post_delete,
        name="post_delete",
    ),
    path(
        "post/<int:pk>/edit/",
        views.post_edit,
        name="post_edit",
    ),
]
