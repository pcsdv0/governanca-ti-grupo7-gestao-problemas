# Gestão de Problemas - Grupo 7

Sistema web de **Gestão de Problemas** baseado no ITIL 4 e no COBIT 2019 (DSS02 - Gerenciar solicitações de serviço e incidentes; DSS03 - Gerenciar problemas). Projeto da disciplina de Governança de TI, 6º período, UNINASSAU.

> **Situação atual (Entrega 2 · MVP, 13/11/2026):** o MVP está **completo e navegável**. Todos os requisitos marcados como MVP no planejamento (RF01, RF02, RF04 a RF07, RF09 a RF12, RF15, RF17, RF20, RF21, RF23 e RF24) têm backend e tela: Usuários, Sistemas, Incidentes, Problemas, CausaRaiz, ErroConhecido, Ações Corretivas e histórico de auditoria, com navegação por perfil e dados de demonstração. Pesquisa na KEDB (RF18), alerta de recorrência (RF29), dashboard (RF25/RF26) e validação do Responsável pelo sistema no encerramento (RF13) são da versão final. O escopo exato está em [docs/escopo-backend-mvp.md](docs/escopo-backend-mvp.md).

## Demonstração rápida

```bash
pip install -r requirements.txt
cp .env.example .env          # no PowerShell: copy .env.example .env
python manage.py migrate
python manage.py carregar_demo
python manage.py runserver
```

Acesse <http://127.0.0.1:8000>. Usuários de demonstração (senha `demo1234`):

| Login | Nome | Perfil |
|---|---|---|
| `suporte` / `suporte2` | Ana Lima / João Ferreira | Suporte |
| `dev` / `dev2` | Carla Mendes / Rafael Souza | Desenvolvedor |
| `gestor` | Marcos Oliveira | Gestor de TI |
| `responsavel` | Patrícia Rocha | Responsável pelo sistema (Sistema de Matrícula e Portal do Aluno) |
| `responsavel2` | Bruno Almeida | Responsável pelo sistema (E-mail institucional) |

O comando `carregar_demo` grava tudo pelos serviços do backend (mesmas regras, permissões e auditoria do uso real) e só carrega dados se o banco ainda não tiver Incidentes. Ele cria 3 Problemas: **PRB-001** (Sistema de Matrícula, em correção, 5 ocorrências), **PRB-002** (Portal do Aluno, em investigação) e **PRB-003** (E-mail institucional, ciclo completo até Encerrado), além de 4 Incidentes sem Problema para demonstrar a abertura. Roteiro de demonstração em [docs/roteiro-demonstracao.md](docs/roteiro-demonstracao.md); telas em [docs/telas/](docs/telas/).

## O problema que resolvemos

Cenário do Grupo 7: *problemas recorrentes sem solução definitiva*. A equipe de TI recebe chamados sobre os mesmos erros, aplica uma solução de contorno e fecha o chamado, sem investigar a causa raiz. O sistema conecta incidentes a problemas, conduz a investigação de causa raiz, mantém uma base de erros conhecidos (KEDB) e acompanha as ações corretivas até o encerramento, com indicadores para os gestores.

### Incidente x Problema

| | Incidente | Problema |
|---|---|---|
| O que é | Interrupção ou degradação de um serviço | Causa raiz desconhecida de um ou mais incidentes |
| Objetivo | Restaurar rápido, com solução de contorno | Investigar, corrigir de forma definitiva e evitar reincidência |

Relação central: **um Problema se relaciona com vários Incidentes.**

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ (esta entrega validada com 3.14.9) |
| Framework | **Django 5.2.18 (LTS)** |
| Interface | Templates Django, Bootstrap 5 (CDN), HTMX (opcional), Chart.js (dashboard) |
| Banco | SQLite (desenvolvimento) / PostgreSQL (produção, via `DATABASE_URL` + dj-database-url) |
| Auditoria | django-simple-history |
| Configuração | python-decouple (variáveis de ambiente / `.env`) |
| Produção | gunicorn + whitenoise, hospedado no Render (plano gratuito) |
| Qualidade | ruff (lint e formatação), testes do Django, GitHub Actions |

Versões fixadas em [requirements.txt](requirements.txt). Motivos das escolhas em [docs/arquitetura.md](docs/arquitetura.md).

## Estrutura de pastas

