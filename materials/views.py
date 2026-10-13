from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def vault(request):
    """Protected entry point for the document vault."""
    return render(request, "materials/vault.html")
