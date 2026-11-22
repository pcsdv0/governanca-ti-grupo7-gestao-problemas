from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Perfil, Usuario
from sistemas.models import Sistema

from .constantes import ImpactoIncidente
from .models import Incidente


class IncidenteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            perfil: Usuario.objects.create_user(username=perfil.lower(), perfil=perfil)
            for perfil in Perfil
        }
        cls.suporte = cls.usuarios[Perfil.SUPORTE]
        cls.gestor = cls.usuarios[Perfil.GESTOR_TI]
        cls.responsavel = cls.usuarios[Perfil.RESPONSAVEL_SISTEMA]
        cls.outro_suporte = Usuario.objects.create_user("outro_suporte", perfil=Perfil.SUPORTE)
        cls.outro_responsavel = Usuario.objects.create_user(
            "outro_responsavel", perfil=Perfil.RESPONSAVEL_SISTEMA
        )
        cls.admin = Usuario.objects.create_superuser("admin", password=None)
        cls.sistema = Sistema.objects.create(
            nome="Biblioteca", descricao="Livros", responsavel=cls.responsavel
        )
        cls.outro_sistema = Sistema.objects.create(
            nome="Portal acadêmico", descricao="Notas", responsavel=cls.outro_responsavel
        )
        cls.ocorrencia = datetime(2026, 11, 8, 14, 35, 42, tzinfo=ZoneInfo("America/Recife"))
        cls.incidente = Incidente.objects.create(
            titulo="Falha na consulta",
            descricao="Não carrega o catálogo.",
            data_ocorrencia=cls.ocorrencia,
            impacto=ImpactoIncidente.MEDIO,
            sistema=cls.sistema,
            registrado_por=cls.suporte,
        )
        cls.outro_incidente = Incidente.objects.create(
            titulo="Notas indisponíveis",
            descricao="Página não abre.",
            data_ocorrencia=cls.ocorrencia,
            impacto=ImpactoIncidente.ALTO,
            sistema=cls.outro_sistema,
            registrado_por=cls.outro_suporte,
        )

    def setUp(self):
        self.lista_url = reverse("incidentes:listar")
        self.cadastro_url = reverse("incidentes:cadastrar")
        self.edicao_url = reverse("incidentes:editar", args=[self.incidente.pk])
        self.dados = {
            "titulo": "Falha ao emprestar",
            "descricao": "O empréstimo não conclui.",
            "data_ocorrencia": "2026-11-08T14:35:42",
            "impacto": ImpactoIncidente.BAIXO,
            "sistema": self.sistema.pk,
        }

    def test_impactos_iguais_as_convencoes(self):
        self.assertEqual(
            ImpactoIncidente.choices,
            [("BAIXO", "Baixo"), ("MEDIO", "Médio"), ("ALTO", "Alto")],
        )

    def test_anonimos_seguem_para_login_sem_gravacao(self):
        for url in (self.lista_url, self.cadastro_url, self.edicao_url):
            for metodo in ("get", "post"):
                with self.subTest(url=url, metodo=metodo):
                    resposta = getattr(self.client, metodo)(url)
                    self.assertRedirects(resposta, f"{reverse('contas:login')}?next={url}")
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_cadastro_exclusivo_para_suporte_e_superusuario(self):
        for perfil, usuario in self.usuarios.items():
            self.client.force_login(usuario)
            esperado = 200 if perfil == Perfil.SUPORTE else 403
            self.assertEqual(self.client.get(self.cadastro_url).status_code, esperado)
            if perfil != Perfil.SUPORTE:
                with self.subTest(perfil=perfil):
                    self.assertEqual(
                        self.client.post(self.cadastro_url, self.dados).status_code, 403
                    )
        self.assertEqual(Incidente.objects.count(), 2)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.cadastro_url).status_code, 200)
        self.assertRedirects(self.client.post(self.cadastro_url, self.dados), self.lista_url)
        criado = Incidente.objects.get(titulo=self.dados["titulo"])
        self.assertEqual(criado.registrado_por, self.admin)
        self.assertEqual(criado.history.get().history_user, self.admin)

    def test_cadastro_persiste_campos_autor_e_auditoria(self):
        self.client.force_login(self.suporte)
        resposta = self.client.post(
            self.cadastro_url,
            {
                **self.dados,
                "registrado_por": self.gestor.pk,
                "registrado_por_id": self.gestor.pk,
                "history_user": self.gestor.pk,
            },
            follow=True,
        )
        self.assertRedirects(resposta, self.lista_url)
        self.assertContains(resposta, "Incidente registrado com sucesso.")
        criado = Incidente.objects.get(titulo=self.dados["titulo"])
        self.assertEqual(criado.descricao, self.dados["descricao"])
        self.assertEqual(criado.data_ocorrencia, self.ocorrencia)
        self.assertTrue(timezone.is_aware(criado.data_ocorrencia))
        self.assertEqual(criado.impacto, ImpactoIncidente.BAIXO)
        self.assertEqual(criado.sistema, self.sistema)
        self.assertEqual(criado.registrado_por, self.suporte)
        historico = criado.history.get()
        self.assertEqual(historico.history_type, "+")
        self.assertEqual(historico.history_user, self.suporte)
        self.assertEqual(historico.registrado_por_id, self.suporte.pk)

    def test_edicao_por_autor_gestor_e_superusuario_preserva_autor(self):
        for editor in (self.suporte, self.gestor, self.admin):
            self.client.force_login(editor)
            with self.subTest(editor=editor):
                self.assertEqual(self.client.get(self.edicao_url).status_code, 200)
                resposta = self.client.post(
                    self.edicao_url,
                    {
                        **self.dados,
                        "titulo": f"Corrigido por {editor.username}",
                        "sistema": self.outro_sistema.pk,
                        "impacto": ImpactoIncidente.ALTO,
                        "registrado_por": self.outro_suporte.pk,
                        "registrado_por_id": self.outro_suporte.pk,
                    },
                    follow=True,
                )
                self.assertRedirects(resposta, self.lista_url)
                self.assertContains(resposta, "Incidente atualizado com sucesso.")
                self.incidente.refresh_from_db()
                self.assertEqual(self.incidente.titulo, f"Corrigido por {editor.username}")
                self.assertEqual(self.incidente.sistema, self.outro_sistema)
                self.assertEqual(self.incidente.impacto, ImpactoIncidente.ALTO)
                self.assertEqual(self.incidente.registrado_por, self.suporte)
                historico = self.incidente.history.latest()
                self.assertEqual(historico.history_user, editor)
                self.assertEqual(historico.registrado_por_id, self.suporte.pk)
                self.assertEqual(historico.history_type, "~")
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 4)
        original = self.incidente.history.earliest()
        self.assertEqual(original.titulo, "Falha na consulta")
        self.assertEqual(original.sistema_id, self.sistema.pk)

    def test_edicao_de_outro_autor_e_perfis_sem_permissao_retornam_403(self):
        for usuario in (
            self.outro_suporte,
            self.usuarios[Perfil.DESENVOLVEDOR],
            self.responsavel,
        ):
            self.client.force_login(usuario)
            for metodo in ("get", "post"):
                with self.subTest(usuario=usuario, metodo=metodo):
                    resposta = getattr(self.client, metodo)(self.edicao_url, self.dados)
                    self.assertEqual(resposta.status_code, 403)
        self.incidente.refresh_from_db()
        self.assertEqual(self.incidente.titulo, "Falha na consulta")
        self.assertEqual(self.incidente.registrado_por, self.suporte)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_validacao_de_obrigatorios_no_cadastro_e_na_edicao(self):
        self.client.force_login(self.suporte)
        for url in (self.cadastro_url, self.edicao_url):
            for campo in self.dados:
                with self.subTest(url=url, campo=campo):
                    resposta = self.client.post(url, {**self.dados, campo: ""})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertIn(campo, resposta.context["form"].errors)
                    self.assertContains(resposta, "Este campo é obrigatório.")
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_campos_invalidos_nao_gravam_nem_geram_historico(self):
        self.client.force_login(self.suporte)
        casos = (
            ("titulo", "x" * 201),
            ("titulo", "  "),
            ("descricao", "  "),
            ("impacto", "CRITICO"),
            ("sistema", 999999),
            ("data_ocorrencia", "data inválida"),
        )
        for url in (self.cadastro_url, self.edicao_url):
            for campo, valor in casos:
                with self.subTest(url=url, campo=campo):
                    resposta = self.client.post(url, {**self.dados, campo: valor})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertIn(campo, resposta.context["form"].errors)
        self.incidente.refresh_from_db()
        self.assertEqual(self.incidente.titulo, "Falha na consulta")
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_todos_os_impactos_confirmados_sao_aceitos(self):
        self.client.force_login(self.suporte)
        for impacto in ImpactoIncidente:
            with self.subTest(impacto=impacto):
                resposta = self.client.post(
                    self.cadastro_url, {**self.dados, "titulo": impacto.label, "impacto": impacto}
                )
                self.assertRedirects(resposta, self.lista_url)
                self.assertEqual(Incidente.objects.get(titulo=impacto.label).impacto, impacto)

    def test_datas_passadas_e_futuras_nao_recebem_restricao_extra(self):
        self.client.force_login(self.suporte)
        for data in ("2020-01-01T00:00", "2099-12-31T23:59"):
            with self.subTest(data=data):
                resposta = self.client.post(
                    self.cadastro_url, {**self.dados, "data_ocorrencia": data}
                )
                self.assertRedirects(resposta, self.lista_url)

    def test_get_nao_grava_e_edicao_preserva_horario_local_com_segundos(self):
        self.client.force_login(self.suporte)
        self.client.get(self.cadastro_url, self.dados)
        resposta = self.client.get(self.edicao_url)
        self.assertContains(resposta, 'value="2026-11-08T14:35:42"')
        self.assertNotIn("registrado_por", resposta.context["form"].fields)
        self.assertNotContains(resposta, 'name="registrado_por"')
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_incidente_inexistente_retorna_404(self):
        self.client.force_login(self.suporte)
        url = reverse("incidentes:editar", args=[999999])
        for metodo in ("get", "post"):
            with self.subTest(metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(url, self.dados).status_code, 404)

    def test_metodos_nao_previstos_nao_gravam(self):
        self.client.force_login(self.suporte)
        self.assertEqual(self.client.post(self.lista_url, self.dados).status_code, 405)
        for url in (self.cadastro_url, self.edicao_url):
            for metodo in ("put", "patch", "delete"):
                with self.subTest(url=url, metodo=metodo):
                    self.assertEqual(getattr(self.client, metodo)(url).status_code, 405)
        self.assertEqual(Incidente.objects.count(), 2)
        self.assertEqual(self.incidente.history.count(), 1)

    def test_csrf_obrigatorio_para_cadastrar_e_editar(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.suporte)
        for url in (self.cadastro_url, self.edicao_url):
            with self.subTest(url=url):
                self.assertEqual(cliente.post(url, self.dados).status_code, 403)
                self.assertContains(cliente.get(url), 'name="csrfmiddlewaretoken"')
                token = cliente.cookies["csrftoken"].value
                self.assertEqual(
                    cliente.post(url, {**self.dados, "csrfmiddlewaretoken": token}).status_code,
                    302,
                )

    def test_listagem_liberada_para_perfis_confirmados_e_superusuario(self):
        for usuario in (self.suporte, self.usuarios[Perfil.DESENVOLVEDOR], self.gestor, self.admin):
            self.client.force_login(usuario)
            with self.subTest(usuario=usuario):
                resposta = self.client.get(self.lista_url)
                self.assertContains(resposta, "Falha na consulta")
                self.assertContains(resposta, "Notas indisponíveis")

    def test_responsavel_consulta_apenas_incidentes_dos_seus_sistemas(self):
        self.client.force_login(self.responsavel)
        resposta = self.client.get(self.lista_url)
        self.assertContains(resposta, "Falha na consulta")
        self.assertNotContains(resposta, "Notas indisponíveis")
        self.assertNotContains(resposta, self.outro_sistema.nome)
        self.assertQuerySetEqual(
            resposta.context["form"].fields["sistema"].queryset, [self.sistema]
        )
        resposta = self.client.get(self.lista_url, {"sistema": self.outro_sistema.pk})
        self.assertIn("sistema", resposta.context["form"].errors)
        self.assertNotContains(resposta, "Notas indisponíveis")
        self.assertFalse(resposta.context["incidentes"])

    def test_responsavel_sem_sistemas_nao_ve_incidentes(self):
        usuario = Usuario.objects.create_user("sem_sistema", perfil=Perfil.RESPONSAVEL_SISTEMA)
        self.client.force_login(usuario)
        resposta = self.client.get(self.lista_url)
        self.assertContains(resposta, "Nenhum incidente encontrado.")
        self.assertFalse(resposta.context["form"].fields["sistema"].queryset.exists())

    def test_links_de_acoes_respeitam_perfil_e_autoria(self):
        outra_edicao = reverse("incidentes:editar", args=[self.outro_incidente.pk])
        for usuario in (*self.usuarios.values(), self.admin):
            self.client.force_login(usuario)
            with self.subTest(usuario=usuario):
                resposta = self.client.get(self.lista_url)
                if usuario == self.suporte or usuario.is_superuser:
                    self.assertContains(resposta, f'href="{self.cadastro_url}"')
                else:
                    self.assertNotContains(resposta, f'href="{self.cadastro_url}"')
                if usuario in (self.suporte, self.gestor, self.admin):
                    self.assertContains(resposta, f'href="{self.edicao_url}"')
                else:
                    self.assertNotContains(resposta, f'href="{self.edicao_url}"')
                if usuario in (self.gestor, self.admin):
                    self.assertContains(resposta, f'href="{outra_edicao}"')
                else:
                    self.assertNotContains(resposta, f'href="{outra_edicao}"')

    def test_filtro_por_sistema(self):
        self.client.force_login(self.gestor)
        resposta = self.client.get(self.lista_url, {"sistema": self.sistema.pk})
        self.assertContains(resposta, "Falha na consulta")
        self.assertNotContains(resposta, "Notas indisponíveis")

    def test_filtro_de_periodo_inclui_dias_completos_no_fuso_local(self):
        inicio = self.ocorrencia.replace(hour=0, minute=0, second=0)
        datas = {
            "Antes do período": inicio - timedelta(microseconds=1),
            "Início do período": inicio,
            "Fim do período": inicio + timedelta(days=1) - timedelta(microseconds=1),
            "Depois do período": inicio + timedelta(days=1),
            "UTC no dia seguinte": datetime(2026, 11, 9, 1, 0, tzinfo=UTC),
        }
        for titulo, data in datas.items():
            Incidente.objects.create(
                titulo=titulo,
                descricao="Teste de período",
                data_ocorrencia=data,
                impacto=ImpactoIncidente.BAIXO,
                sistema=self.sistema,
                registrado_por=self.suporte,
            )
        self.client.force_login(self.gestor)
        resposta = self.client.get(
            self.lista_url,
            {"data_inicio": "2026-11-08", "data_fim": "2026-11-08", "sistema": self.sistema.pk},
        )
        for titulo in ("Início do período", "Fim do período", "UTC no dia seguinte"):
            self.assertContains(resposta, titulo)
        for titulo in ("Antes do período", "Depois do período", "Notas indisponíveis"):
            self.assertNotContains(resposta, titulo)
        self.assertContains(resposta, "Falha na consulta")

    def test_limites_de_periodo_sao_opcionais(self):
        self.client.force_login(self.gestor)
        casos = (
            ({"data_inicio": "2026-11-08"}, True),
            ({"data_fim": "2026-11-08"}, True),
            ({"data_inicio": "2026-11-09"}, False),
            ({"data_fim": "2026-11-07"}, False),
        )
        for filtros, encontrado in casos:
            with self.subTest(filtros=filtros):
                resposta = self.client.get(self.lista_url, filtros)
                self.assertEqual(bool(resposta.context["incidentes"]), encontrado)

    def test_filtros_invalidos_mostram_erros_sem_expor_resultados(self):
        self.client.force_login(self.gestor)
        for filtros in (
            {"data_inicio": "inválida"},
            {"data_fim": "2026-02-30"},
            {"data_inicio": "2026-11-09", "data_fim": "2026-11-08"},
            {"sistema": 999999},
        ):
            with self.subTest(filtros=filtros):
                resposta = self.client.get(self.lista_url, filtros)
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context["form"].errors)
                self.assertContains(resposta, "Confira os filtros")
                self.assertNotContains(resposta, "Falha na consulta")
                self.assertNotContains(resposta, "Notas indisponíveis")

    def test_listagem_escapa_html_informado_pelo_usuario(self):
        self.client.force_login(self.suporte)
        self.client.post(
            self.cadastro_url, {**self.dados, "descricao": "<script>alert(1)</script>"}
        )
        resposta = self.client.get(self.lista_url)
        self.assertNotContains(resposta, "<script>alert(1)</script>")
        self.assertContains(resposta, "&lt;script&gt;alert(1)&lt;/script&gt;")
