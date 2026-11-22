from django.test import TestCase
from django.urls import reverse

from contas.models import Perfil, Usuario
from problemas.models import Problema
from sistemas.models import Sistema

from .models import ErroConhecido


class PesquisaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {p: Usuario.objects.create_user(p, perfil=p) for p in Perfil}
        sistema = Sistema.objects.create(
            nome="Portal", responsavel=cls.usuarios[Perfil.RESPONSAVEL_SISTEMA]
        )
        problema = Problema.objects.create(sistema=sistema, titulo="Queda do portal")
        cls.erro = ErroConhecido.objects.create(
            problema=problema,
            sintoma="Timeout",
            causa="Pool esgotado",
            solucao_contorno="Reiniciar conexões",
        )

    def test_busca_por_palavra_nos_tres_campos_e_perfis(self):
        url = reverse("kedb:pesquisar")
        self.assertEqual(self.client.get(url).status_code, 302)
        for perfil, usuario in self.usuarios.items():
            self.client.force_login(usuario)
            if perfil in (Perfil.SUPORTE, Perfil.DESENVOLVEDOR):
                for termo in ("", "TIMEOUT", "pool", "reiniciar", " timeout   pool "):
                    self.assertContains(self.client.get(url, {"q": termo}), "Reiniciar conexões")
                self.assertNotContains(self.client.get(url, {"q": "outro"}), "Reiniciar conexões")
            else:
                self.assertEqual(self.client.get(url).status_code, 403)
