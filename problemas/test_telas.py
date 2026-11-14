"""Aceite das telas da F3 com os templates reais e as rotas de config.urls.

Percorre o roteiro de docs/integracao-problemas-f3.md (Incidente → Problema →
CausaRaiz → ErroConhecido → AçãoCorretiva → Encerrado), cada etapa com o perfil
definido na Matriz RACI, e confere o que cada perfil vê nas telas.
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from acoes.models import AcaoCorretiva
from contas.models import Perfil, Usuario
from incidentes.models import Incidente
from sistemas.models import Sistema

from .constantes import StatusProblema
from .models import Problema


class TelasMvpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def usuario(login, perfil):
            return Usuario.objects.create_user(login, first_name=login.title(), perfil=perfil)

        cls.suporte = usuario("suporte", Perfil.SUPORTE)
        cls.dev = usuario("dev", Perfil.DESENVOLVEDOR)
        cls.gestor = usuario("gestor", Perfil.GESTOR_TI)
        cls.responsavel = usuario("responsavel", Perfil.RESPONSAVEL_SISTEMA)
        cls.outro_responsavel = usuario("responsavel2", Perfil.RESPONSAVEL_SISTEMA)
        cls.sistema = Sistema.objects.create(
            nome="Sistema de Matrícula", descricao="Matrícula on-line", responsavel=cls.responsavel
        )
        cls.sistema_externo = Sistema.objects.create(
            nome="E-mail institucional", descricao="Correio", responsavel=cls.outro_responsavel
        )
        cls.incidentes = [
            Incidente.objects.create(
                titulo=f"Queda {n}",
                descricao="Sistema fora do ar",
                data_ocorrencia=timezone.now(),
                impacto="ALTO",
                sistema=cls.sistema,
                registrado_por=cls.suporte,
            )
            for n in (1, 2)
        ]
        cls.incidente_externo = Incidente.objects.create(
            titulo="Caixa cheia",
            descricao="Cota excedida",
            data_ocorrencia=timezone.now(),
            impacto="BAIXO",
            sistema=cls.sistema_externo,
            registrado_por=cls.suporte,
        )

    def entrar(self, usuario):
        self.client.force_login(usuario)

    def test_fluxo_completo_pelas_telas(self):
        # Suporte: a lista oferece a seleção e a abertura do Problema com os selecionados
        self.entrar(self.suporte)
        lista = self.client.get(reverse("incidentes:listar"))
        self.assertContains(lista, "Abrir Problema com os selecionados")
        self.assertContains(lista, f"INC-{self.incidentes[0].pk:03d}")
        ids = [i.pk for i in self.incidentes]
        formulario = self.client.get(reverse("problemas:cadastrar"), {"incidentes": ids})
        self.assertRegex(
            formulario.content.decode(), rf'value="{ids[0]}" id="inc{ids[0]}"\s+checked'
        )
        resposta = self.client.post(
            reverse("problemas:cadastrar"),
            {"titulo": "Queda recorrente", "descricao": "Quedas no pico", "incidentes": ids},
            follow=True,
        )
        problema = Problema.objects.get()
        self.assertRedirects(resposta, reverse("problemas:detalhe", args=[problema.pk]))
        self.assertContains(resposta, f"PRB-{problema.pk:03d}")
        self.assertContains(resposta, "2 ocorrência(s)")
        self.assertNotContains(resposta, "Avançar para")  # Suporte não altera status

        # Gestor de TI: atribui responsável e prioridade (RF11) e inicia a investigação
        self.entrar(self.gestor)
        self.client.post(
            reverse("problemas:atribuir", args=[problema.pk]),
            {"responsavel": self.dev.pk, "prioridade": "ALTA"},
        )
        detalhe = self.client.get(reverse("problemas:detalhe", args=[problema.pk]))
        self.assertContains(detalhe, "Avançar para “Em investigação”")
        self.client.post(
            reverse("problemas:alterar_status", args=[problema.pk]),
            {"status": StatusProblema.EM_INVESTIGACAO},
        )

        # Desenvolvedor: CausaRaiz, ErroConhecido, AçãoCorretiva e avanço do ciclo
        self.entrar(self.dev)
        self.client.post(
            reverse("problemas:registrar_causa_raiz", args=[problema.pk]),
            {"descricao": "Pool de conexões esgotado", "analise_5_porques": "1. Cai no pico..."},
        )
        self.client.post(
            reverse("kedb:registrar", args=[problema.pk]),
            {"sintoma": "Fora do ar", "causa": "Pool", "solucao_contorno": "Reiniciar o serviço"},
        )
        for status in (StatusProblema.ERRO_CONHECIDO, StatusProblema.EM_CORRECAO):
            self.client.post(
                reverse("problemas:alterar_status", args=[problema.pk]), {"status": status}
            )
        self.client.post(
            reverse("acoes:cadastrar", args=[problema.pk]),
            {
                "descricao": "Fechar conexões",
                "prazo": date.today().isoformat(),
                "responsavel": self.dev.pk,
            },
        )
        acao = AcaoCorretiva.objects.get()
        detalhe = self.client.get(reverse("problemas:detalhe", args=[problema.pk]))
        self.assertContains(detalhe, "Marcar como Em andamento")
        self.assertContains(detalhe, "Reiniciar o serviço")
        for status in ("EM_ANDAMENTO", "CONCLUIDA"):
            self.client.post(reverse("acoes:alterar_status", args=[acao.pk]), {"status": status})
        self.client.post(
            reverse("problemas:alterar_status", args=[problema.pk]),
            {"status": StatusProblema.RESOLVIDO},
        )
        detalhe = self.client.get(reverse("problemas:detalhe", args=[problema.pk]))
        self.assertNotContains(detalhe, "Avançar para “Encerrado”")  # só o Gestor encerra

        # Gestor de TI: encerra e consulta o histórico
        self.entrar(self.gestor)
        resposta = self.client.post(
            reverse("problemas:alterar_status", args=[problema.pk]),
            {"status": StatusProblema.ENCERRADO},
            follow=True,
        )
        problema.refresh_from_db()
        self.assertEqual(problema.status, StatusProblema.ENCERRADO)
        self.assertContains(resposta, "Em correção → Resolvido")
        self.assertContains(resposta, "Resolvido → Encerrado")
        self.assertNotContains(resposta, "Criar AçãoCorretiva")

    def test_navegacao_por_perfil(self):
        self.entrar(self.suporte)
        inicio = self.client.get(reverse("inicio"))
        for url in ("incidentes:listar", "problemas:listar", "acoes:listar"):
            self.assertContains(inicio, reverse(url))
        self.assertNotContains(inicio, reverse("contas:usuarios"))
        self.entrar(self.gestor)
        inicio = self.client.get(reverse("inicio"))
        self.assertContains(inicio, reverse("contas:usuarios"))
        self.assertContains(inicio, reverse("sistemas:listar"))

    def test_lista_de_acoes_respeita_escopo_do_responsavel(self):
        externo = Problema.objects.create(
            titulo="Cota", descricao="x", sistema=self.sistema_externo
        )
        AcaoCorretiva.objects.create(
            descricao="Alerta de cota", prazo=date.today(), problema=externo, responsavel=self.dev
        )
        self.entrar(self.responsavel)
        self.assertNotContains(self.client.get(reverse("acoes:listar")), "Alerta de cota")
        self.entrar(self.outro_responsavel)
        self.assertContains(self.client.get(reverse("acoes:listar")), "Alerta de cota")

    def test_telas_principais_abrem_para_todos_os_perfis(self):
        for usuario in (self.suporte, self.dev, self.gestor, self.responsavel):
            self.entrar(usuario)
            for url in ("inicio", "incidentes:listar", "problemas:listar", "acoes:listar"):
                self.assertEqual(self.client.get(reverse(url)).status_code, 200, (usuario, url))


class CarregarDemoTests(TestCase):
    def test_carrega_dados_pelos_servicos_e_nao_duplica(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("carregar_demo", stdout=StringIO())
        self.assertEqual(Incidente.objects.count(), 13)
        self.assertEqual(
            list(Problema.objects.order_by("pk").values_list("status", flat=True)),
            [StatusProblema.EM_CORRECAO, StatusProblema.EM_INVESTIGACAO, StatusProblema.ENCERRADO],
        )
        encerrado = Problema.objects.get(status=StatusProblema.ENCERRADO)
        self.assertEqual(encerrado.historico_status.count(), 6)
        call_command("carregar_demo", stdout=StringIO())
        self.assertEqual(Incidente.objects.count(), 13)
