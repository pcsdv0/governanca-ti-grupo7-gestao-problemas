from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inicio(request):
    """Página inicial: só para usuários logados."""
    return render(request, "inicio.html")
