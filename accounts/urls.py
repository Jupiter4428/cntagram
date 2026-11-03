from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("account/delete/", views.delete_account, name="delete_account"),
    path("moderators/", views.moderator_manage, name="moderator_manage"),
    path("moderators/<int:pk>/remove/", views.moderator_remove, name="moderator_remove"),
    path("audio/<path:filename>", views.serve_audio_stream, name="audio_stream"),
]