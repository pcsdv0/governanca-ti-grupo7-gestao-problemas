# TODO Funções 1 e 2 (F1/F2): modelos Problema, CausaRaiz e HistóricoStatus;
# ciclo de status (choices em problemas/constantes.py).
# Nomes padronizados: docs/convencoes.md. Modelo de dados: docs/modelo-de-dados.md.

from django.test import SimpleTestCase

from problemas.constantes import StatusProblema


class StatusProblemaTests(SimpleTestCase):
    """Garante que os status continuam idênticos a docs/convencoes.md."""

    def test_status_iguais_as_convencoes(self):
        self.assertEqual(
            StatusProblema.choices,
            [
                ("REGISTRADO", "Registrado"),
                ("EM_INVESTIGACAO", "Em investigação"),
                ("ERRO_CONHECIDO", "Erro conhecido"),
                ("EM_CORRECAO", "Em correção"),
                ("RESOLVIDO", "Resolvido"),
                ("ENCERRADO", "Encerrado"),
            ],
        )
