from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from contas.models import Perfil, Usuario

from .models import Sistema


class SistemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {
            perfil: Usuario.objects.create_user(
                username=perfil.lower(), perfil=perfil, first_name=perfil.label
            )
            for perfil in Perfil
        }
        cls.gestor = cls.usuarios[Perfil.GESTOR_TI]
        cls.responsavel = cls.usuarios[Perfil.RESPONSAVEL_SISTEMA]
        cls.admin = Usuario.objects.create_superuser("admin", password=None)
        cls.sistema = Sistema.objects.create(
            nome="Portal acadêmico",
            descricao="Matrículas e notas",
            responsavel=cls.responsavel,
        )

    def setUp(self):
        self.lista_url = reverse("sistemas:listar")
        self.cadastro_url = reverse("sistemas:cadastrar")
        self.edicao_url = reverse("sistemas:editar", args=[self.sistema.pk])
        self.dados = {
            "nome": "Biblioteca",
            "descricao": "Empréstimos de livros",
            "responsavel": self.responsavel.pk,
        }

    def test_anonimos_seguem_fluxo_de_login(self):
        for url in (self.lista_url, self.cadastro_url, self.edicao_url):
            for metodo in ("get", "post"):
                with self.subTest(url=url, metodo=metodo):
                    resposta = getattr(self.client, metodo)(url)
                    self.assertRedirects(resposta, f"{reverse('contas:login')}?next={url}")
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_telas_permitidas_ao_gestor_e_superusuario(self):
        for usuario in (self.gestor, self.admin):
            self.client.force_login(usuario)
            for url in (self.lista_url, self.cadastro_url, self.edicao_url):
                with self.subTest(usuario=usuario, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_outros_tres_perfis_recebem_403_sem_gravacao(self):
        for perfil in (Perfil.SUPORTE, Perfil.DESENVOLVEDOR, Perfil.RESPONSAVEL_SISTEMA):
            self.client.force_login(self.usuarios[perfil])
            for url in (self.lista_url, self.cadastro_url, self.edicao_url):
                for metodo in ("get", "post"):
                    with self.subTest(perfil=perfil, url=url, metodo=metodo):
                        resposta = getattr(self.client, metodo)(url, self.dados)
                        self.assertEqual(resposta.status_code, 403)
        self.sistema.refresh_from_db()
        self.assertEqual(self.sistema.nome, "Portal acadêmico")
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_cadastro_persiste_responsavel_e_audita_autor_autenticado(self):
        self.client.force_login(self.gestor)
        resposta = self.client.post(
            self.cadastro_url,
            {**self.dados, "history_user": self.responsavel.pk},
            follow=True,
        )
        self.assertRedirects(resposta, self.lista_url)
        self.assertContains(resposta, "Sistema cadastrado com sucesso.")
        sistema = Sistema.objects.get(nome="Biblioteca")
        self.assertEqual(sistema.descricao, "Empréstimos de livros")
        self.assertEqual(sistema.responsavel, self.responsavel)
        self.assertEqual(sistema.history.count(), 1)
        registro = sistema.history.get()
        self.assertEqual(registro.history_type, "+")
        self.assertEqual(registro.history_user, self.gestor)
        self.assertEqual(registro.responsavel_id, self.responsavel.pk)
        self.assertIsNotNone(registro.history_date)

    def test_edicao_preserva_identidade_e_historico_dos_valores_e_autores(self):
        self.client.force_login(self.gestor)
        self.client.post(self.cadastro_url, self.dados)
        sistema = Sistema.objects.get(nome="Biblioteca")
        outro_gestor = Usuario.objects.create_user("outro_gestor", perfil=Perfil.GESTOR_TI)
        outro_responsavel = Usuario.objects.create_user(
            "outro_responsavel", perfil=Perfil.RESPONSAVEL_SISTEMA
        )
        self.client.force_login(outro_gestor)
        resposta = self.client.post(
            reverse("sistemas:editar", args=[sistema.pk]),
            {
                "nome": "Biblioteca atualizada",
                "descricao": "Catálogo e empréstimos",
                "responsavel": outro_responsavel.pk,
            },
            follow=True,
        )
        self.assertRedirects(resposta, self.lista_url)
        self.assertContains(resposta, "Sistema atualizado com sucesso.")
        sistema.refresh_from_db()
        self.assertEqual(sistema.nome, "Biblioteca atualizada")
        self.assertEqual(sistema.descricao, "Catálogo e empréstimos")
        self.assertEqual(sistema.responsavel, outro_responsavel)
        self.assertEqual(Sistema.objects.count(), 2)
        anterior, atual = sistema.history.order_by("history_id")
        self.assertEqual(anterior.nome, "Biblioteca")
        self.assertEqual(anterior.responsavel_id, self.responsavel.pk)
        self.assertEqual(anterior.history_user, self.gestor)
        self.assertEqual(atual.nome, sistema.nome)
        self.assertEqual(atual.responsavel_id, outro_responsavel.pk)
        self.assertEqual(atual.history_user, outro_gestor)
        self.assertEqual(atual.history_type, "~")

    def test_superusuario_com_perfil_suporte_pode_cadastrar_e_editar(self):
        self.assertEqual(self.admin.perfil, Perfil.SUPORTE)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.post(self.cadastro_url, self.dados), self.lista_url)
        sistema = Sistema.objects.get(nome="Biblioteca")
        self.assertRedirects(
            self.client.post(
                reverse("sistemas:editar", args=[sistema.pk]),
                {**self.dados, "nome": "Biblioteca central"},
            ),
            self.lista_url,
        )
        sistema.refresh_from_db()
        self.assertEqual(sistema.nome, "Biblioteca central")
        self.assertEqual(sistema.history.count(), 2)
        self.assertTrue(all(item.history_user == self.admin for item in sistema.history.all()))

    def test_listagem_exibe_sistema_responsavel_e_links(self):
        self.client.force_login(self.gestor)
        resposta = self.client.get(self.lista_url)
        for texto in ("Portal acadêmico", "Matrículas e notas", str(self.responsavel)):
            self.assertContains(resposta, texto)
        self.assertContains(resposta, self.cadastro_url)
        self.assertContains(resposta, self.edicao_url)

    def test_listagem_vazia_orienta_usuario(self):
        Sistema.objects.all().delete()
        self.client.force_login(self.gestor)
        self.assertContains(self.client.get(self.lista_url), "Nenhum sistema cadastrado.")

    def test_campos_obrigatorios_validados_no_servidor(self):
        self.client.force_login(self.gestor)
        for url in (self.cadastro_url, self.edicao_url):
            for campo in self.dados:
                with self.subTest(url=url, campo=campo):
                    resposta = self.client.post(url, {**self.dados, campo: ""})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertIn(campo, resposta.context["form"].errors)
                    self.assertContains(resposta, "Este campo é obrigatório.")
                    self.assertContains(resposta, "Não foi possível salvar.")
        self.sistema.refresh_from_db()
        self.assertEqual(self.sistema.nome, "Portal acadêmico")
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_post_vazio_e_textos_em_branco_nao_gravam(self):
        self.client.force_login(self.gestor)
        for dados in ({}, {**self.dados, "nome": "   ", "descricao": "\n  "}):
            with self.subTest(dados=dados):
                resposta = self.client.post(self.cadastro_url, dados)
                self.assertTrue(resposta.context["form"].errors)
        self.assertEqual(Sistema.objects.count(), 1)

    def test_nome_longo_e_responsavel_inexistente_sao_rejeitados(self):
        self.client.force_login(self.gestor)
        for campo, valor in (("nome", "x" * 201), ("responsavel", 999999)):
            for url in (self.cadastro_url, self.edicao_url):
                with self.subTest(campo=campo, url=url):
                    resposta = self.client.post(url, {**self.dados, campo: valor})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertIn(campo, resposta.context["form"].errors)
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_formularios_listam_apenas_responsaveis_pelo_sistema(self):
        self.client.force_login(self.gestor)
        for url in (self.cadastro_url, self.edicao_url):
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertQuerySetEqual(
                    resposta.context["form"].fields["responsavel"].queryset,
                    [self.responsavel],
                )

    def test_post_adulterado_rejeita_responsavel_de_outro_perfil(self):
        for autor in (self.gestor, self.admin):
            self.client.force_login(autor)
            for perfil in (Perfil.SUPORTE, Perfil.DESENVOLVEDOR, Perfil.GESTOR_TI):
                for url in (self.cadastro_url, self.edicao_url):
                    with self.subTest(autor=autor, perfil=perfil, url=url):
                        resposta = self.client.post(
                            url, {**self.dados, "responsavel": self.usuarios[perfil].pk}
                        )
                        self.assertEqual(resposta.status_code, 200)
                        self.assertFormError(
                            resposta.context["form"],
                            "responsavel",
                            "Selecione um usuário com o perfil Responsável pelo sistema.",
                        )
        self.sistema.refresh_from_db()
        self.assertEqual(self.sistema.responsavel, self.responsavel)
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_validacao_do_modelo_exige_perfil_do_responsavel(self):
        for perfil, usuario in self.usuarios.items():
            with self.subTest(perfil=perfil):
                sistema = Sistema(nome="Teste", descricao="Teste", responsavel=usuario)
                if perfil == Perfil.RESPONSAVEL_SISTEMA:
                    sistema.full_clean()
                else:
                    with self.assertRaises(ValidationError) as erro:
                        sistema.full_clean()
                    self.assertIn("responsavel", erro.exception.message_dict)

    def test_edicao_exige_novo_responsavel_se_perfil_atual_mudar(self):
        self.responsavel.perfil = Perfil.SUPORTE
        self.responsavel.save()
        self.client.force_login(self.gestor)
        resposta = self.client.post(self.edicao_url, self.dados)
        self.assertIn("responsavel", resposta.context["form"].errors)
        self.assertEqual(self.sistema.history.count(), 1)
        novo_responsavel = Usuario.objects.create_user(
            "novo_responsavel", perfil=Perfil.RESPONSAVEL_SISTEMA
        )
        resposta = self.client.post(
            self.edicao_url, {**self.dados, "responsavel": novo_responsavel.pk}
        )
        self.assertRedirects(resposta, self.lista_url)
        self.sistema.refresh_from_db()
        self.assertEqual(self.sistema.responsavel, novo_responsavel)

    def test_get_de_formularios_nao_grava_e_edicao_carrega_valores(self):
        self.client.force_login(self.gestor)
        self.client.get(self.cadastro_url, self.dados)
        resposta = self.client.get(self.edicao_url, self.dados)
        self.assertContains(resposta, "Portal acadêmico")
        self.assertContains(resposta, "Matrículas e notas")
        self.assertEqual(resposta.context["form"]["responsavel"].value(), self.responsavel.pk)
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_sistema_inexistente_retorna_404(self):
        self.client.force_login(self.gestor)
        url = reverse("sistemas:editar", args=[999999])
        for metodo in ("get", "post"):
            with self.subTest(metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(url, self.dados).status_code, 404)

    def test_metodos_nao_previstos_nao_gravam(self):
        self.client.force_login(self.gestor)
        self.assertEqual(self.client.post(self.lista_url, self.dados).status_code, 405)
        for url in (self.cadastro_url, self.edicao_url):
            for metodo in ("put", "patch", "delete"):
                with self.subTest(url=url, metodo=metodo):
                    self.assertEqual(getattr(self.client, metodo)(url).status_code, 405)
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_csrf_exigido_no_cadastro_e_edicao(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.gestor)
        for url in (self.cadastro_url, self.edicao_url):
            with self.subTest(url=url):
                self.assertEqual(cliente.post(url, self.dados).status_code, 403)
                pagina = cliente.get(url)
                self.assertContains(pagina, 'name="csrfmiddlewaretoken"')
                token = cliente.cookies["csrftoken"].value
                resposta = cliente.post(url, {**self.dados, "csrfmiddlewaretoken": token})
                self.assertEqual(resposta.status_code, 302)

    def test_listagem_escapa_html_informado_pelo_usuario(self):
        self.client.force_login(self.gestor)
        self.client.post(
            self.cadastro_url, {**self.dados, "descricao": "<script>alert(1)</script>"}
        )
        resposta = self.client.get(self.lista_url)
        self.assertNotContains(resposta, "<script>alert(1)</script>")
        self.assertContains(resposta, "&lt;script&gt;alert(1)&lt;/script&gt;")


class SistemaAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser("admin", password=None)
        cls.responsavel = Usuario.objects.create_user(
            "responsavel", perfil=Perfil.RESPONSAVEL_SISTEMA
        )
        cls.sistema = Sistema.objects.create(
            nome="Portal", descricao="Serviços acadêmicos", responsavel=cls.responsavel
        )

    def test_admin_cadastra_edita_e_exibe_historico_com_autor(self):
        self.client.force_login(self.admin)
        dados = {"nome": "Biblioteca", "descricao": "Livros", "responsavel": self.responsavel.pk}
        resposta = self.client.post(reverse("admin:sistemas_sistema_add"), dados)
        self.assertEqual(resposta.status_code, 302)
        sistema = Sistema.objects.get(nome="Biblioteca")
        resposta = self.client.post(
            reverse("admin:sistemas_sistema_change", args=[sistema.pk]),
            {**dados, "nome": "Biblioteca central"},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(sistema.history.count(), 2)
        self.assertTrue(all(item.history_user == self.admin for item in sistema.history.all()))
        resposta = self.client.get(reverse("admin:sistemas_sistema_history", args=[sistema.pk]))
        self.assertContains(resposta, "Biblioteca central")

    def test_admin_exige_perfil_mesmo_com_permissoes_django(self):
        permissoes = Permission.objects.filter(
            content_type__app_label="sistemas", content_type__model="sistema"
        )
        for perfil in Perfil:
            usuario = Usuario.objects.create_user(username=perfil, perfil=perfil, is_staff=True)
            usuario.user_permissions.set(permissoes)
            self.client.force_login(usuario)
            for nome, args in (
                ("changelist", []),
                ("add", []),
                ("change", [self.sistema.pk]),
                ("history", [self.sistema.pk]),
            ):
                with self.subTest(perfil=perfil, tela=nome):
                    resposta = self.client.get(reverse(f"admin:sistemas_sistema_{nome}", args=args))
                    esperado = 200 if perfil == Perfil.GESTOR_TI else 403
                    self.assertEqual(resposta.status_code, esperado)
            resposta = self.client.post(
                reverse("admin:sistemas_sistema_change", args=[self.sistema.pk]),
                {"nome": "Atualizado", "descricao": "Teste", "responsavel": self.responsavel.pk},
            )
            self.assertEqual(resposta.status_code, 302 if perfil == Perfil.GESTOR_TI else 403)

    def test_admin_filtra_e_valida_perfil_do_responsavel(self):
        self.client.force_login(self.admin)
        for url in (
            reverse("admin:sistemas_sistema_add"),
            reverse("admin:sistemas_sistema_change", args=[self.sistema.pk]),
        ):
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertQuerySetEqual(
                    resposta.context["adminform"].form.fields["responsavel"].queryset,
                    [self.responsavel],
                )
                resposta = self.client.post(
                    url,
                    {"nome": "Inválido", "descricao": "Teste", "responsavel": self.admin.pk},
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("responsavel", resposta.context["adminform"].form.errors)
        self.sistema.refresh_from_db()
        self.assertEqual(self.sistema.responsavel, self.responsavel)
        self.assertEqual(Sistema.objects.count(), 1)
        self.assertEqual(self.sistema.history.count(), 1)

    def test_admin_nao_oferece_exclusao(self):
        self.client.force_login(self.admin)
        url = reverse("admin:sistemas_sistema_delete", args=[self.sistema.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        self.client.post(
            reverse("admin:sistemas_sistema_changelist"),
            {"action": "delete_selected", "_selected_action": [self.sistema.pk], "post": "yes"},
        )
        self.assertTrue(Sistema.objects.filter(pk=self.sistema.pk).exists())
