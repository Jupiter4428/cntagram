from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path(
        "departments/<str:department_code>/batches/",
        views.batch_manage,
        name="batch_manage",
    ),
    path("batches/<int:batch_id>/delete/", views.batch_delete, name="batch_delete"),
    path(
        "batches/<int:batch_id>/courses/",
        views.batch_course_manage,
        name="batch_course_manage",
    ),
    path(
        "batch-courses/<int:batch_course_id>/remove/",
        views.batch_course_remove,
        name="batch_course_remove",
    ),
]
