from django.db.models import Count

from .models import Batch, BatchCourse, Course, Department


def department_list():
    return Department.objects.order_by("code")


def batch_list():
    # course_count ใช้แสดงจำนวนวิชาโดยไม่ต้อง query ทีละรุ่น
    return Batch.objects.annotate(course_count=Count("batch_courses")).order_by(
        "department__code", "number"
    )



def course_list():
    return Course.objects.order_by("code")


def batch_course_list(*, batch):
    return BatchCourse.objects.filter(batch=batch).order_by("course__code")
