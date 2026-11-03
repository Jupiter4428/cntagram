"""Protected downloads: the server, never a public media URL, serves the file."""
from django.views.decorators.http import require_GET
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from .services import record_download
from .selectors import published_documents
from .views import open_document_pdf


@require_GET
def document_download(request, document_id):
    document = get_object_or_404(published_documents(), pk=document_id)
    stream, version = open_document_pdf(document)

    # A log is created only after the protected file was successfully opened.
    # Database failures close the stream rather than sending an unlogged file.
    try:
        record_download(document=document, user=request.user)
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
