from django.utils.functional import SimpleLazyObject

from . import selectors


def approval_permissions(request):
    """ส่ง can_review_materials ให้ทุก template ไว้แสดงลิงก์ Approval Queue

    ใช้ SimpleLazyObject จึง query เฉพาะหน้าที่ใช้ตัวแปรนี้จริง
    """
    return {
        "can_review_materials": SimpleLazyObject(
            lambda: selectors.can_review_any(user=getattr(request, "user", None))
        )
    }
