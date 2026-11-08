import datetime

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone

from catalog.models import Batch, Course, Department

from .models import PollVote, Role, ShoutboxMessage, User, UserCounter, UserRole


def moderator_list():
    """ดึงรายชื่อ Moderator ทั้งหมดพร้อมข้อมูลเชื่อมโยง (ป้องกัน N+1 Queries)"""
    return (
        UserRole.objects.filter(role__code=Role.MODERATOR)
        .select_related("user", "granted_by", "department")
        .order_by("department__code", "user__email")
    )


def is_moderator_of_department(*, user, department):
    """ตรวจสอบว่าผู้ใช้เป็น Moderator ประจำภาควิชานั้นหรือไม่"""
    if not user or not user.is_authenticated:
        return False
    return UserRole.objects.filter(
        user=user,
        role__code=Role.MODERATOR,
        department=department,
    ).exists()


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
        rows.append(
            {
                "label": role.name_th,
                "count": role.count,
                "percent": percent,
                "offset": offset,
                "end": end,
            }
        )
        offset = end
    if rows:
        rows[-1]["end"] = 100
    return rows


def _new_user_counts(today):
    """ผู้ใช้ใหม่วันนี้ / สัปดาห์นี้ (เริ่มจันทร์) / เดือนนี้ / ปีนี้
    ใน aggregate เดียว และยอดสะสมทั้งหมด

    "ทั้งหมด" = ยอดสะสมผู้ใช้ที่เคยถูกสร้างจาก UserCounter ไม่ลดเมื่อลบหรือปิดใช้งาน
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
        **{
            key: Count("pk", filter=Q(created_at__gte=since(day)))
            for key, day in starts.items()
        },
    )
    counts["all"] = UserCounter.objects.get(
        pk=1
    ).total  # แถว pk=1 สร้างใน migration 0004
    return counts


USERS_PER_PAGE = 7


def _users_page(page):
    """ผู้ใช้ใหม่สุดก่อน หน้าละ 7 คน พร้อม role และจำนวนเอกสารที่อัปโหลด

    นับเอกสารผ่าน reverse relation `documents` (Document.uploader)
    จึงไม่ต้อง import materials (ADR 0001)
    """
    users = (
        User.objects.select_related("department")
        .prefetch_related("user_roles")
        .annotate(upload_count=Count("documents"))
        .order_by("-created_at", "-pk")
    )
    users_page = Paginator(users, USERS_PER_PAGE).get_page(page)
    # template เรียกเมธอดที่มีอาร์กิวเมนต์ไม่ได้
    # จึงเตรียมเลขหน้า (1 2 3 4 5 6 … 20) ไว้ให้
    users_page.elided_range = list(
        users_page.paginator.get_elided_page_range(
            users_page.number, on_each_side=5, on_ends=1
        )
    )
    return users_page


def admin_dashboard(*, today=None, page=1):
    """ข้อมูลสรุปสำหรับหน้า Dashboard ของ Super Admin"""
    new_users = _new_user_counts(today or timezone.localdate())
    return {
        "totals": {
            "users": new_users[
                "all"
            ],  # ยอดสะสมเดียวกับกล่องผู้ใช้ใหม่ ไม่ต้อง query ซ้ำ
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


POLL_QUESTION = "วิชาไหนโหดสุดเทอมนี้"
POLL_CHOICES = (
    ("math", "Engineering Math / Calculus"),
    ("dsa", "Data Structures & Algorithms"),
    ("circuit", "Circuit Analysis / Physics"),
)


def get_weekly_poll():
    """Return durable poll totals and percentages."""
    vote_counts = dict(
        PollVote.objects.values("choice")
        .annotate(n=Count("pk"))
        .values_list("choice", "n")
    )
    total_votes = sum(vote_counts.values())
    choices = []
    for key, label in POLL_CHOICES:
        votes = vote_counts.get(key, 0)
        choices.append(
            {
                "key": key,
                "label": label,
                "votes": votes,
                "percent": round(votes * 100 / total_votes) if total_votes else 0,
            }
        )
    return {"question": POLL_QUESTION, "total": total_votes, "choices": choices}


SHOUTBOX_MAX_MESSAGES = 30
DEFAULT_SHOUTBOX_MESSAGES = (
    {"author": "[CN21] พี่บอย", "text": "น้องๆ อย่าลืมทวนวงจรไฟฟ้านะ"},
    {"author": "[CN23] น้ำหวาน", "text": "ขอบคุณสำหรับชีทแคลคูลัสค่า!"},
    {"author": "[ME22] ก้อง", "text": "ใครมีแนวข้อสอบ Thermo ฝากอัปหน่อย"},
    {"author": "[CE24] เต้ย", "text": "สู้ๆ กับมิดเทอมทุกคนครับ"},
)


def get_shoutbox_messages():
    """Return the newest 30 persisted messages, or demo content when empty."""
    messages = list(
        ShoutboxMessage.objects.select_related("user__department").order_by(
            "-created_at", "-pk"
        )[:SHOUTBOX_MAX_MESSAGES]
    )
    if not messages:
        return list(DEFAULT_SHOUTBOX_MESSAGES)
    messages.reverse()
    return [
        {
            "author": (
                f"[{msg.user.department.code if msg.user.department else 'Member'}] "
                f"{msg.user.nickname}"
            ),
            "text": msg.text,
        }
        for msg in messages
    ]
