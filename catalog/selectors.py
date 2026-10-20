from .models import Department


def department_list():
    return Department.objects.order_by("code")