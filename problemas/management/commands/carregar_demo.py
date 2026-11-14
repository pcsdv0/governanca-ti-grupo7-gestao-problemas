"""Carrega dados de demonstração realistas (F6), com incidentes recorrentes.

Uso:
    python manage.py carregar_demo           # só carrega se ainda não houver Incidentes
    python manage.py carregar_demo --senha X  # define a senha dos usuários de demonstração

Todas as gravações de negócio passam pelos serviços (problemas, acoes, kedb), de modo que
as regras de transição, as permissões por perfil e a auditoria (django-simple-history e
HistóricoStatus) são as mesmas do uso real. As datas são retroativas para a linha do tempo
ficar coerente com as datas de ocorrência dos Incidentes.
"""

from contextlib import contextmanager
from datetime import timedelta
from unittest import mock

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from acoes.services import alterar_status_acao, criar_acao
from contas.models import Perfil, Usuario
from incidentes.models import Incidente
from kedb.services import registrar_erro_conhecido
from problemas.constantes import StatusProblema
from problemas.services import (
    abrir_problema,
    alterar_status,
    atribuir_responsavel_prioridade,
    registrar_causa_raiz,
    vincular_incidentes,
)
from sistemas.models import Sistema

SENHA_PADRAO = "demo1234"


class Command(BaseCommand):
    help = "Carrega usuários, sistemas, incidentes e problemas de demonstração."

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha", default=SENHA_PADRAO, help="Senha dos usuários de demonstração."
        )

    @transaction.atomic
    def handle(self, *args, **opcoes):
        if Incidente.objects.exists():
            self.stdout.write("O banco já tem Incidentes; nada foi carregado.")
            return
        agora = timezone.now()

        @contextmanager
        def em(dias_atras):
            """Executa as gravações como se fosse `dias_atras` dias atrás."""
            momento = agora - timedelta(days=dias_atras)
            with mock.patch("django.utils.timezone.now", return_value=momento):
                yield momento

        def usuario(login, nome, sobrenome, perfil):
            u, _ = Usuario.objects.get_or_create(
                username=login,
                defaults={
                    "first_name": nome,
                    "last_name": sobrenome,
                    "perfil": perfil,
                    "email": f"{login}@exemplo.com.br",
                },
            )
            u.set_password(opcoes["senha"])
            u.save()
            return u

        ana = usuario("suporte", "Ana", "Lima", Perfil.SUPORTE)
        joao = usuario("suporte2", "João", "Ferreira", Perfil.SUPORTE)
        carla = usuario("dev", "Carla", "Mendes", Perfil.DESENVOLVEDOR)
        rafael = usuario("dev2", "Rafael", "Souza", Perfil.DESENVOLVEDOR)
        marcos = usuario("gestor", "Marcos", "Oliveira", Perfil.GESTOR_TI)
        patricia = usuario("responsavel", "Patrícia", "Rocha", Perfil.RESPONSAVEL_SISTEMA)
        bruno = usuario("responsavel2", "Bruno", "Almeida", Perfil.RESPONSAVEL_SISTEMA)

        def sistema(nome, descricao, responsavel):
            with em(60):
                s = Sistema(nome=nome, descricao=descricao, responsavel=responsavel)
                s._history_user = marcos
                s.save()
            return s

        matricula = sistema("Sistema de Matrícula", "Matrícula on-line dos alunos.", patricia)
        portal = sistema("Portal do Aluno", "Notas, boletins, frequência e financeiro.", patricia)
        email = sistema("E-mail institucional", "Correio eletrônico institucional.", bruno)

        def incidente(titulo, descricao, sis, dias, impacto, autor):
            with em(dias) as momento:
                inc = Incidente(
                    titulo=titulo,
                    descricao=descricao,
                    sistema=sis,
                    impacto=impacto,
                    data_ocorrencia=momento - timedelta(hours=1),
                    registrado_por=autor,
                )
                inc._history_user = autor
                inc.save()
            return inc

        # --- PRB-001: Sistema de Matrícula, em correção (exemplo da Seção 3.1) ---
        m1 = incidente(
            "Sistema reiniciado pelo Suporte após queda",
            "Tela branca; serviço reiniciado.",
            matricula,
            16,
            "ALTO",
            ana,
        )
        m2 = incidente(
            "Lentidão extrema e timeout no login",
            "Login demora mais de 1 minuto.",
            matricula,
            12,
            "MEDIO",
            ana,
        )
        m3 = incidente(
            "Matrícula indisponível após atualização noturna",
            "Fora do ar às 07h.",
            matricula,
            10,
            "ALTO",
            joao,
        )
        with em(9):
            p1 = abrir_problema(
                usuario=ana,
                titulo="Queda recorrente do Sistema de Matrícula",
                descricao=(
                    "O sistema fica indisponível em horários de pico; "
                    "o Suporte reinicia o serviço a cada ocorrência."
                ),
                incidentes_ids=[m1.pk, m2.pk, m3.pk],
            )
        with em(8.9):
            atribuir_responsavel_prioridade(
                usuario=marcos, problema_id=p1.pk, responsavel_id=carla.pk, prioridade="ALTA"
            )
        with em(8):
            alterar_status(usuario=carla, problema_id=p1.pk, status=StatusProblema.EM_INVESTIGACAO)
        with em(7):
            registrar_causa_raiz(
                usuario=carla,
                problema_id=p1.pk,
                descricao=(
                    "Esgotamento do pool de conexões com o banco de dados, causado por "
                    "conexões não liberadas em caso de exceção."
                ),
                analise_5_porques=(
                    "1. Por que o sistema cai? Porque as requisições expiram aguardando o banco.\n"
                    "2. Por que expiram? Porque não há conexão livre no pool.\n"
                    "3. Por que não há conexão livre? Porque o pool de 20 conexões "
                    "se esgota no pico.\n"
                    "4. Por que se esgota? Porque consultas com erro não devolvem a conexão.\n"
                    "5. Por que não devolvem? Porque o código de acesso a dados não fecha "
                    "a conexão nos blocos de exceção."
                ),
            )
        with em(6):
            registrar_erro_conhecido(
                usuario=carla,
                problema_id=p1.pk,
                sintoma=(
                    "Sistema de Matrícula lento ou fora do ar (erro 500/timeout) "
                    "em horário de pico."
                ),
                causa="Pool de conexões com o banco esgotado.",
                solucao_contorno=(
                    "Reiniciar o serviço da aplicação de matrícula e avisar "
                    "o Desenvolvedor responsável."
                ),
            )
        with em(5.9):
            alterar_status(usuario=carla, problema_id=p1.pk, status=StatusProblema.ERRO_CONHECIDO)
        m4 = incidente(
            "Erro 500 ao confirmar matrícula",
            "Erro ao confirmar disciplinas.",
            matricula,
            5,
            "ALTO",
            ana,
        )
        with em(5):
            vincular_incidentes(usuario=ana, problema_id=p1.pk, incidentes_ids=[m4.pk])
        with em(4):
            a1 = criar_acao(
                usuario=carla,
                problema_id=p1.pk,
                descricao="Fechar conexões em caso de exceção",
                prazo=(agora - timedelta(days=1)).date(),
                responsavel_id=carla.pk,
            )
            a2 = criar_acao(
                usuario=marcos,
                problema_id=p1.pk,
                descricao="Aumentar o limite do pool de 20 para 60",
                prazo=(agora + timedelta(days=2)).date(),
                responsavel_id=rafael.pk,
            )
            criar_acao(
                usuario=carla,
                problema_id=p1.pk,
                descricao="Criar teste de carga para o pico de matrícula",
                prazo=(agora + timedelta(days=5)).date(),
                responsavel_id=carla.pk,
            )
        with em(3.9):
            alterar_status(usuario=carla, problema_id=p1.pk, status=StatusProblema.EM_CORRECAO)
        with em(3):
            alterar_status_acao(usuario=carla, acao_id=a1.pk, status="EM_ANDAMENTO")
        m5 = incidente(
            "Matrícula fora do ar na abertura do prazo",
            "Indisponível no primeiro dia do prazo.",
            matricula,
            2,
            "ALTO",
            ana,
        )
        with em(2):
            vincular_incidentes(usuario=ana, problema_id=p1.pk, incidentes_ids=[m5.pk])
        with em(1):
            alterar_status_acao(usuario=carla, acao_id=a1.pk, status="CONCLUIDA")
        with em(0.9):
            alterar_status_acao(usuario=rafael, acao_id=a2.pk, status="EM_ANDAMENTO")

        # --- PRB-002: Portal do Aluno, em investigação ---
        b1 = incidente(
            "Boletim não carrega no Portal do Aluno",
            "Página do boletim fica carregando.",
            portal,
            7,
            "MEDIO",
            joao,
        )
        b2 = incidente(
            "Boletim demora mais de 1 minuto para abrir",
            "Lentidão na consulta de notas.",
            portal,
            4,
            "MEDIO",
            ana,
        )
        with em(3):
            p2 = abrir_problema(
                usuario=joao,
                titulo="Boletim lento ou indisponível no Portal do Aluno",
                descricao="Consultas de boletim travam com frequência.",
                incidentes_ids=[b1.pk, b2.pk],
            )
        with em(2.5):
            atribuir_responsavel_prioridade(
                usuario=marcos, problema_id=p2.pk, responsavel_id=rafael.pk, prioridade="MEDIA"
            )
        with em(2):
            alterar_status(usuario=rafael, problema_id=p2.pk, status=StatusProblema.EM_INVESTIGACAO)

        # --- PRB-003: E-mail institucional, ciclo completo até Encerrado ---
        e1 = incidente(
            "Caixa de e-mail cheia sem aviso",
            "Usuário deixou de receber e-mails.",
            email,
            28,
            "BAIXO",
            ana,
        )
        e2 = incidente(
            "E-mails devolvidos por cota excedida",
            "Mensagens retornam ao remetente.",
            email,
            24,
            "BAIXO",
            joao,
        )
        with em(22):
            p3 = abrir_problema(
                usuario=ana,
                titulo="Caixa de e-mail cheia sem aviso ao usuário",
                descricao="Usuários só descobrem a cota excedida quando e-mails são devolvidos.",
                incidentes_ids=[e1.pk, e2.pk],
            )
        with em(21.9):
            atribuir_responsavel_prioridade(
                usuario=marcos, problema_id=p3.pk, responsavel_id=rafael.pk, prioridade="BAIXA"
            )
        with em(21):
            alterar_status(usuario=rafael, problema_id=p3.pk, status=StatusProblema.EM_INVESTIGACAO)
        with em(20):
            registrar_causa_raiz(
                usuario=rafael,
                problema_id=p3.pk,
                descricao="Política de alerta de cota desativada no servidor de e-mail.",
                analise_5_porques=(
                    "1. Por que os e-mails voltam? Cota excedida.\n"
                    "2. Por que o usuário não sabia? Não houve alerta.\n"
                    "3. Por que não houve alerta? A política de aviso estava desativada."
                ),
            )
            registrar_erro_conhecido(
                usuario=rafael,
                problema_id=p3.pk,
                sintoma="Usuário não recebe e-mails ou recebe devoluções.",
                causa="Cota da caixa excedida sem alerta.",
                solucao_contorno="Aumentar temporariamente a cota e orientar a limpeza da caixa.",
            )
        with em(19.9):
            alterar_status(usuario=rafael, problema_id=p3.pk, status=StatusProblema.ERRO_CONHECIDO)
        with em(18):
            a3 = criar_acao(
                usuario=rafael,
                problema_id=p3.pk,
                descricao="Ativar alerta automático de cota em 80%",
                prazo=(agora - timedelta(days=14)).date(),
                responsavel_id=rafael.pk,
            )
        with em(17.9):
            alterar_status(usuario=rafael, problema_id=p3.pk, status=StatusProblema.EM_CORRECAO)
        with em(15):
            alterar_status_acao(usuario=rafael, acao_id=a3.pk, status="EM_ANDAMENTO")
        with em(13):
            alterar_status_acao(usuario=rafael, acao_id=a3.pk, status="CONCLUIDA")
        with em(12):
            alterar_status(usuario=rafael, problema_id=p3.pk, status=StatusProblema.RESOLVIDO)
        with em(11):
            alterar_status(usuario=marcos, problema_id=p3.pk, status=StatusProblema.ENCERRADO)

        # --- Incidentes ainda sem Problema, para demonstrar RF07 e RF09 ---
        incidente(
            "Lentidão ao gerar comprovante de matrícula",
            "Comprovante leva 40 s para gerar.",
            matricula,
            1,
            "MEDIO",
            joao,
        )
        incidente(
            "Frequência não atualiza no Portal do Aluno",
            "Faltas lançadas não aparecem.",
            portal,
            4,
            "BAIXO",
            joao,
        )
        incidente(
            "Erro ao baixar boleto no Portal do Aluno",
            "O PDF do boleto não é gerado.",
            portal,
            1,
            "ALTO",
            ana,
        )
        incidente(
            "Senha do e-mail expirada sem aviso",
            "Usuário bloqueado ao acessar o e-mail.",
            email,
            2,
            "BAIXO",
            ana,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Dados de demonstração carregados: 7 usuários, 3 Sistemas, "
                "13 Incidentes e 3 Problemas. "
                f"Senha dos usuários: {opcoes['senha']}"
            )
        )
