from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("vault/", views.vault, name="vault"),
    path("documents/<int:document_id>/", views.document_detail, name="document_detail"),
    path(
        "documents/<int:document_id>/preview/",
        views.document_preview,
        name="document_preview",
    ),
    path("upload/", views.upload, name="upload"),
    path("upload/done/", views.upload_done, name="upload_done"),
    path(
        "upload/batches/<int:batch_id>/courses/",
        views.upload_course_options,
        name="upload_course_options",
    ),
    path("approvals/", views.approval_queue, name="approval_queue"),
    path("approvals/<int:document_id>/", views.approval_review, name="approval_review"),
    path(
        "approvals/<int:document_id>/preview/",
        views.approval_document_preview,
        name="approval_preview",
    ),
]
