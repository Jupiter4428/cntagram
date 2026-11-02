from django.utils.functional import SimpleLazyObject

from . import selectors


def approval_permissions(request):
    """Context processor exposing can_review_materials for navigation and UI."""

    def _get_can_review():
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return selectors.can_review_any(user=user)

    return {"can_review_materials": SimpleLazyObject(_get_can_review)}
