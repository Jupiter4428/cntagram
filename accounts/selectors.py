import datetime

from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.utils import timezone

from catalog.models import Batch, Course, Department

from .models import Role, User


def _role_counts():
    """จำนวนผู้ใช้ต่อ role เรียงมากไปน้อย พร้อม % และจุดเริ่ม/จบของชิ้นในกราฟโดนัท

    นับคนไม่ซ้ำ: moderator ที่ดูแลหลายภาคมีหลายแถวใน user_role แต่นับเป็นคนเดียว
    ชิ้นสุดท้ายจบที่ 100 เสมอ กันเศษจากการปัดทำให้โดนัทไม่ครบวง
    """
    roles = (
        Role.objects.annotate(count=Count("user_roles__user", distinct=True))
        .filter(count__gt=0)
        .order_by("-count", "code")
    )
    total = sum(role.count for role in roles)
    rows, offset = [], 0
    for role in roles:
        percent = round(role.count * 100 / total)
        end = offset + percent
        rows.append({"label": role.name_th, "count": role.count, "percent": percent, "offset": offset, "end": end})
        offset = end
    if rows:
        rows[-1]["end"] = 100
    return rows


def _new_user_counts(today):
    """ผู้ใช้ใหม่วันนี้ / สัปดาห์นี้ (เริ่มจันทร์) / เดือนนี้ / ปีนี้ / ทั้งหมด ใน query เดียว

    "ทั้งหมด" = ยอดสะสมผู้ใช้ที่เคยถูกสร้าง (pk ล่าสุด) เพิ่มทีละหนึ่งต่อการสร้าง ไม่ลดเมื่อลบหรือปิดใช้งาน
    """

    def since(day):
        return timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))

    starts = {
        "day": today,
        "week": today - datetime.timedelta(days=today.weekday()),
        "month": today.replace(day=1),
        "year": today.replace(month=1, day=1),
    }
    counts = User.objects.aggregate(
        **{key: Count("pk", filter=Q(created_at__gte=since(day))) for key, day in starts.items()},
        all=Max("pk"),
    )
    counts["all"] = counts["all"] or 0  # ยังไม่มีผู้ใช้ Max ได้ None
    return counts


USERS_PER_PAGE = 7


def _users_page(page):
    """ผู้ใช้ใหม่สุดก่อน หน้าละ 7 คน พร้อม role และจำนวนเอกสารที่อัปโหลด

    นับเอกสารผ่าน reverse relation `documents` (Document.uploader) จึงไม่ต้อง import materials (ADR 0001)
    """
    users = (
        User.objects.select_related("department")
        .prefetch_related("user_roles")
        .annotate(upload_count=Count("documents"))
        .order_by("-created_at", "-pk")
    )
    users_page = Paginator(users, USERS_PER_PAGE).get_page(page)
    # template เรียกเมธอดที่มีอาร์กิวเมนต์ไม่ได้ จึงเตรียมเลขหน้า (1 2 3 4 5 6 … 20) ไว้ให้
    users_page.elided_range = list(
        users_page.paginator.get_elided_page_range(users_page.number, on_each_side=5, on_ends=1)
    )
    return users_page


def admin_dashboard(*, today=None, page=1):
    """ข้อมูลสรุปสำหรับหน้า Dashboard ของ Super Admin"""
    new_users = _new_user_counts(today or timezone.localdate())
    return {
        "totals": {
            "users": new_users["all"],  # ยอดสะสมเดียวกับกล่องผู้ใช้ใหม่ ไม่ต้อง query ซ้ำ
            "departments": Department.objects.filter(is_active=True).count(),
            "batches": Batch.objects.count(),
            "courses": Course.objects.count(),
        },
        "roles": _role_counts(),
        "new_users": new_users,
        "users_page": _users_page(page),
        "departments": list(
            Department.objects.filter(is_active=True).annotate(
                user_count=Count("users", distinct=True),
                batch_count=Count("batches", distinct=True),
            )
        ),
    }
