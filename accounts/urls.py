from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("account/profile/", views.profile, name="profile"),
    path("account/delete/", views.delete_account, name="delete_account"),
    path("users/<int:user_id>/avatar/", views.user_avatar, name="user_avatar"),
    path("poll/vote/", views.poll_vote, name="poll_vote"),
    path("shoutbox/post/", views.shoutbox_post, name="shoutbox_post"),
    path("moderators/", views.moderator_manage, name="moderator_manage"),
    path(
        "moderators/<int:pk>/remove/", views.moderator_remove, name="moderator_remove"
    ),
]
