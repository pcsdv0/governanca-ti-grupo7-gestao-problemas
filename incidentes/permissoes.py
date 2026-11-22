from contas.models import Perfil
from contas.permissoes import usuario_tem_perfil


def pode_editar_incidente(usuario, incidente):
    return usuario_tem_perfil(usuario, [Perfil.GESTOR_TI]) or (
        usuario.perfil == Perfil.SUPORTE and incidente.registrado_por_id == usuario.pk
    )
