from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("moderators/", views.moderator_manage, name="moderator_manage"),
    path("moderators/<int:pk>/remove/", views.moderator_remove, name="moderator_remove"),
]