from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("vault/", views.vault, name="vault"),
    path("approvals/", views.approval_queue, name="approval_queue"),
    path("approvals/<int:document_id>/", views.approval_review, name="approval_review"),
    path("approvals/<int:document_id>/preview/", views.approval_preview, name="approval_preview"),
]