```
.
├── config/              # Configurações do projeto (settings, urls, wsgi)
├── contas/              # F1 - Usuário, perfis, login, controle de acesso e telas de Usuários (RF02)
│   ├── permissoes.py    #      perfil_requerido e PerfilRequeridoMixin
│   └── templatetags/    #      F3 - filtros de interface (códigos INC/PRB, cores, perfil)
├── sistemas/            # F2 - Sistemas: modelo, formulários, views, templates, admin e testes
├── incidentes/          # F2 - Cadastro, edição, filtros, auditoria e FK para Problema
├── problemas/          # F1/F2/F3 - Problemas, causa raiz, histórico, telas e carregar_demo
│   └── constantes.py    #      status do Problema
├── acoes/               # F2/F3 - Ações corretivas, histórico e telas
│   └── constantes.py    #      status da Ação corretiva
├── kedb/                # F2/F3 - Registro de ErroConhecido (MVP); pesquisa na Entrega 3
├── dashboard/           # F3 - Indicadores (vazio, Entrega 3)
├── templates/           # base.html (barra lateral por perfil), inicio.html, 403.html, login
├── static/              # CSS próprio
├── docs/                # Documentação do projeto
├── scripts/             # configurar_github.py (configuração inicial do GitHub)
├── .github/             # CI, modelo de PR e de issues
├── Dockerfile, docker-compose.yml   # Plano B: rodar local com PostgreSQL
├── build.sh, render.yaml            # Deploy no Render
└── requirements.txt, pyproject.toml, .env.example
```

## Como rodar localmente

### Opção 1: ambiente virtual (dia a dia)

Pré-requisitos: Python 3.12 ou superior e Git.

