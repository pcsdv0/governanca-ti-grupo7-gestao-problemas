from copy import deepcopy
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse
from django.utils import timezone

from acoes.constantes import StatusAcaoCorretiva
from acoes.models import AcaoCorretiva
from acoes.services import alterar_status_acao, criar_acao
from contas.models import Perfil, Usuario
from incidentes.models import Incidente
from kedb.models import ErroConhecido
from kedb.services import registrar_erro_conhecido
from sistemas.models import Sistema

from . import test_backend
from .constantes import StatusProblema
from .models import CausaRaiz, HistoricoStatus, Problema
from .services import abrir_problema, alterar_status, registrar_causa_raiz

urlpatterns = [
    path("problemas/", include("problemas.urls")),
    path("acoes/", include("acoes.urls")),
    path("kedb/", include("kedb.urls")),
    path("", include("config.urls")),
]
TEMPLATES_TESTE = deepcopy(test_backend.TEMPLATES_TESTE)
TEMPLATES_TESTE[0]["OPTIONS"]["loaders"][0][1].update(
    {
        "acoes/form.html": "<form method='post'>{% csrf_token %}{{ form.as_p }}</form>",
        "kedb/form.html": "<form method='post'>{% csrf_token %}{{ form.as_p }}</form>",
    }
)


