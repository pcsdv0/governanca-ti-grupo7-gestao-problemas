# Gestão de Problemas - Grupo 7

Sistema web de **Gestão de Problemas** baseado no ITIL 4 e no COBIT 2019 (DSS02 - Gerenciar solicitações de serviço e incidentes; DSS03 - Gerenciar problemas). Projeto da disciplina de Governança de TI, 6º período, UNINASSAU.

> **Situação atual: esqueleto.** Já funcionam o login/logout, a página inicial protegida, o usuário com os 4 perfis e o controle de acesso por perfil. Os módulos de negócio (incidentes, problemas, causa raiz, ações corretivas, KEDB e dashboard) estão criados **vazios** e serão implementados nas Entregas 2 e 3 (ver [Funções](#funções-da-equipe) e as issues do repositório).

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
| Linguagem | Python 3.12+ (desenvolvido e testado com 3.13) |
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
├── contas/              # F1 - Usuário, perfis, login e controle de acesso (pronto)
│   └── permissoes.py    #      perfil_requerido e PerfilRequeridoMixin
├── sistemas/            # F2 - Sistemas de TI (vazio)
├── incidentes/          # F2 - Incidentes (vazio)
├── problemas/           # F1/F2 - Problemas, causa raiz, histórico (vazio)
│   └── constantes.py    #      status do Problema
├── acoes/               # F2 - Ações corretivas (vazio)
│   └── constantes.py    #      status da Ação corretiva
├── kedb/                # F2 - Base de erros conhecidos (vazio, Entrega 3)
├── dashboard/           # F3 - Indicadores (vazio, Entrega 3)
├── templates/           # base.html, inicio.html, 403.html, registration/login.html
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

## Testes e lint

```bash
python manage.py test                          # testes
ruff check .                                   # lint
ruff format .                                  # formata o código
python manage.py makemigrations --check --dry-run   # confere se falta migration
```

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
- [docs/modelo-de-dados.md](docs/modelo-de-dados.md): entidades e relação central (rascunho)
- [docs/decisoes.md](docs/decisoes.md): registro de decisões e pendências
- [docs/EQUIPE.md](docs/EQUIPE.md): funções, responsáveis e backups
- [CONTRIBUTING.md](CONTRIBUTING.md): branches, commits e pull requests

## O que já existe e o que falta

| Pronto (esqueleto) | A implementar |
|---|---|
| Projeto Django configurado (dev, Docker, Render) | Incidentes, Sistemas (Entrega 2) |
| Usuário com perfil e admin | Problemas, causa raiz, ciclo de status, histórico (Entrega 2) |
| Login, logout e página inicial protegida | Ações corretivas (Entrega 2) |
| Controle de acesso por perfil, com testes | KEDB, alerta de recorrência (Entrega 3) |
| Choices de status do Problema e da Ação corretiva | Dashboard e indicadores, aprovação de encerramento (Entrega 3) |
| CI, lint, modelos de PR/issue, documentação inicial | Dados de demonstração |
