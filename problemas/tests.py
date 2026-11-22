# Choices do ciclo de status. Testes do backend e do fluxo integrado do MVP:
# test_backend.py e test_mvp.py.
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
