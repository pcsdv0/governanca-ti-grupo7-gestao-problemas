"""
Controle de acesso por perfil.

Uso em views de função:

    @perfil_requerido(Perfil.GESTOR_TI)
    def aprovar_encerramento(request, pk): ...

Uso em views de classe:

    class ProblemaCreateView(PerfilRequeridoMixin, CreateView):
        perfis_permitidos = [Perfil.SUPORTE, Perfil.GESTOR_TI]

Regras:
- usuário não logado é enviado para a tela de login;
- usuário logado sem um dos perfis permitidos recebe 403 (acesso negado);
- superusuário (administrador do Django) sempre tem acesso.
"""

from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def usuario_tem_perfil(usuario, perfis):
    """Retorna True se o usuário pode acessar uma tela restrita a `perfis`."""
    return usuario.is_superuser or usuario.perfil in perfis


def perfil_requerido(*perfis):
    """Decorator que restringe a view aos perfis informados."""

    def decorator(view):
        @wraps(view)
        def _view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not usuario_tem_perfil(request.user, perfis):
                raise PermissionDenied("Seu perfil não tem acesso a esta página.")
            return view(request, *args, **kwargs)

        return _view

    return decorator


class PerfilRequeridoMixin(AccessMixin):
    """Versão para views de classe. Defina `perfis_permitidos` na view."""

    perfis_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not usuario_tem_perfil(request.user, self.perfis_permitidos):
            raise PermissionDenied("Seu perfil não tem acesso a esta página.")
        return super().dispatch(request, *args, **kwargs)