```bash
git clone https://github.com/pcsdv0/governanca-ti-grupo7-gestao-problemas.git
cd governanca-ti-grupo7-gestao-problemas

python -m venv .venv
# Windows (PowerShell):   .venv\Scripts\Activate.ps1
# Windows (Git Bash):     source .venv/Scripts/activate
# Linux/macOS:            source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # no PowerShell: copy .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse <http://127.0.0.1:8000> e entre com o usuário criado. Para criar usuários com outros perfis, use o admin em <http://127.0.0.1:8000/admin/> (campo "Perfil").

### Opção 2: Docker (plano B da apresentação)

Pré-requisito: Docker Desktop aberto.

```bash
docker compose up --build                                  # sobe web + PostgreSQL
docker compose exec web python manage.py createsuperuser   # em outro terminal, na primeira vez
```

Acesse <http://localhost:8000>. Para parar: `Ctrl+C` e `docker compose down` (os dados ficam no volume; `docker compose down -v` apaga o banco).

## Sistemas (RF04)

Após configurar o ambiente e executar `python manage.py migrate`, entre no sistema e acesse <http://127.0.0.1:8000/sistemas/>. A navegação global continua sob responsabilidade da F3; o módulo pode ser aberto diretamente pelo endereço.

- **Listar:** `/sistemas/`.
- **Cadastrar:** `/sistemas/novo/`.
- **Editar:** `/sistemas/<id>/editar/`, pelo botão **Editar** na lista.
- **Acesso:** Gestor de TI e superusuário. Anônimos seguem para login; Suporte, Desenvolvedor e Responsável pelo sistema recebem 403 nessas operações.
- **Dados obrigatórios:** nome (até 200 caracteres), descrição e Responsável pelo sistema. Dados inválidos mantêm o formulário aberto com mensagens de erro. GET exibe páginas; POST grava com proteção CSRF.
- **Seleção do responsável:** exige usuário com o perfil `RESPONSAVEL_SISTEMA`, tanto no formulário da aplicação quanto no admin. A validação no servidor também rejeita outros perfis enviados diretamente por POST, inclusive quando o operador é superusuário. A associação não altera as permissões do usuário.
- **Auditoria:** cadastro e edição registram valores, data e autor autenticado. Para conferir, entre em `/admin/`, abra o Sistema e seu **Histórico**. O admin mantém `is_staff`, permissões Django e a restrição de perfil; superusuário tem acesso. Não há exclusão disponível.

Para uma conferência manual: cadastre um Sistema, confira os dados na listagem, edite o nome ou responsável e verifique as duas versões no histórico. Entre com outro perfil e confirme o acesso negado. Os testes automatizados cobrem esses fluxos, os quatro perfis, superusuário, campos obrigatórios, referências inválidas, CSRF e autoria do histórico.

O vínculo Sistema–Responsável explicita responsabilidades. O controle por perfil restringe as operações, e o histórico oferece rastreabilidade para demonstrar governança no trabalho.

## Incidentes (RF05/RF06)

Após executar `python manage.py migrate`, acesse <http://127.0.0.1:8000/incidentes/>. Cadastre antes um Sistema como Gestor de TI ou superusuário.

- **Cadastro:** `/incidentes/novo/`, permitido ao Suporte. Título, descrição, data e hora da ocorrência, impacto e Sistema afetado são obrigatórios. O servidor atribui o usuário autenticado como autor.
- **Impacto:** Baixo (efeito limitado, serviço principal disponível), Médio (degradação relevante ou indisponibilidade parcial) e Alto (serviço essencial indisponível ou operação amplamente afetada), conforme confirmado pela F2.
- **Edição:** `/incidentes/<id>/editar/`. Suporte edita os próprios registros; Gestor de TI edita qualquer registro. A edição permite corrigir os campos do cadastro e preserva o autor original.
- **Consulta:** Suporte, Desenvolvedor e Gestor de TI consultam todos os incidentes. Responsável pelo sistema consulta somente os incidentes dos sistemas associados a ele.
- **Filtros:** Sistema, vínculo com Problema (Todos / Com vínculo / Sem vínculo) e período por datas De/Até, opcionais e combináveis. Os dias inicial e final são incluídos integralmente no fuso America/Recife. Filtros inválidos exibem erros.
- **Superusuário:** mantém a exceção existente para todas as operações.
- **Auditoria:** histórico de valores, data e editor em cada cadastro/edição; disponível pelo ORM (`incidente.history.all()`). Incidentes não é exposto no admin nesta etapa.
- **Segurança:** CSRF, validação no servidor, 403 para edição sem permissão e 404 para registro inexistente. GET não grava. Não há exclusão.

Para conferir: registre um Incidente como Suporte, filtre por Sistema e pelo dia da ocorrência, edite com o próprio autor e com um Gestor e verifique a preservação de `registrado_por` e os editores em `history_user`. Outro usuário Suporte deve receber 403 ao tentar editar esse registro.

A FK opcional para `problemas.Problema` e o filtro por vínculo estão implementados. O vínculo é feito pelos serviços/views de Problemas (RF07), com tela pendente da F3. Um Incidente vinculado não pode trocar para outro Sistema na edição comum; seu autor original e vínculo são preservados. Veja [docs/modelo-de-dados.md](docs/modelo-de-dados.md).

Os templates mínimos reaproveitam a estrutura visual existente. Os links na página inicial e o requisito de acesso em até três cliques serão integrados com a F3.

## Usuários (RF02)

O Gestor de TI cadastra e edita Usuários em **Cadastros → Usuários** (`/contas/usuarios/`), definindo nome, login, e-mail, senha inicial e perfil. A edição permite trocar o perfil e inativar o acesso, sem exclusão. Os demais perfis recebem 403. O admin do Django continua disponível para o superusuário.

## Problemas, CausaRaiz, ErroConhecido e Ações Corretivas — telas integradas

Nesta etapa, a F2 implementou o backend de Problemas por solicitação expressa, sem alterar a divisão geral da equipe abaixo.

- Suporte abre um Problema a partir de um ou mais Incidentes do mesmo Sistema e vincula outros Incidentes.
- A abertura usa status Registrado, responsável não atribuído e prioridade não atribuída.
- Gestor de TI atribui um Desenvolvedor e prioridade Baixa, Média ou Alta.
- Desenvolvedor e Gestor avançam na sequência Registrado → Em investigação → Erro conhecido → Em correção → Resolvido.
- Gestor de TI encerra a partir de Resolvido somente quando existe pelo menos uma AçãoCorretiva e todas estão Concluídas. Superusuário também precisa atender à regra. Após encerramento, novas ações e alterações de status das ações são bloqueadas. Não há saltos, reabertura, transferência, desvinculação ou exclusão.
- Consulta inclui contagem de incidentes, CausaRaiz, ErroConhecido, ações, histórico de status e linha do tempo de alterações. Responsável pelo sistema consulta somente seus sistemas.
- Modelos, migrations, serviços transacionais, formulários e views estão implementados e testáveis sem telas finais.

**Acesso:** menu **Problemas** (`/problemas/`) e **Ações corretivas** (`/acoes/`). Na lista de Incidentes, o Suporte marca os Incidentes sem vínculo e clica em **Abrir Problema com os selecionados**. O detalhe do Problema reúne a barra do ciclo de status, o botão de avanço para o próximo status (conforme o perfil) e as abas Incidentes vinculados, Causa raiz, Erro conhecido, Ações corretivas e Histórico. As telas seguem o contrato de [docs/integracao-problemas-f3.md](docs/integracao-problemas-f3.md). Não há API REST nem escrita desses módulos pelo admin.

No PowerShell, na raiz do projeto:

```powershell
$env:DEBUG = "True"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test problemas incidentes acoes kedb
.\.venv\Scripts\python.exe manage.py runserver
```

Os testes de `problemas/test_backend.py` e `problemas/test_mvp.py` verificam as views com templates em memória; `problemas/test_telas.py` percorre o fluxo completo com os templates reais e as rotas de `config/urls.py`.

## CausaRaiz, ErroConhecido e Ações Corretivas — backend do MVP

- **RF15:** qualquer Desenvolvedor cadastra ou atualiza uma CausaRaiz por Problema, com descrição e análise dos 5 Porquês em texto.
- **RF17:** qualquer Desenvolvedor cadastra ou atualiza um ErroConhecido por Problema, com sintoma, causa e solução de contorno. Salvar causa ou erro não muda automaticamente o status do Problema.
- **RF20:** Desenvolvedor e Gestor criam AçãoCorretiva com descrição, responsável Desenvolvedor e prazo como data. O status inicial é Aberta; não há restrição adicional de data.
- **RF21:** qualquer Desenvolvedor avança a ação por Aberta → Em andamento → Concluída, sem saltos ou retornos. A edição de descrição, prazo e responsável não é oferecida nesta etapa.
- **RF23/RF24:** os três modelos usam django-simple-history, com autor, data e valores. O detalhe de Problema reúne os registros e seus históricos, respeitando o escopo por Sistema.
- A exceção de superusuário preserva as validações de negócio. Não há exclusão.

RF17 pertence ao MVP, conforme o planejamento da AV2. Somente a consulta/pesquisa global na KEDB (RF18) fica para a versão final. O registro também pode ser consultado no detalhe autorizado do Problema.

## Testes e lint

```bash
python manage.py check                         # configuração do Django
python manage.py test                          # testes
ruff check .                                   # lint
ruff format --check .                          # confere a formatação
python manage.py makemigrations --check --dry-run   # confere se falta migration
```

Para testar os módulos desta entrega: `python manage.py test sistemas incidentes problemas acoes kedb`. Se precisar formatar, passe ao `ruff format` somente os arquivos alterados.

O GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) roda lint, `manage.py check`, a checagem de migrations e os testes a cada push e pull request.

## Deploy no Render

O deploy usa o blueprint [render.yaml](render.yaml) (serviço web + PostgreSQL gratuitos) e o script [build.sh](build.sh), que instala as dependências, coleta os estáticos, aplica as migrations e cria o administrador.

> **Só criar o banco e o serviço por volta de 28/10/2026.** O PostgreSQL gratuito do Render expira 30 dias após a criação.

1. Entre em <https://dashboard.render.com> com a conta do GitHub.
2. **New → Blueprint**, escolha este repositório e a branch `main`.
3. O Render lê o `render.yaml` e pede os valores de `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` (o administrador). Preencha e confirme.
4. Aguarde o build. O endereço fica no formato `https://gestao-problemas.onrender.com` (ou com um sufixo, se o nome estiver em uso).
5. A cada push na `main` o Render faz o deploy de novo automaticamente.

