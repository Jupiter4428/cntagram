from django.contrib import admin

from .models import Batch, BatchCourse, Course, Department, SystemSetting


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name_th", "name_en", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name_th", "name_en"]


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ["code", "department", "number"]
    list_filter = ["department"]
    search_fields = ["department__code", "number"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["code", "name_th", "name_en"]
    search_fields = ["code", "name_th", "name_en"]


@admin.register(BatchCourse)
class BatchCourseAdmin(admin.ModelAdmin):
    list_display = ["batch", "course"]
    list_filter = ["batch__department"]
    search_fields = [
        "batch__department__code",
        "batch__number",
        "course__code",
        "course__name_en",
    ]
    autocomplete_fields = ["batch", "course"]


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]
