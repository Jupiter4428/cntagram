# Issue #73 — US-9 Frontend integration notes

This branch is deliberately based on `origin/develop` and contains **only frontend work plus a display-state helper**. Backend PR #62 (US-6), PR #51 (US-9), and FE Issue #69 are not merged yet. Do not merge this branch until dependencies are ready.

## Files prepared
- `materials/templates/materials/approval_queue.html`: show approved/missing roles, disabled review action and reason.
- `materials/templates/materials/approval_review.html`: show approval progress, hide review form when not eligible.
- `materials/approval_ui.py`: bulk attach display state, using `approval_progress_for` from US-9 and one query for already-reviewed docs.

## Required view integration after backend merge

In `materials/views.py`, import:
```python
from materials.approval_ui import attach_approval_ui
```

In `approval_queue`, **evaluate** the queryset and attach UI state before rendering:
```python
documents = attach_approval_ui(
    pending_documents_for_moderator(user=request.user), request.user
)
return render(request, "materials/approval_queue.html", {"documents": documents})
```

In `approval_review`, before rendering GET or failed POST:
```python
attach_approval_ui([document], request.user)
```

IMPORTANT: The template disables the form when `approval_ui` is absent. It must be supplied by the view. Server-side `review_document` remains authoritative and must validate every POST.

## Required checks
1. Integrate with PR #62, #51, and the FE #69 queue/review edits (resolve any template conflicts).
2. Run `python manage.py check` and `python manage.py test` on integrated branch.
3. Moderator: exam already approved by moderator => shows waiting for Super Admin and disabled button.
4. Moderator: legacy exam batch <= configured `legacy_batch_max` => disabled button with reason.
5. Super Admin: permitted to review where required, but cannot approve own document or repeat a decision.
6. Ensure missing roles and approved roles display correct Thai names, no `|safe`, and no N+1 query.
7. Test mobile layout and FE #69 PDF preview/403 behavior.
8. After all pass, PR description should include `Closes #73`; do not commit/push until explicitly requested.
