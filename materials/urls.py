from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("vault/", views.vault, name="vault"),
    path("upload/", views.upload, name="upload"),
    path("upload/done/", views.upload_done, name="upload_done"),
    path(
        "upload/batches/<int:batch_id>/courses/",
        views.upload_course_options,
        name="upload_course_options",
    ),
]
