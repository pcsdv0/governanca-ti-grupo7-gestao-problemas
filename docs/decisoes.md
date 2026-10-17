# Registro de decisões

Registro leve: uma linha por decisão, com data e motivo. Decisões novas entram no fim da tabela.

| Data | Decisão | Motivo |
|---|---|---|
| 17/10/2026 | Stack: Python 3.12+ (usamos 3.13), Django 5.2 LTS (5.2.18), templates Django, Bootstrap 5 (CDN), HTMX opcional, Chart.js, django-simple-history, python-decouple, dj-database-url, gunicorn, whitenoise, ruff | Simplicidade para um MVP em 14 dias; detalhes em [arquitetura.md](arquitetura.md). A 5.2 é a LTS mais recente disponível (a 6.1 não é LTS). |
| 17/10/2026 | Banco: SQLite no desenvolvimento, PostgreSQL em produção via `DATABASE_URL` | Zero instalação para o grupo; PostgreSQL gratuito no Render. |
| 17/10/2026 | Hospedagem: Render, plano gratuito. O banco PostgreSQL e o serviço web serão criados **por volta de 28/10/2026** | O banco gratuito do Render expira 30 dias após a criação; criado em 28/10, cobre até depois da apresentação (27/11). |
| 17/10/2026 | Plano B da apresentação: Docker local (`docker compose up --build`) | Não depender da internet nem do Render no dia. |
| 17/10/2026 | Choices gravam o código em maiúsculas (ex.: `GESTOR_TI`) e exibem o rótulo (ex.: "Gestor de TI") | Código estável no banco; rótulo pode aparecer nas telas sem afetar dados. |
| 17/10/2026 | Perfil padrão de um usuário novo: Suporte | Menor privilégio. |
| 17/10/2026 | Superusuário (admin do Django) passa em qualquer restrição de perfil | Permite administrar e demonstrar o sistema sem criar um usuário por perfil. |
| 17/10/2026 | Controle de acesso em `contas/permissoes.py`: decorator `perfil_requerido` e `PerfilRequeridoMixin`. Não logado → login; perfil errado → 403 | Uma regra única para todas as views. |
| 17/10/2026 | Estáticos com `CompressedStaticFilesStorage` (sem manifesto) | Mais simples e não exige `collectstatic` para rodar os testes. |
| 17/10/2026 | Um único `requirements.txt` (inclui o ruff) | Simplicidade: um comando instala tudo. |
| 17/10/2026 | `USAR_HTTPS` liga redirecionamento e cookies seguros só no Render | No Docker local (http) os cookies seguros impediriam o login. |
| 17/10/2026 | Administrador no Render criado no `build.sh` a partir de variáveis `DJANGO_SUPERUSER_*` | O plano gratuito do Render não oferece terminal. |
| 17/10/2026 | Fuso horário `America/Recife` e idioma `pt-br` | Público e banca em Pernambuco. |
| 17/10/2026 | Nomes das funções F2 a F6 deduzidos do plano de tarefas (a validar com o grupo) | Só a F1 foi definida formalmente. |
| 17/10/2026 | Configuração do GitHub (repositório, labels, milestones, issues) feita pelo script `scripts/configurar_github.py` | Repetível e sem retrabalho manual; o script pula o que já existe e não apaga nada. |

## Pendências

- [ ] Nome do sistema (hoje aparece como "Gestão de Problemas").
- [ ] Formato da Entrega 1 exigido pela professora (documento, modelo, extensão).
- [ ] Validar os nomes e responsáveis das funções F2 a F6 ([EQUIPE.md](EQUIPE.md)).
