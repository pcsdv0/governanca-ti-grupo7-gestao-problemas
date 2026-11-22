from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Perfil, Usuario
from incidentes.forms import IncidenteForm
from incidentes.models import Incidente
from sistemas.models import Sistema

from .constantes import PrioridadeProblema, StatusProblema
from .models import HistoricoStatus, Problema
from .services import (
    abrir_problema,
    alterar_status,
    atribuir_responsavel_prioridade,
    problemas_visiveis,
    vincular_incidentes,
)


class ProblemaBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            perfil: Usuario.objects.create_user(username=perfil, perfil=perfil) for perfil in Perfil
        }
        cls.suporte = cls.usuarios[Perfil.SUPORTE]
        cls.dev = cls.usuarios[Perfil.DESENVOLVEDOR]
        cls.gestor = cls.usuarios[Perfil.GESTOR_TI]
        cls.responsavel = cls.usuarios[Perfil.RESPONSAVEL_SISTEMA]
        cls.admin = Usuario.objects.create_superuser("admin", password=None)
        cls.outro_responsavel = Usuario.objects.create_user(
            "outro",
            perfil=Perfil.RESPONSAVEL_SISTEMA,
        )
        cls.sistema = Sistema.objects.create(
            nome="Matrícula",
            descricao="Matrículas",
            responsavel=cls.responsavel,
        )
        cls.outro_sistema = Sistema.objects.create(
            nome="Biblioteca",
            descricao="Livros",
            responsavel=cls.outro_responsavel,
        )
        cls.incidentes = [
            Incidente.objects.create(
                titulo=f"Queda {numero}",
                descricao="Interrupção",
                data_ocorrencia=timezone.now(),
                impacto="ALTO",
                sistema=cls.sistema,
                registrado_por=cls.suporte,
            )
            for numero in range(3)
        ]
        cls.externo = Incidente.objects.create(
            titulo="Falha externa",
            descricao="Outro sistema",
            data_ocorrencia=timezone.now(),
            impacto="BAIXO",
            sistema=cls.outro_sistema,
            registrado_por=cls.suporte,
        )
        cls.problema = abrir_problema(
            usuario=cls.suporte,
            titulo="Quedas repetidas",
            descricao="Investigar conexões",
            incidentes_ids=[cls.incidentes[0].pk],
        )

    def abrir(self, **kwargs):
        dados = {
            "usuario": self.suporte,
            "titulo": "Outra falha",
            "descricao": "Investigar",
            "incidentes_ids": [self.incidentes[1].pk, self.incidentes[2].pk],
        }
        return abrir_problema(**(dados | kwargs))

    def avancar_ate_resolvido(self):
        for status in (
            StatusProblema.EM_INVESTIGACAO,
            StatusProblema.ERRO_CONHECIDO,
            StatusProblema.EM_CORRECAO,
            StatusProblema.RESOLVIDO,
        ):
            alterar_status(usuario=self.dev, problema_id=self.problema.pk, status=status)

    def test_prioridades_documentadas(self):
        self.assertEqual(
            PrioridadeProblema.choices,
            [("BAIXA", "Baixa"), ("MEDIA", "Média"), ("ALTA", "Alta")],
        )

    def test_abertura_deriva_sistema_e_preserva_autoria_incidentes(self):
        problema = self.abrir()
        self.assertEqual(problema.sistema, self.sistema)
        self.assertEqual(problema.status, StatusProblema.REGISTRADO)
        self.assertEqual(problema.prioridade, "")
        self.assertIsNone(problema.responsavel)
        self.assertEqual(problema.incidentes.count(), 2)
        for incidente in problema.incidentes.all():
            self.assertEqual(incidente.registrado_por, self.suporte)
            self.assertEqual(incidente.history.first().history_user, self.suporte)
        self.assertEqual(problema.history.get().history_user, self.suporte)
        evento = problema.historico_status.get()
        self.assertEqual((evento.status_anterior, evento.status_novo), ("", "REGISTRADO"))
        self.assertEqual(evento.usuario, self.suporte)
        self.assertEqual(evento.history.get().history_user, self.suporte)

    def test_abertura_exige_incidentes_existentes_livres_do_mesmo_sistema(self):
        for ids in (
            [],
            [999999],
            ["abc"],
            [self.externo.pk, self.incidentes[1].pk],
            [self.incidentes[0].pk, self.incidentes[1].pk],
        ):
            with self.subTest(ids=ids), self.assertRaises(ValidationError):
                self.abrir(incidentes_ids=ids)
        self.assertEqual(Problema.objects.count(), 1)
        self.incidentes[1].refresh_from_db()
        self.assertIsNone(self.incidentes[1].problema_id)

    def test_titulo_descricao_obrigatorios_sem_gravacao_parcial(self):
        for campos in ({"titulo": "  "}, {"descricao": ""}, {"titulo": "x" * 201}):
            with self.subTest(campos=campos), self.assertRaises(ValidationError):
                self.abrir(**campos)
        self.assertEqual(Problema.objects.count(), 1)
        self.assertEqual(HistoricoStatus.objects.count(), 1)

    def test_falha_no_vinculo_reverte_problema_historicos_e_demais_vinculos(self):
        salvar = Incidente.save

        def falhar_no_segundo(incidente, *args, **kwargs):
            if incidente.pk == self.incidentes[2].pk:
                raise RuntimeError("Falha simulada de persistência")
            return salvar(incidente, *args, **kwargs)

        with patch.object(Incidente, "save", falhar_no_segundo), self.assertRaises(RuntimeError):
            self.abrir()
        self.assertEqual(Problema.objects.count(), 1)
        self.assertEqual(Problema.history.count(), 1)
        self.assertEqual(HistoricoStatus.objects.count(), 1)
        for incidente in self.incidentes[1:]:
            incidente.refresh_from_db()
            self.assertIsNone(incidente.problema_id)
            self.assertEqual(incidente.history.count(), 1)

    def test_servicos_exigem_perfil_mesmo_fora_de_requisicao(self):
        for usuario in (AnonymousUser(), self.dev, self.gestor, self.responsavel):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                self.abrir(usuario=usuario)
        self.suporte.is_active = False
        with self.assertRaises(PermissionDenied):
            self.abrir()
        self.assertEqual(Problema.objects.count(), 1)

    def test_vinculo_idempotente_e_sem_transferencia(self):
        vincular_incidentes(
            usuario=self.suporte,
            problema_id=self.problema.pk,
            incidentes_ids=[self.incidentes[0].pk, self.incidentes[1].pk],
        )
        quantidade = self.incidentes[1].history.count()
        vincular_incidentes(
            usuario=self.suporte,
            problema_id=self.problema.pk,
            incidentes_ids=[self.incidentes[1].pk, self.incidentes[1].pk],
        )
        self.assertEqual(self.incidentes[1].history.count(), quantidade)
        self.assertEqual(self.problema.incidentes.count(), 2)
        outro = self.abrir(incidentes_ids=[self.incidentes[2].pk])
        with self.assertRaises(ValidationError):
            vincular_incidentes(
                usuario=self.suporte,
                problema_id=outro.pk,
                incidentes_ids=[self.incidentes[1].pk],
            )
        with self.assertRaises(ValidationError):
            vincular_incidentes(
                usuario=self.suporte,
                problema_id=self.problema.pk,
                incidentes_ids=[self.externo.pk],
            )

    def test_atribuicao_exige_gestor_desenvolvedor_e_prioridade_valida(self):
        for usuario in (self.suporte, self.dev, self.responsavel):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                atribuir_responsavel_prioridade(
                    usuario=usuario,
                    problema_id=self.problema.pk,
                    responsavel_id=self.dev.pk,
                    prioridade="ALTA",
                )
        for responsavel, prioridade in (
            (self.suporte.pk, "ALTA"),
            (999999, "ALTA"),
            (self.dev.pk, ""),
            (self.dev.pk, "URGENTE"),
        ):
            with self.subTest(prioridade=prioridade), self.assertRaises(ValidationError):
                atribuir_responsavel_prioridade(
                    usuario=self.gestor,
                    problema_id=self.problema.pk,
                    responsavel_id=responsavel,
                    prioridade=prioridade,
                )
        self.problema.refresh_from_db()
        self.assertIsNone(self.problema.responsavel)
        atribuir_responsavel_prioridade(
            usuario=self.gestor,
            problema_id=self.problema.pk,
            responsavel_id=self.dev.pk,
            prioridade="ALTA",
        )
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.responsavel, self.dev)
        self.assertEqual(self.problema.prioridade, "ALTA")
        self.assertEqual(self.problema.history.first().history_user, self.gestor)
        self.assertEqual(self.problema.historico_status.count(), 1)

    def test_transicoes_sequenciais_auditadas_e_encerramento_sem_acoes_bloqueado(self):
        self.avancar_ate_resolvido()
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, StatusProblema.RESOLVIDO)
        eventos = list(self.problema.historico_status.all())
        self.assertEqual(len(eventos), 5)
        self.assertEqual(eventos[-1].status_anterior, StatusProblema.EM_CORRECAO)
        self.assertEqual(eventos[-1].usuario, self.dev)
        with self.assertRaises(PermissionDenied):
            alterar_status(
                usuario=self.dev,
                problema_id=self.problema.pk,
                status=StatusProblema.ENCERRADO,
            )
        for usuario in (self.gestor, self.admin):
            with (
                self.subTest(usuario=usuario),
                self.assertRaisesMessage(
                    ValidationError,
                    "ao menos uma AçãoCorretiva",
                ),
            ):
                alterar_status(
                    usuario=usuario,
                    problema_id=self.problema.pk,
                    status=StatusProblema.ENCERRADO,
                )
        self.assertEqual(self.problema.history.count(), 5)

    def test_rejeita_salto_repeticao_e_reabertura(self):
        for status in ("INVALIDO", "RESOLVIDO", "REGISTRADO", "ENCERRADO"):
            with self.subTest(status=status), self.assertRaises(ValidationError):
                alterar_status(usuario=self.gestor, problema_id=self.problema.pk, status=status)
        self.avancar_ate_resolvido()
        with self.assertRaises(ValidationError):
            alterar_status(
                usuario=self.gestor,
                problema_id=self.problema.pk,
                status="EM_INVESTIGACAO",
            )
        self.assertEqual(self.problema.historico_status.count(), 5)

    def test_status_nao_disponivel_para_suporte_ou_responsavel(self):
        for usuario in (self.suporte, self.responsavel):
            with self.subTest(usuario=usuario), self.assertRaises(PermissionDenied):
                alterar_status(
                    usuario=usuario,
                    problema_id=self.problema.pk,
                    status="EM_INVESTIGACAO",
                )

    def test_auditoria_orm_tambem_registra_transicao_com_autor(self):
        self.problema._history_user = self.gestor
        self.problema.status = StatusProblema.EM_INVESTIGACAO
        self.problema.save()
        evento = self.problema.historico_status.last()
        self.assertEqual(evento.usuario, self.gestor)
        self.assertEqual(evento.status_anterior, StatusProblema.REGISTRADO)
        self.assertEqual(self.problema.historico_status.count(), 2)

    def test_referencias_protegidas_e_vinculo_opcional(self):
        self.incidentes[1].refresh_from_db()
        self.assertIsNone(self.incidentes[1].problema)
        with self.assertRaises(ProtectedError):
            self.problema.delete()
        with self.assertRaises(ProtectedError):
            self.sistema.delete()

    def test_consulta_contagem_e_escopo_do_responsavel(self):
        externo = self.abrir(incidentes_ids=[self.externo.pk])
        self.assertEqual(problemas_visiveis(self.responsavel).get().pk, self.problema.pk)
        self.assertEqual(problemas_visiveis(self.responsavel).get().quantidade_incidentes, 1)
        for usuario in (self.suporte, self.dev, self.gestor, self.admin):
            self.assertEqual(problemas_visiveis(usuario).count(), 2)
        self.client.force_login(self.responsavel)
        resposta = self.client.get(reverse("problemas:listar"))
        self.assertQuerySetEqual(resposta.context["problemas"], [self.problema])
        self.assertEqual(
            self.client.get(reverse("problemas:detalhe", args=[externo.pk])).status_code,
            404,
        )
        detalhe = self.client.get(reverse("problemas:detalhe", args=[self.problema.pk]))
        self.assertEqual(detalhe.context["historico_status"].get().usuario, self.suporte)
        self.assertEqual(detalhe.context["historico"].get().history_user, self.suporte)

    def test_views_anonimo_login_e_matriz_dos_quatro_perfis(self):
        operacoes = {
            "listar": ([], set(Perfil.values)),
            "detalhe": ([self.problema.pk], set(Perfil.values)),
            "cadastrar": ([], {Perfil.SUPORTE}),
            "vincular": ([self.problema.pk], {Perfil.SUPORTE}),
            "atribuir": ([self.problema.pk], {Perfil.GESTOR_TI}),
            "alterar_status": ([self.problema.pk], {Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI}),
        }
        for nome, (args, permitidos) in operacoes.items():
            url = reverse(f"problemas:{nome}", args=args)
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
                        self.assertEqual(self.client.post(url).status_code, 403)
            self.client.force_login(self.admin)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_abertura_http_ignora_campos_forjados_e_audita_autor(self):
        self.client.force_login(self.suporte)
        resposta = self.client.post(
            reverse("problemas:cadastrar"),
            {
                "titulo": "Queda investigada",
                "descricao": "Falha",
                "incidentes": [self.incidentes[1].pk],
                "status": "ENCERRADO",
                "prioridade": "ALTA",
                "responsavel": self.dev.pk,
                "sistema": self.outro_sistema.pk,
                "history_user": self.gestor.pk,
            },
        )
        criado = Problema.objects.get(titulo="Queda investigada")
        self.assertRedirects(resposta, reverse("problemas:detalhe", args=[criado.pk]))
        self.assertEqual(criado.status, "REGISTRADO")
        self.assertEqual(criado.prioridade, "")
        self.assertIsNone(criado.responsavel_id)
        self.assertEqual(criado.sistema, self.sistema)
        self.assertEqual(criado.history.get().history_user, self.suporte)

    def test_formularios_invalidos_mostram_erros_sem_gravar(self):
        self.client.force_login(self.suporte)
        for dados in (
            {},
            {"titulo": "Teste", "descricao": "Descrição", "incidentes": [999999]},
            {
                "titulo": "Teste",
                "descricao": "Descrição",
                "incidentes": [self.incidentes[1].pk, self.externo.pk],
            },
        ):
            resposta = self.client.post(reverse("problemas:cadastrar"), dados)
            self.assertEqual(resposta.status_code, 200)
            self.assertTrue(resposta.context["form"].errors)
        self.assertEqual(Problema.objects.count(), 1)
        resposta = self.client.post(
            reverse("problemas:vincular", args=[self.problema.pk]),
            {"incidentes": [self.externo.pk]},
        )
        self.assertTrue(resposta.context["form"].errors)

    def test_fluxo_http_vinculo_atribuicao_status_e_historico(self):
        self.client.force_login(self.suporte)
        self.assertEqual(
            self.client.post(
                reverse("problemas:vincular", args=[self.problema.pk]),
                {"incidentes": [self.incidentes[1].pk]},
            ).status_code,
            302,
        )
        self.client.force_login(self.gestor)
        self.assertEqual(
            self.client.post(
                reverse("problemas:atribuir", args=[self.problema.pk]),
                {"responsavel": self.dev.pk, "prioridade": "MEDIA"},
            ).status_code,
            302,
        )
        self.client.force_login(self.dev)
        self.assertEqual(
            self.client.post(
                reverse("problemas:alterar_status", args=[self.problema.pk]),
                {"status": "EM_INVESTIGACAO"},
            ).status_code,
            302,
        )
        self.problema.refresh_from_db()
        self.assertEqual(self.problema.status, "EM_INVESTIGACAO")
        self.assertEqual(self.problema.prioridade, "MEDIA")
        self.assertEqual(self.problema.historico_status.last().usuario, self.dev)

    def test_get_nao_grava_metodos_e_404(self):
        self.client.force_login(self.admin)
        for nome in ("detalhe", "vincular", "atribuir", "alterar_status"):
            url = reverse(f"problemas:{nome}", args=[self.problema.pk])
            self.client.get(url)
            self.assertEqual(self.client.put(url).status_code, 405)
            inexistente = reverse(f"problemas:{nome}", args=[999999])
            self.assertEqual(self.client.get(inexistente).status_code, 404)
            if nome != "detalhe":
                self.assertEqual(self.client.post(inexistente, {}).status_code, 404)
        self.assertEqual(self.client.post(reverse("problemas:listar")).status_code, 405)
        self.assertEqual(self.problema.history.count(), 1)
        self.assertEqual(self.problema.historico_status.count(), 1)

    def test_csrf_exigido_em_todas_as_escritas(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.admin)
        for nome, args in (
            ("cadastrar", []),
            ("vincular", [self.problema.pk]),
            ("atribuir", [self.problema.pk]),
            ("alterar_status", [self.problema.pk]),
        ):
            url = reverse(f"problemas:{nome}", args=args)
            self.assertEqual(cliente.post(url, {}).status_code, 403)
        self.assertEqual(Problema.objects.count(), 1)

    def test_superusuario_opera_mas_nao_ignora_regras_de_negocio(self):
        criado = self.abrir(usuario=self.admin)
        self.assertEqual(criado.history.get().history_user, self.admin)
        with self.assertRaises(ValidationError):
            atribuir_responsavel_prioridade(
                usuario=self.admin,
                problema_id=criado.pk,
                responsavel_id=self.gestor.pk,
                prioridade="ALTA",
            )
        atribuir_responsavel_prioridade(
            usuario=self.admin,
            problema_id=criado.pk,
            responsavel_id=self.dev.pk,
            prioridade="BAIXA",
        )
        alterar_status(usuario=self.admin, problema_id=criado.pk, status="EM_INVESTIGACAO")
        self.assertEqual(criado.historico_status.last().usuario, self.admin)

    def test_edicao_incidente_nao_troca_sistema_quando_vinculado(self):
        incidente = self.incidentes[0]
        self.client.force_login(self.suporte)
        dados = {
            "titulo": incidente.titulo,
            "descricao": incidente.descricao,
            "data_ocorrencia": "2026-11-09T10:30:00",
            "impacto": "MEDIO",
            "sistema": self.outro_sistema.pk,
        }
        resposta = self.client.post(reverse("incidentes:editar", args=[incidente.pk]), dados)
        self.assertTrue(resposta.context["form"].has_error("sistema"))
        incidente.refresh_from_db()
        self.assertEqual(incidente.sistema, self.sistema)
        self.assertEqual(incidente.problema_id, self.problema.pk)
        self.assertNotIn("problema", IncidenteForm().fields)
        dados.update(sistema=self.sistema.pk, problema="", registrado_por=self.dev.pk)
        self.assertEqual(
            self.client.post(reverse("incidentes:editar", args=[incidente.pk]), dados).status_code,
            302,
        )
        incidente.refresh_from_db()
        self.assertEqual(incidente.problema_id, self.problema.pk)
        self.assertEqual(incidente.registrado_por, self.suporte)

    def test_filtro_por_vinculo_combinado_com_sistema_e_escopo(self):
        self.client.force_login(self.suporte)
        resposta = self.client.get(reverse("incidentes:listar"), {"vinculo_problema": "com"})
        self.assertQuerySetEqual(resposta.context["incidentes"], [self.incidentes[0]])
        resposta = self.client.get(
            reverse("incidentes:listar"),
            {
                "vinculo_problema": "sem",
                "sistema": self.sistema.pk,
            },
        )
        self.assertEqual(set(resposta.context["incidentes"]), set(self.incidentes[1:]))
        self.client.force_login(self.responsavel)
        resposta = self.client.get(reverse("incidentes:listar"), {"vinculo_problema": "sem"})
        self.assertNotIn(self.externo, resposta.context["incidentes"])
        resposta = self.client.get(reverse("incidentes:listar"), {"vinculo_problema": "inválido"})
        self.assertTrue(resposta.context["form"].errors)
        self.assertFalse(resposta.context["incidentes"].exists())

    def test_rotas_de_problemas_integradas(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/problemas/").status_code, 200)
        self.assertEqual(self.client.get("/problemas/novo/").status_code, 200)

    def test_abertura_revalida_toda_selecao_se_outro_usuario_vincular_antes(self):
        self.client.force_login(self.suporte)

        def reservar_e_abrir(**dados):
            self.abrir(incidentes_ids=[self.incidentes[1].pk])
            return abrir_problema(**dados)

        with patch("problemas.views.services.abrir_problema", side_effect=reservar_e_abrir):
            resposta = self.client.post(
                reverse("problemas:cadastrar"),
                {
                    "titulo": "Seleção concorrente",
                    "descricao": "Investigar",
                    "incidentes": [self.incidentes[1].pk, self.incidentes[2].pk],
                },
            )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertFalse(Problema.objects.filter(titulo="Seleção concorrente").exists())
        self.incidentes[2].refresh_from_db()
        self.assertIsNone(self.incidentes[2].problema_id)

    def test_vinculo_revalida_toda_selecao_se_outro_usuario_vincular_antes(self):
        self.client.force_login(self.suporte)

        def reservar_e_vincular(**dados):
            self.abrir(incidentes_ids=[self.incidentes[1].pk])
            return vincular_incidentes(**dados)

        with patch("problemas.views.services.vincular_incidentes", side_effect=reservar_e_vincular):
            resposta = self.client.post(
                reverse("problemas:vincular", args=[self.problema.pk]),
                {"incidentes": [self.incidentes[1].pk, self.incidentes[2].pk]},
            )
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["form"].errors)
        self.assertEqual(self.problema.incidentes.count(), 1)
        self.incidentes[2].refresh_from_db()
        self.assertIsNone(self.incidentes[2].problema_id)
