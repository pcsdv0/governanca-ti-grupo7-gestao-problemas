"""Teste do comando carregar_demo (dados de demonstração da F6)."""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from contas.models import Usuario
from dashboard.services import indicadores
from incidentes.models import Incidente

from .constantes import StatusProblema
from .models import Problema


class CarregarDemoTests(TestCase):
    def test_carrega_pelos_servicos_com_validacao_e_nao_duplica(self):
        call_command("carregar_demo", stdout=StringIO())
        self.assertEqual(Incidente.objects.count(), 13)
        self.assertEqual(
            list(Problema.objects.order_by("pk").values_list("status", flat=True)),
            [StatusProblema.EM_CORRECAO, StatusProblema.EM_INVESTIGACAO, StatusProblema.ENCERRADO],
        )
        encerrado = Problema.objects.get(status=StatusProblema.ENCERRADO)
        # RF13: o encerramento só ocorreu depois da validação do Responsável pelo sistema
        self.assertEqual(encerrado.validado_por, encerrado.sistema.responsavel)
        self.assertEqual(encerrado.historico_status.count(), 6)

        # O dashboard já tem o que mostrar: alerta de recorrência e ações no prazo
        dados = indicadores(usuario=Usuario.objects.get(username="gestor"))
        self.assertTrue(dados["alertas"])
        self.assertIsNotNone(dados["percentual_acoes_no_prazo"])

        call_command("carregar_demo", stdout=StringIO())
        self.assertEqual(Incidente.objects.count(), 13)
