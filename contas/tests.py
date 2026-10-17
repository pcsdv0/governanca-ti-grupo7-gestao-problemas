from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views import View

from .models import Perfil, Usuario
from .permissoes import PerfilRequeridoMixin, perfil_requerido

SENHA = "SenhaDeTeste#2026"


class PerfilTests(TestCase):
    def test_perfis_iguais_as_convencoes(self):
        """Os perfis precisam ser idênticos a docs/convencoes.md."""
        self.assertEqual(
            Perfil.choices,
            [
                ("SUPORTE", "Suporte"),
                ("DESENVOLVEDOR", "Desenvolvedor"),
                ("GESTOR_TI", "Gestor de TI"),
                ("RESPONSAVEL_SISTEMA", "Responsável pelo sistema"),
            ],
        )

    def test_perfil_padrao_e_suporte(self):
        usuario = Usuario.objects.create_user("novo", password=SENHA)
        self.assertEqual(usuario.perfil, Perfil.SUPORTE)


class LoginTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            "ana",
            password=SENHA,
            first_name="Ana",
            last_name="Silva",
            perfil=Perfil.GESTOR_TI,
        )

    def test_pagina_de_login_abre(self):
        resposta = self.client.get(reverse("contas:login"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Entrar")

    def test_inicio_exige_login(self):
        resposta = self.client.get(reverse("inicio"))
        self.assertRedirects(resposta, f"{reverse('contas:login')}?next=/")

    def test_login_valido_leva_para_inicio_com_nome_e_perfil(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "ana", "password": SENHA},
            follow=True,
        )
        self.assertRedirects(resposta, reverse("inicio"))
        self.assertContains(resposta, "Ana Silva")
        self.assertContains(resposta, "Gestor de TI")

    def test_login_invalido_permanece_na_tela(self):
        resposta = self.client.post(
            reverse("contas:login"), {"username": "ana", "password": "errada"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse("contas:logout"))
        self.assertRedirects(resposta, reverse("contas:login"))
        self.assertRedirects(
            self.client.get(reverse("inicio")), f"{reverse('contas:login')}?next=/"
        )


@perfil_requerido(Perfil.GESTOR_TI, Perfil.RESPONSAVEL_SISTEMA)
def view_restrita(request):
    return HttpResponse("ok")


class ViewRestritaDeClasse(PerfilRequeridoMixin, View):
    perfis_permitidos = [Perfil.GESTOR_TI]

    def get(self, request):
        return HttpResponse("ok")


class PerfilRequeridoTests(TestCase):
    """O controle de acesso por perfil deve bloquear acessos indevidos."""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, usuario):
        request = self.factory.get("/restrita/")
        request.user = usuario
        return request

    def _usuario(self, perfil, **extra):
        return Usuario.objects.create_user(f"u_{perfil}", password=SENHA, perfil=perfil, **extra)

    def test_anonimo_vai_para_login(self):
        resposta = view_restrita(self._request(AnonymousUser()))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("contas:login"), resposta.url)

    def test_perfil_nao_permitido_recebe_403(self):
        for perfil in (Perfil.SUPORTE, Perfil.DESENVOLVEDOR):
            with self.subTest(perfil=perfil), self.assertRaises(PermissionDenied):
                view_restrita(self._request(self._usuario(perfil)))

    def test_perfis_permitidos_acessam(self):
        for perfil in (Perfil.GESTOR_TI, Perfil.RESPONSAVEL_SISTEMA):
            with self.subTest(perfil=perfil):
                resposta = view_restrita(self._request(self._usuario(perfil)))
                self.assertEqual(resposta.status_code, 200)

    def test_superusuario_acessa(self):
        admin = Usuario.objects.create_superuser("admin", password=SENHA)
        self.assertEqual(view_restrita(self._request(admin)).status_code, 200)

    def test_mixin_bloqueia_e_libera(self):
        view = ViewRestritaDeClasse.as_view()
        self.assertEqual(view(self._request(AnonymousUser())).status_code, 302)
        with self.assertRaises(PermissionDenied):
            view(self._request(self._usuario(Perfil.SUPORTE)))
        self.assertEqual(view(self._request(self._usuario(Perfil.GESTOR_TI))).status_code, 200)
