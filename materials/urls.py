from django.urls import path

from . import views
from .downloads import document_download

app_name = "materials"

urlpatterns = [
    path('documents/<int:document_id>/download/', document_download, name='document_download'),
    path("vault/", views.vault, name="vault"),
    path("documents/<int:document_id>/", views.document_detail, name="document_detail"),
    path(
        "documents/<int:document_id>/preview/",
        views.document_preview,
        name="document_preview",
    ),
]
