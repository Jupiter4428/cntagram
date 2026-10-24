# catalog/urls.py
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_update, name="department_update"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/add/", views.batch_create, name="batch_create"),
    path("batches/<int:pk>/delete/", views.batch_delete, name="batch_delete"),
    path("batches/<int:pk>/courses/", views.batch_course_manage, name="batch_course_manage"),
    path(
        "batches/<int:pk>/courses/<int:batch_course_pk>/remove/",
        views.batch_course_remove,
        name="batch_course_remove",
    ),
    path("courses/", views.course_list, name="course_list"),
    path("courses/add/", views.course_create, name="course_create"),
]