**Avisos importantes**

- **O serviço gratuito hiberna após 15 minutos sem acesso.** O primeiro acesso depois disso demora cerca de 1 minuto. **Abra o site alguns minutos antes de demonstrar.**
- **O banco gratuito expira 30 dias após a criação.** Se precisar recriá-lo, rode o deploy de novo e **repovoe com os dados de demonstração**.
- Se o Render falhar no dia, use o plano B (Docker local).

## Fluxo de trabalho com Git

- `main`: só o que é entregue. `develop`: integração (branch padrão). Trabalho em `feat/<funcao>-<assunto>`.
- Commits em [Conventional Commits](https://www.conventionalcommits.org/pt-br/) em português: `feat(incidentes): cadastro de incidentes`.
- Todo PR vai para `develop`, com revisão de pelo menos 1 pessoa e CI verde.
- **Nomes padronizados vêm de [docs/convencoes.md](docs/convencoes.md).**

Detalhes em [CONTRIBUTING.md](CONTRIBUTING.md).

## Funções da equipe

| Função | Papel | Responsabilidades |
|---|---|---|
| F1 | Líder técnico e arquiteto | Stack, repositório, arquitetura, login e perfis, Problemas e ciclo de status, histórico/auditoria, indicadores, aprovação de encerramento, deploy |
| F2 | Back-end e modelo de dados | Modelo de dados, Incidentes, vínculo incidente-problema, causa raiz (5 Porquês), ações corretivas, KEDB, alerta de recorrência |
| F3 | Front-end e interface | Protótipo, telas e navegação por perfil, integração às views, dashboard, refinamentos |
| F4 | Requisitos e documentação | Descrição do problema, perfis, funcionalidades (MVP), diagramas, fechamento da documentação |
| F5 | Governança (ITIL 4 / COBIT 2019) | Conceitos de governança e tabela conceito → funcionalidade, matriz RACI, referências |
| F6 | Qualidade e entregas | Documento e consistência de nomes, plano e casos de teste, dados de demonstração, envio das entregas, slides |

Responsáveis e backups em [docs/EQUIPE.md](docs/EQUIPE.md).

### Prazos

| Marco | Data |
|---|---|
| Entrega 1 - Planejamento | 30/10/2026 |
| Entrega 2 - MVP | 13/11/2026 |
| Entrega 3 - Versão final | 23/11/2026 |
| Apresentação | 27/11/2026 |

## Documentação

- [docs/convencoes.md](docs/convencoes.md): perfis, status e entidades (**fonte da verdade**)
- [docs/arquitetura.md](docs/arquitetura.md): visão geral, diagrama e decisões técnicas
- [docs/modelo-de-dados.md](docs/modelo-de-dados.md): estrutura implementada de Sistemas, Incidentes e Problemas e pendências de integração
- [docs/decisoes.md](docs/decisoes.md): registro de decisões e pendências
- [docs/EQUIPE.md](docs/EQUIPE.md): funções, responsáveis e backups
- [docs/escopo-backend-mvp.md](docs/escopo-backend-mvp.md): requisitos F2 do MVP e distinção da versão final
- [docs/integracao-problemas-f3.md](docs/integracao-problemas-f3.md): contrato das views, formulários, contextos e ativação das telas
- [docs/roteiro-demonstracao.md](docs/roteiro-demonstracao.md): roteiro da demonstração do MVP
- [docs/auditoria-entrega2.md](docs/auditoria-entrega2.md): auditoria planejamento × sistema da Entrega 2
- [docs/entregas/](docs/entregas/): documento da Entrega 2 (Word e PDF)
- [CONTRIBUTING.md](CONTRIBUTING.md): branches, commits e pull requests

## O que já existe e o que falta

| Pronto (MVP) | A implementar (versão final, 23/11) |
|---|---|
| Projeto Django configurado (dev, Docker, Render) | Dashboard e indicadores com Chart.js (RF25, RF26) |
| Login, logout, perfis e controle de acesso (RF01) | Alerta de recorrência (RF29) |
| Usuários: cadastro, edição e perfil pelo Gestor de TI (RF02) | Pesquisa por palavra-chave na KEDB (RF18) |
| Sistemas (RF04) | Validação do Responsável pelo sistema no encerramento (RF13) |
| Incidentes com filtros, seleção e abertura de Problema (RF05 a RF07, RF09) | Atualização dos diagramas e documentação final |
| Problemas: atribuição, ciclo de status, detalhe e contagem (RF10 a RF12) | |
| CausaRaiz (RF15), ErroConhecido (RF17), Ações Corretivas (RF20, RF21) | |
| Histórico de status e linha do tempo de auditoria (RF23, RF24) | |
| Navegação por perfil (barra lateral), dados de demonstração e testes das telas | |
