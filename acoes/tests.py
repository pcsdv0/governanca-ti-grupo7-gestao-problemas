# TODO Função 2 (F2): modelo AçãoCorretiva (choices em acoes/constantes.py).
# Nomes padronizados: docs/convencoes.md. Modelo de dados: docs/modelo-de-dados.md.

from django.test import SimpleTestCase

from acoes.constantes import StatusAcaoCorretiva


class StatusAcaoCorretivaTests(SimpleTestCase):
    """Garante que os status continuam idênticos a docs/convencoes.md."""

    def test_status_iguais_as_convencoes(self):
        self.assertEqual(
            StatusAcaoCorretiva.choices,
            [
                ("ABERTA", "Aberta"),
                ("EM_ANDAMENTO", "Em andamento"),
                ("CONCLUIDA", "Concluída"),
            ],
        )
