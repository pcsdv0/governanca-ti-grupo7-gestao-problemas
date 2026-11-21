from datetime import UTC, datetime, timedelta

from django.test import TestCase
from django.urls import reverse

from acoes.constantes import StatusAcaoCorretiva
from acoes.models import AcaoCorretiva
from contas.models import Perfil, Usuario
from incidentes.models import Incidente
from problemas.constantes import StatusProblema
from problemas.models import HistoricoStatus, Problema
from sistemas.models import Sistema

from .services import indicadores


class PainelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestor = Usuario.objects.create_user("gestor", perfil=Perfil.GESTOR_TI)
        cls.dev = Usuario.objects.create_user("dev", perfil=Perfil.DESENVOLVEDOR)
        cls.dono = Usuario.objects.create_user("dono", perfil=Perfil.RESPONSAVEL_SISTEMA)
        cls.sistema = Sistema.objects.create(nome="Portal", responsavel=cls.dono)
        cls.outro = Sistema.objects.create(nome="E-mail", responsavel=cls.dono)
        cls.agora = datetime(2026, 11, 21, 15, tzinfo=UTC)

    def incidente(self, titulo, quando, sistema=None, problema=None):
        return Incidente.objects.create(
            titulo=titulo,
            problema=problema,
            sistema=sistema or self.sistema,
            data_ocorrencia=quando,
            registrado_por=self.dev,
            impacto="ALTO",
        )

    def test_painel_vazio_e_permissoes(self):
        url = reverse("dashboard:painel")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.dev)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.gestor)
        resposta = self.client.get(url)
        self.assertContains(resposta, "Sem dados")
        self.assertEqual(resposta.context["problemas_abertos"], 0)
        self.assertEqual(resposta.context["alertas"], [])

    def test_limites_da_janela_agrupamento_e_contagens(self):
        problema = Problema.objects.create(sistema=self.sistema, titulo="Pool")
        inicio = self.agora - timedelta(days=30)
        self.incidente("Queda", inicio, problema=problema)
        self.incidente("TIMEOUT", self.agora, problema=problema)
        self.incidente(" Timeout ", self.agora, problema=problema)
        self.incidente("timeout", self.agora)
        self.incidente("queda", inicio - timedelta(microseconds=1))
        self.incidente("queda", self.agora + timedelta(microseconds=1))
        self.incidente("timeout", self.agora, self.outro)
        dados = indicadores(usuario=self.gestor, agora=self.agora)
        self.assertEqual(sorted(a["quantidade"] for a in dados["alertas"]), [3, 3])
        por_sistema = {s.pk: s for s in dados["por_sistema"]}
        self.assertEqual(por_sistema[self.sistema.pk].incidentes_recorrentes, 4)
        self.assertEqual(por_sistema[self.outro.pk].incidentes_recorrentes, 0)
        self.assertEqual(por_sistema[self.sistema.pk].total_incidentes, 6)
        self.assertEqual(por_sistema[self.sistema.pk].total_problemas, 1)
        self.assertEqual(
            dados["por_status"][0], {"nome": "Registrado", "problemas": 1, "incidentes": 3}
        )
        self.assertEqual(dados["por_problema"].get().incidentes_vinculados, 3)
        self.assertEqual(dados["incidentes_sem_problema"], 4)

    def test_tempo_de_resolucao_e_percentual_no_fuso_do_projeto(self):
        problema = Problema.objects.create(sistema=self.sistema, titulo="Queda")
        abertura = self.agora - timedelta(hours=5)
        resolucao = abertura + timedelta(hours=3)
        HistoricoStatus.objects.filter(problema=problema).update(data_alteracao=abertura)
        problema.status = StatusProblema.RESOLVIDO
        problema.save()
        HistoricoStatus.objects.filter(problema=problema, status_novo="RESOLVIDO").update(
            data_alteracao=resolucao
        )
        # 01:00 UTC já é o dia seguinte em UTC, mas ainda é o dia do prazo em Recife.
        data = datetime(2026, 11, 21, 1, tzinfo=UTC)
        for prazo in (data.date() - timedelta(days=1), data.date() - timedelta(days=2)):
            acao = AcaoCorretiva.objects.create(
                problema=problema,
                responsavel=self.dev,
                prazo=prazo,
                descricao="Reparo",
                status=StatusAcaoCorretiva.CONCLUIDA,
            )
            acao.history.update(history_date=data)
        dados = indicadores(usuario=self.gestor, agora=self.agora)
        self.assertEqual(dados["tempo_medio_horas"], 3)
        self.assertEqual(dados["percentual_acoes_no_prazo"], 50)
        self.assertEqual(dados["problemas_abertos"], 0)

    def test_reincidencia_conta_problema_uma_vez_so_apos_encerramento(self):
        resolucao = self.agora - timedelta(hours=2)
        encerramento = self.agora - timedelta(hours=1)
        problema = Problema.objects.create(sistema=self.sistema, titulo="Falha no portal")
        problema.status = StatusProblema.RESOLVIDO
        problema.save()
        HistoricoStatus.objects.filter(
            problema=problema, status_novo=StatusProblema.RESOLVIDO
        ).update(data_alteracao=resolucao)
        self.incidente("Após a resolução", resolucao + timedelta(minutes=10), problema=problema)

        def total():
            return indicadores(usuario=self.gestor, agora=self.agora)["problemas_reincidentes"]

        self.assertEqual(total(), 0)
        problema.status = StatusProblema.ENCERRADO
        problema.save()
        HistoricoStatus.objects.filter(
            problema=problema, status_novo=StatusProblema.ENCERRADO
        ).update(data_alteracao=encerramento)
        self.incidente("No instante do encerramento", encerramento, problema=problema)
        self.incidente("Ocorrência futura", self.agora + timedelta(seconds=1), problema=problema)
        self.incidente("Sem vínculo", self.agora)
        self.assertEqual(total(), 0)
        self.incidente(
            "Primeira reincidência", encerramento + timedelta(microseconds=1), problema=problema
        )
        self.assertEqual(total(), 1)
        self.incidente("Segunda reincidência", self.agora, problema=problema)
        self.assertEqual(total(), 1)