@override_settings(ROOT_URLCONF=__name__, TEMPLATES=TEMPLATES_TESTE)
class BackendMvpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            perfil: Usuario.objects.create_user(username=perfil, perfil=perfil) for perfil in Perfil
        }
        cls.suporte = cls.usuarios[Perfil.SUPORTE]
        cls.dev = cls.usuarios[Perfil.DESENVOLVEDOR]
        cls.gestor = cls.usuarios[Perfil.GESTOR_TI]
        cls.responsavel = cls.usuarios[Perfil.RESPONSAVEL_SISTEMA]
        cls.outro_dev = Usuario.objects.create_user("outro_dev", perfil=Perfil.DESENVOLVEDOR)
        cls.admin = Usuario.objects.create_superuser("admin", password=None)
        cls.outro_responsavel = Usuario.objects.create_user(
            "outro_responsavel",
            perfil=Perfil.RESPONSAVEL_SISTEMA,
        )
        cls.sistema = Sistema.objects.create(
            nome="Matrícula",
            descricao="Matrículas",
            responsavel=cls.responsavel,
        )
        cls.sistema_externo = Sistema.objects.create(
            nome="Outro sistema",
            descricao="Outro",
            responsavel=cls.outro_responsavel,
        )
        cls.problemas = []
        for sistema in (cls.sistema, cls.sistema_externo):
            incidente = Incidente.objects.create(
                titulo="Falha",
                descricao="Falha intermitente",
                data_ocorrencia=timezone.now(),
                impacto="ALTO",
                sistema=sistema,
                registrado_por=cls.suporte,
            )
            cls.problemas.append(
                abrir_problema(
                    usuario=cls.suporte,
                    titulo=sistema.nome,
                    descricao="Investigar",
                    incidentes_ids=[incidente.pk],
                )
            )
        cls.problema, cls.externo = cls.problemas

    def causa(self, **kwargs):
        dados = {
            "usuario": self.dev,
            "problema_id": self.problema.pk,
            "descricao": "Conexões não liberadas",
            "analise_5_porques": "1. Por que caiu? Conexões esgotadas.\n2. Por quê? Não liberadas.",
        }
        return registrar_causa_raiz(**(dados | kwargs))

    def erro(self, **kwargs):
        dados = {
            "usuario": self.dev,
            "problema_id": self.problema.pk,
            "sintoma": "Sistema indisponível",
            "causa": "Conexões esgotadas",
            "solucao_contorno": "Reiniciar o serviço temporariamente",
        }
        return registrar_erro_conhecido(**(dados | kwargs))

    def acao(self, **kwargs):
        dados = {
            "usuario": self.gestor,
            "problema_id": self.problema.pk,
            "descricao": "Liberar conexões",
            "prazo": date(2026, 11, 12),
            "responsavel_id": self.dev.pk,
        }
        return criar_acao(**(dados | kwargs))

    def concluir(self, acao, usuario=None):
        for status in (StatusAcaoCorretiva.EM_ANDAMENTO, StatusAcaoCorretiva.CONCLUIDA):
            alterar_status_acao(usuario=usuario or self.dev, acao_id=acao.pk, status=status)

    def resolver(self):
        for status in StatusProblema.values[1:-1]:
            alterar_status(usuario=self.dev, problema_id=self.problema.pk, status=status)

    def encerrar(self, usuario=None):
        return alterar_status(
            usuario=usuario or self.gestor,
            problema_id=self.problema.pk,
            status=StatusProblema.ENCERRADO,
        )

    def test_causa_e_erro_unicos_editaveis_auditados_sem_alterar_status(self):
        causa = self.causa()
        erro = self.erro()
        atualizada = self.causa(usuario=self.outro_dev, descricao="Diagnóstico revisado")
        atualizado = self.erro(usuario=self.outro_dev, solucao_contorno="Contorno revisado")
        self.assertEqual(atualizada.pk, causa.pk)
        self.assertEqual(atualizado.pk, erro.pk)
        for registro in (atualizada, atualizado):
            self.assertEqual(registro.history.count(), 2)
            self.assertEqual(registro.history.last().history_user, self.dev)
            self.assertEqual(registro.history.first().history_user, self.outro_dev)
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, StatusProblema.REGISTRADO)
        self.assertEqual(self.problema.historico_status.count(), 1)

    def test_unicidade_por_problema_tambem_garantida_no_banco(self):
        self.causa()
        self.erro()
        for modelo, campos in (
            (CausaRaiz, {"descricao": "Outra", "analise_5_porques": "Outra análise"}),
            (ErroConhecido, {"sintoma": "Outro", "causa": "Outra", "solucao_contorno": "Outro"}),
        ):
            with (
                self.subTest(modelo=modelo),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                modelo.objects.create(problema=self.problema, **campos)

    def test_documentacao_tecnica_exclusiva_desenvolvedor_com_excecao_superusuario(self):
        for metodo in (self.causa, self.erro):
            for usuario in (self.suporte, self.gestor, self.responsavel, AnonymousUser()):
                with (
                    self.subTest(metodo=metodo, usuario=usuario),
                    self.assertRaises(PermissionDenied),
                ):
                    metodo(usuario=usuario)
            registro = metodo(usuario=self.admin)
            self.assertEqual(registro.history.get().history_user, self.admin)

    def test_campos_textuais_obrigatorios_sem_registro_parcial(self):
        for metodo, campos in (
            (self.causa, ("descricao", "analise_5_porques")),
            (self.erro, ("sintoma", "causa", "solucao_contorno")),
        ):
            for campo in campos:
                with self.subTest(campo=campo), self.assertRaises(ValidationError):
                    metodo(**{campo: "  "})
        self.assertFalse(CausaRaiz.objects.exists())
        self.assertFalse(ErroConhecido.objects.exists())

    def test_criacao_acao_com_prazo_passado_responsavel_e_auditoria(self):
        acao = self.acao(prazo=date(2020, 1, 1))
        self.assertEqual(acao.status, StatusAcaoCorretiva.ABERTA)
        self.assertEqual(acao.responsavel, self.dev)
        self.assertEqual(acao.problema, self.problema)
        self.assertEqual(acao.prazo, date(2020, 1, 1))
        self.assertEqual(acao.history.get().history_user, self.gestor)
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, StatusProblema.REGISTRADO)

    def test_acao_requer_campos_validos_e_responsavel_desenvolvedor(self):
        for dados in (
            {"descricao": " "},
            {"prazo": None},
            {"prazo": "2026-02-30"},
            {"responsavel_id": None},
            {"responsavel_id": 999999},
            {"responsavel_id": self.gestor.pk},
            {"responsavel_id": self.responsavel.pk},
            {"responsavel_id": self.suporte.pk},
        ):
            with self.subTest(dados=dados), self.assertRaises(ValidationError):
                self.acao(**dados)
        self.assertFalse(AcaoCorretiva.objects.exists())
        self.assertFalse(AcaoCorretiva.history.exists())

    def test_matriz_de_perfis_das_acoes_e_outro_desenvolvedor(self):
        for usuario in (self.suporte, self.responsavel, AnonymousUser()):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                self.acao(usuario=usuario)
        for usuario in (self.gestor, self.dev, self.admin):
            self.acao(usuario=usuario)
        acao = self.acao()
        for usuario in (self.suporte, self.responsavel, self.gestor, AnonymousUser()):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                alterar_status_acao(
                    usuario=usuario,
                    acao_id=acao.pk,
                    status=StatusAcaoCorretiva.EM_ANDAMENTO,
                )
        self.concluir(acao, usuario=self.outro_dev)
        acao.refresh_from_db()
        self.assertEqual(acao.status, StatusAcaoCorretiva.CONCLUIDA)
        self.assertEqual(acao.responsavel, self.dev)
        self.assertEqual(acao.history.first().history_user, self.outro_dev)

    def test_status_sequencial_rejeita_saltos_repeticao_e_retorno(self):
        acao = self.acao()
        for status in ("CONCLUIDA", "ABERTA", "INVALIDO"):
            with self.subTest(status=status), self.assertRaises(ValidationError):
                alterar_status_acao(usuario=self.dev, acao_id=acao.pk, status=status)
        self.concluir(acao)
        for status in StatusAcaoCorretiva.values:
            with self.subTest(status=status), self.assertRaises(ValidationError):
                alterar_status_acao(usuario=self.dev, acao_id=acao.pk, status=status)
        self.assertEqual(
            list(
                acao.history.order_by("history_date", "history_id").values_list(
                    "status",
                    flat=True,
                )
            ),
            ["ABERTA", "EM_ANDAMENTO", "CONCLUIDA"],
        )
        self.assertEqual(acao.history.count(), 3)

    def test_encerramento_exige_ao_menos_uma_acao_e_todas_concluidas(self):
        self.resolver()
        with self.assertRaises(ValidationError) as contexto:
            self.encerrar()
        self.assertEqual(contexto.exception.code, "sem_acoes")
        primeira = self.acao()
        segunda = self.acao()
        self.concluir(primeira)
        with self.assertRaises(ValidationError) as contexto:
            self.encerrar()
        self.assertEqual(contexto.exception.code, "acoes_pendentes")
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, StatusProblema.RESOLVIDO)
        self.concluir(segunda)
        encerrado = self.encerrar()
        self.assertEqual(encerrado.status, StatusProblema.ENCERRADO)
        self.assertEqual(encerrado.history.first().history_user, self.gestor)
        evento = encerrado.historico_status.last()
        self.assertEqual((evento.status_anterior, evento.status_novo), ("RESOLVIDO", "ENCERRADO"))
        self.assertEqual(evento.usuario, self.gestor)

    def test_so_gestor_encerra_e_nao_ha_reabertura_apos_acoes_concluidas(self):
        self.resolver()
        self.concluir(self.acao())
        with self.assertRaises(PermissionDenied):
            self.encerrar(usuario=self.dev)
        self.encerrar()
        with self.assertRaises(ValidationError):
            alterar_status(
                usuario=self.gestor,
                problema_id=self.problema.pk,
                status="EM_INVESTIGACAO",
            )

    def test_novas_acoes_e_status_bloqueados_depois_do_encerramento(self):
        acao = self.acao()
        self.concluir(acao)
        self.resolver()
        self.encerrar()
        for usuario in (self.gestor, self.dev, self.admin):
            with self.subTest(usuario=usuario), self.assertRaises(ValidationError) as contexto:
                self.acao(usuario=usuario)
            self.assertEqual(contexto.exception.code, "problema_encerrado")
        for usuario in (self.dev, self.admin):
            with self.subTest(usuario=usuario), self.assertRaises(ValidationError) as contexto:
                alterar_status_acao(usuario=usuario, acao_id=acao.pk, status="EM_ANDAMENTO")
            self.assertEqual(contexto.exception.code, "problema_encerrado")
        self.assertEqual(AcaoCorretiva.objects.count(), 1)
        self.assertEqual(acao.history.count(), 3)

    def test_superusuario_encerra_mas_nao_dispensa_acoes_concluidas(self):
        self.resolver()
        with self.assertRaises(ValidationError):
            self.encerrar(usuario=self.admin)
        acao = self.acao(usuario=self.admin)
        with self.assertRaises(ValidationError):
            self.encerrar(usuario=self.admin)
        self.concluir(acao, usuario=self.admin)
        encerrado = self.encerrar(usuario=self.admin)
        self.assertEqual(encerrado.historico_status.last().usuario, self.admin)

    def test_falha_na_auditoria_reverte_criacao_e_status_da_acao(self):
        with patch.object(
            AcaoCorretiva.history.model, "save", side_effect=RuntimeError("Auditoria")
        ):
            with self.assertRaises(RuntimeError):
                self.acao()
        self.assertFalse(AcaoCorretiva.objects.exists())
        acao = self.acao()
        with patch.object(
            AcaoCorretiva.history.model, "save", side_effect=RuntimeError("Auditoria")
        ):
            with self.assertRaises(RuntimeError):
                alterar_status_acao(usuario=self.dev, acao_id=acao.pk, status="EM_ANDAMENTO")
        acao.refresh_from_db()
        self.assertEqual(acao.status, "ABERTA")
        self.assertEqual(acao.history.count(), 1)

    def test_falha_na_auditoria_reverte_documentacao_e_encerramento(self):
        causa = self.causa()
        with patch.object(CausaRaiz.history.model, "save", side_effect=RuntimeError("Auditoria")):
            with self.assertRaises(RuntimeError):
                self.causa(descricao="Não deve persistir")
        causa.refresh_from_db()
        self.assertEqual(causa.descricao, "Conexões não liberadas")
        self.resolver()
        self.concluir(self.acao())
        with patch.object(HistoricoStatus, "save", side_effect=RuntimeError("Histórico")):
            with self.assertRaises(RuntimeError):
                self.encerrar()
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, "RESOLVIDO")
        self.assertEqual(self.problema.history.first().status, "RESOLVIDO")

    def test_matriz_http_dos_quatro_perfis_login_metodos_e_get_sem_gravacao(self):
        acao = self.acao()
        rotas = (
            ("problemas:registrar_causa_raiz", [self.problema.pk], {Perfil.DESENVOLVEDOR}),
            ("kedb:registrar", [self.problema.pk], {Perfil.DESENVOLVEDOR}),
            ("acoes:cadastrar", [self.problema.pk], {Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI}),
            ("acoes:alterar_status", [acao.pk], {Perfil.DESENVOLVEDOR}),
        )
        for nome, args, permitidos in rotas:
            url = reverse(nome, args=args)
            self.client.logout()
            for metodo in ("get", "post"):
                resposta = getattr(self.client, metodo)(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("next=", resposta.url)
            for perfil, usuario in self.usuarios.items():
                self.client.force_login(usuario)
                with self.subTest(nome=nome, perfil=perfil):
                    self.assertEqual(
                        self.client.get(url).status_code,
                        200 if perfil in permitidos else 403,
                    )
                    if perfil not in permitidos:
                        self.assertEqual(self.client.post(url, {}).status_code, 403)
            self.client.force_login(self.admin)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.put(url).status_code, 405)
            inexistente = reverse(nome, args=[999999])
            self.assertEqual(self.client.get(inexistente).status_code, 404)
            self.assertEqual(self.client.post(inexistente, {}).status_code, 404)
        self.assertFalse(CausaRaiz.objects.exists())
        self.assertFalse(ErroConhecido.objects.exists())
        self.assertEqual(AcaoCorretiva.objects.count(), 1)
        self.assertEqual(acao.history.count(), 1)

    def test_csrf_exigido_e_token_valido_aceito(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.admin)
        acao = self.acao()
        for nome, pk in (
            ("problemas:registrar_causa_raiz", self.problema.pk),
            ("kedb:registrar", self.problema.pk),
            ("acoes:cadastrar", self.problema.pk),
            ("acoes:alterar_status", acao.pk),
        ):
            self.assertEqual(cliente.post(reverse(nome, args=[pk]), {}).status_code, 403)
        url = reverse("problemas:registrar_causa_raiz", args=[self.problema.pk])
        cliente.get(url)
        token = cliente.cookies["csrftoken"].value
        resposta = cliente.post(
            url,
            {
                "descricao": "Causa",
                "analise_5_porques": "Análise",
                "csrfmiddlewaretoken": token,
            },
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(CausaRaiz.objects.get().history.get().history_user, self.admin)

    def test_formularios_invalidos_e_forged_ids_sem_gravar(self):
        self.client.force_login(self.dev)
        for nome, dados in (
            ("problemas:registrar_causa_raiz", {"descricao": "Causa"}),
            ("kedb:registrar", {"sintoma": "Sintoma", "causa": "Causa"}),
            (
                "acoes:cadastrar",
                {"descricao": "Ação", "prazo": "2026-02-30", "responsavel": self.dev.pk},
            ),
            (
                "acoes:cadastrar",
                {"descricao": "Ação", "prazo": "2026-11-12", "responsavel": self.gestor.pk},
            ),
            (
                "acoes:cadastrar",
                {"descricao": "Ação", "prazo": "2026-11-12", "responsavel": 999999},
            ),
        ):
            resposta = self.client.post(reverse(nome, args=[self.problema.pk]), dados)
            self.assertEqual(resposta.status_code, 200)
            self.assertTrue(resposta.context["form"].errors)
        self.assertFalse(CausaRaiz.objects.exists())
        self.assertFalse(ErroConhecido.objects.exists())
        self.assertFalse(AcaoCorretiva.objects.exists())

    def test_http_edita_documentacao_sem_transferir_problema_ou_forjar_autor(self):
        self.causa()
        self.erro()
        self.client.force_login(self.outro_dev)
        for nome, dados, modelo in (
            (
                "problemas:registrar_causa_raiz",
                {
                    "descricao": "Revisada",
                    "analise_5_porques": "Análise revisada",
                },
                CausaRaiz,
            ),
            (
                "kedb:registrar",
                {
                    "sintoma": "Revisado",
                    "causa": "Revisada",
                    "solucao_contorno": "Revisado",
                },
                ErroConhecido,
            ),
        ):
            url = reverse(nome, args=[self.problema.pk])
            resposta = self.client.get(url)
            self.assertTrue(resposta.context["form"].initial)
            dados.update(problema=self.externo.pk, history_user=self.suporte.pk, status="ENCERRADO")
            self.assertEqual(self.client.post(url, dados).status_code, 302)
            registro = modelo.objects.get()
            self.assertEqual(registro.problema, self.problema)
            self.assertEqual(registro.history.count(), 2)
            self.assertEqual(registro.history.first().history_user, self.outro_dev)
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, "REGISTRADO")

    def test_http_status_da_acao_preserva_outros_campos_e_vinculo(self):
        self.client.force_login(self.gestor)
        resposta = self.client.post(
            reverse("acoes:cadastrar", args=[self.problema.pk]),
            {
                "descricao": "Corrigir",
                "prazo": "2026-11-12",
                "responsavel": self.dev.pk,
                "status": "CONCLUIDA",
                "problema": self.externo.pk,
                "history_user": self.dev.pk,
            },
        )
        self.assertEqual(resposta.status_code, 302)
        acao = AcaoCorretiva.objects.get()
        self.assertEqual(acao.status, "ABERTA")
        self.assertEqual(acao.problema, self.problema)
        self.assertEqual(acao.history.get().history_user, self.gestor)
        self.client.force_login(self.outro_dev)
        resposta = self.client.post(
            reverse("acoes:alterar_status", args=[acao.pk]),
            {
                "status": "EM_ANDAMENTO",
                "descricao": "Forjada",
                "prazo": "2030-01-01",
                "responsavel": self.outro_dev.pk,
                "problema": self.externo.pk,
            },
        )
        self.assertEqual(resposta.status_code, 302)
        acao.refresh_from_db()
        self.assertEqual(acao.descricao, "Corrigir")
        self.assertEqual(acao.prazo, date(2026, 11, 12))
        self.assertEqual(acao.responsavel, self.dev)
        self.assertEqual(acao.problema, self.problema)

    def test_detalhe_reune_dados_historicos_sem_vazar_outro_sistema(self):
        causa = self.causa()
        erro = self.erro()
        acao = self.acao()
        self.concluir(acao)
        self.causa(problema_id=self.externo.pk, descricao="Informação externa")
        self.erro(problema_id=self.externo.pk, sintoma="Informação externa")
        self.acao(problema_id=self.externo.pk, descricao="Informação externa")
        self.client.force_login(self.responsavel)
        resposta = self.client.get(reverse("problemas:detalhe", args=[self.problema.pk]))
        self.assertEqual(resposta.context["causa_raiz"], causa)
        self.assertEqual(resposta.context["erro_conhecido"], erro)
        self.assertEqual(list(resposta.context["acoes"]), [acao])
        for chave in ("historico_causa_raiz", "historico_erro_conhecido", "historico_acoes"):
            self.assertTrue(resposta.context[chave])
            self.assertTrue(all(r.problema_id == self.problema.pk for r in resposta.context[chave]))
        eventos = resposta.context["linha_do_tempo"]
        self.assertEqual(
            {evento["entidade"] for evento in eventos},
            {
                "Problema",
                "CausaRaiz",
                "ErroConhecido",
                "AçãoCorretiva",
            },
        )
        self.assertEqual([e["data"] for e in eventos], sorted(e["data"] for e in eventos))
        self.assertTrue(all(e["usuario"] is not None for e in eventos))
        self.assertEqual(
            self.client.get(reverse("problemas:detalhe", args=[self.externo.pk])).status_code,
            404,
        )

    def test_encerramento_revalida_acao_criada_apos_validacao_do_formulario(self):
        self.resolver()
        self.concluir(self.acao())
        self.client.force_login(self.gestor)

        def criar_antes_de_encerrar(**dados):
            self.acao()
            return alterar_status(**dados)

        with patch("problemas.views.services.alterar_status", side_effect=criar_antes_de_encerrar):
            resposta = self.client.post(
                reverse("problemas:alterar_status", args=[self.problema.pk]),
                {"status": "ENCERRADO"},
            )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, "RESOLVIDO")

    def test_acao_nao_criada_se_problema_encerrado_apos_validacao_do_formulario(self):
        self.resolver()
        self.concluir(self.acao())
        self.client.force_login(self.gestor)

        def encerrar_antes_de_criar(**dados):
            self.encerrar()
            return criar_acao(**dados)

        with patch("acoes.views.criar_acao", side_effect=encerrar_antes_de_criar):
            resposta = self.client.post(
                reverse("acoes:cadastrar", args=[self.problema.pk]),
                {
                    "descricao": "Ação tardia",
                    "prazo": "2026-11-12",
                    "responsavel": self.dev.pk,
                },
            )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertFalse(AcaoCorretiva.objects.filter(descricao="Ação tardia").exists())

    def test_fluxo_completo_http_incidente_investigacao_correcao_encerramento(self):
        self.client.force_login(self.suporte)
        resposta = self.client.post(
            reverse("incidentes:cadastrar"),
            {
                "titulo": "Fluxo MVP",
                "descricao": "Queda do serviço",
                "data_ocorrencia": "2026-11-09T10:00:00",
                "impacto": "ALTO",
                "sistema": self.sistema.pk,
            },
        )
        self.assertEqual(resposta.status_code, 302)
        incidente = Incidente.objects.get(titulo="Fluxo MVP")
        resposta = self.client.post(
            reverse("problemas:cadastrar"),
            {
                "titulo": "Problema MVP",
                "descricao": "Investigar queda",
                "incidentes": [incidente.pk],
            },
        )
        self.assertEqual(resposta.status_code, 302)
        problema = Problema.objects.get(titulo="Problema MVP")
        status_url = reverse("problemas:alterar_status", args=[problema.pk])
        self.client.force_login(self.gestor)
        self.assertEqual(
            self.client.post(
                reverse("problemas:atribuir", args=[problema.pk]),
                {
                    "responsavel": self.dev.pk,
                    "prioridade": "ALTA",
                },
            ).status_code,
            302,
        )
        self.client.force_login(self.dev)
        self.assertEqual(
            self.client.post(status_url, {"status": "EM_INVESTIGACAO"}).status_code, 302
        )
        for nome, dados in (
            (
                "problemas:registrar_causa_raiz",
                {
                    "descricao": "Falha no pool",
                    "analise_5_porques": "Análise documentada",
                },
            ),
            (
                "kedb:registrar",
                {
                    "sintoma": "Indisponibilidade",
                    "causa": "Pool esgotado",
                    "solucao_contorno": "Reiniciar temporariamente",
                },
            ),
            (
                "acoes:cadastrar",
                {
                    "descricao": "Corrigir liberação de conexões",
                    "prazo": "2026-11-12",
                    "responsavel": self.dev.pk,
                },
            ),
        ):
            self.assertEqual(
                self.client.post(reverse(nome, args=[problema.pk]), dados).status_code, 302
            )
        for status in ("ERRO_CONHECIDO", "EM_CORRECAO"):
            self.assertEqual(self.client.post(status_url, {"status": status}).status_code, 302)
        acao = problema.acoes_corretivas.get()
        for status in ("EM_ANDAMENTO", "CONCLUIDA"):
            self.assertEqual(
                self.client.post(
                    reverse("acoes:alterar_status", args=[acao.pk]),
                    {
                        "status": status,
                    },
                ).status_code,
                302,
            )
        self.assertEqual(self.client.post(status_url, {"status": "RESOLVIDO"}).status_code, 302)
        self.client.force_login(self.gestor)
        self.assertEqual(self.client.post(status_url, {"status": "ENCERRADO"}).status_code, 302)
        problema.refresh_from_db()
        self.assertEqual(problema.status, "ENCERRADO")
        self.assertEqual(problema.historico_status.count(), 6)
        self.assertEqual(problema.historico_status.last().usuario, self.gestor)
        detalhe = self.client.get(reverse("problemas:detalhe", args=[problema.pk]))
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(detalhe.context["problema"].quantidade_incidentes, 1)
        self.assertEqual(len(detalhe.context["linha_do_tempo"]), 12)

    @override_settings(ROOT_URLCONF="config.urls")
    def test_rotas_novas_disponiveis_apos_integracao_f3(self):
        self.client.force_login(self.admin)
        for url in (
            f"/problemas/{self.problema.pk}/causa-raiz/",
            f"/acoes/problema/{self.problema.pk}/nova/",
            f"/kedb/problema/{self.problema.pk}/registrar/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
