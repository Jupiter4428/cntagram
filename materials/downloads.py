"""Protected downloads: the server, never a public media URL, serves the file."""
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import DownloadLog
from .selectors import published_documents


@login_required
def document_download(request, document_id):
    document = get_object_or_404(published_documents(), pk=document_id)
    version = document.current_version
    if version is None:
        raise Http404("Document has no file")
    try:
        stream = default_storage.open(version.storage_path, "rb")
    except (OSError, ValueError):
        raise Http404("Document file unavailable")

    # A log is created only after the protected file was successfully opened.
    # Database failures close the stream rather than sending an unlogged file.
    try:
        with transaction.atomic():
            DownloadLog.objects.create(document=document, user=request.user)
    except Exception:
        stream.close()
        raise
    response = FileResponse(
        stream, as_attachment=True,
        content_type="application/pdf",
        filename=version.original_name,
    )
    response["Cache-Control"] = "private, no-store"
    return response
