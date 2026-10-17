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
]
