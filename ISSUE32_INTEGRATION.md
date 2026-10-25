# Issue #32 — US-8 Frontend integration

This branch is based on the frontend #77 branch, not on develop. Do not merge this branch as-is until #77 is merged or the branch is rebased to develop and its diff reviewed.

## Template contract

The backend document_detail view should provide:
- `download_url`: a URL to the **server-side protected** download endpoint only when the current user may download the published document. Leave unset/None otherwise. Never use a raw media/file URL.
- `download_count`: an integer from download logs (including 0), or None if not available.
- `download_error`: a user-friendly, escaped error message when access is denied or the file is unavailable.

The template disables the button if no authorized download URL is provided. Backend must enforce authentication, publication status and permissions independently of UI. Download count must increment on the backend only after a successful download, not when displaying or clicking UI.

## Remaining work
- Wait for backend US-8 endpoint and download log implementation.
- Connect the actual view context and endpoint, verify 401/403/404 as appropriate.
- Test signed-in published, pending, guest and denied scenarios; check count after successful download.
- Run integration tests and responsive browser checks before PR/merge.
