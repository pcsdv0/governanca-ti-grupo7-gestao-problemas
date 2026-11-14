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

## Implementação F2 — 08/11/2026

As regras abaixo foram confirmadas no escopo acadêmico informado para esta implementação; as escolhas de código estão identificadas como técnicas e não alteram os nomes padronizados.

| Base | Aplicação | Motivo |
|---|---|---|
| RF04 confirmado | Cadastro, edição e listagem de Sistema com nome, descrição e responsável, restritos ao Gestor de TI | Entregar o módulo definido no planejamento |
| Padrões existentes | Reutilizar `contas/permissoes.py`, exceção de superusuário e `HistoricalRecords()` com o middleware atual | Manter autorização e auditoria consistentes com a arquitetura |
| Escolha técnica autorizada no escopo | Namespace `sistemas` e rotas `/sistemas/`, `/sistemas/novo/` e `/sistemas/<int:pk>/editar/` | Não havia convenção específica; usar as rotas propostas, com GET para páginas e POST para gravações |
| Escolhas técnicas de persistência | Nome com até 200 caracteres; FK do responsável com `PROTECT` | Definir armazenamento textual e preservar referências; sem unicidade de nome ou fluxo de exclusão |
| Limite inicial do escopo | Preparação de Incidentes inicialmente documental, antes da confirmação de impacto | A evolução funcional está registrada abaixo; vínculo com Problema continua dependente da F1 |

## Confirmações da F2 — 08/11/2026

| Decisão confirmada pelo responsável pela F2 | Aplicação |
|---|---|
| A data da ocorrência de Incidente inclui horário | Usar `DateTimeField` no modelo de Incidentes, respeitando o fuso e `USE_TZ` existentes. |
| O responsável por Sistema deve possuir perfil `RESPONSAVEL_SISTEMA` | Restringir seleção e validação nos formulários da aplicação e do admin; gerar migration e testar a rejeição de outros perfis, inclusive em POST do superusuário. |

### Evolução após as confirmações

| Decisão confirmada pelo responsável pela F2 | Aplicação |
|---|---|
| Impacto com níveis Baixo, Médio e Alto e as definições propostas | Choices `BAIXO`, `MEDIO` e `ALTO` em `ImpactoIncidente`; definições em `convencoes.md` e no formulário; preenchimento obrigatório, sem valor padrão |
| Suporte edita os próprios incidentes; Gestor de TI edita qualquer registro | Verificação no servidor para GET/POST; autor original imutável no formulário e auditoria de cada edição; exceção de superusuário preservada |
| Filtro por duas datas opcionais, incluindo os dias inicial e final completos em America/Recife | Campos De/Até na listagem, combináveis com Sistema; intervalo invertido produz erro de validação |

Com impacto e edição definidos, cadastro e consulta de Incidentes passam a ser funcionais. RF06 permanece parcial: o vínculo com Problema e seu filtro dependem da F1. Incidentes não é exposto no admin nesta etapa; o histórico é persistido por `HistoricalRecords` e consultável pelo ORM. Não houve ampliação para Problemas, causa raiz ou ações corretivas.

Escolhas técnicas: título com até 200 caracteres, referências com `PROTECT` e rotas no namespace `incidentes` (`/incidentes/`, `/incidentes/novo/`, `/incidentes/<int:pk>/editar/`), seguindo o padrão de Sistemas.

## Pendências

- [x] Integrar a navegação dos módulos na página inicial com a F3, atendendo ao requisito da AV2 de acesso às telas principais em até três cliques.

- [x] Integrar as telas de Problemas com a F3 conforme `integracao-problemas-f3.md`.
- [x] Integrar Ações Corretivas e sua validação de conclusão para o encerramento de Problemas (backend F2 do MVP).
- [ ] Nome do sistema (hoje aparece como "Gestão de Problemas").
- [ ] Formato da Entrega 1 exigido pela professora (documento, modelo, extensão).
- [ ] Validar os nomes e responsáveis das funções F2 a F6 ([EQUIPE.md](EQUIPE.md)).

## Ampliação de escopo e confirmações da F2 — 09/11/2026

A solicitação de implementar o backend de Problemas nesta entrega substitui a estratégia anterior de aguardar uma implementação da F1. As telas permanecem com a F3. Esta autorização não redefine a divisão geral da equipe no planejamento acadêmico.

| Decisão confirmada pelo responsável pela F2 | Aplicação prevista |
|---|---|
| Prioridades Baixa, Média e Alta; prioridade e responsável inicialmente sem atribuição | Abertura pelo Suporte e atribuição posterior de ambos pelo Gestor de TI (RF11) |
| Vincular somente Incidentes do mesmo Sistema do Problema, sem vínculo com outro Problema | Preservar a relação opcional de um Incidente com no máximo um Problema |
| Repetir o vínculo com o mesmo Problema não gera duplicação | Operação idempotente; transferência e desvinculação fora desta etapa |

### Confirmações complementares e implementação

| Decisão confirmada pelo responsável pela F2 | Aplicação |
|---|---|
| Somente usuários com perfil Desenvolvedor podem ser responsáveis por Problema | Seleção e validação no RF11, inclusive para superusuário |
| Sequência Registrado → Em investigação → Erro conhecido → Em correção → Resolvido → Encerrado, sem saltos nem reabertura | Desenvolvedor e Gestor avançam até Resolvido; encerramento exclusivo do Gestor, respeitada a exceção de superusuário |
| Encerramento pendente de integração com Ações Corretivas concluídas | Solicitação da última transição retorna erro de validação; não se presume conclusão de ações inexistentes |

O backend de Problemas, HistóricoStatus, vínculo com Incidentes, filtro de vínculo, formulários e views foram implementados. O contrato está em [integracao-problemas-f3.md](integracao-problemas-f3.md). As telas permanecem com a F3.

Escolhas técnicas: título com 200 caracteres; referências com `PROTECT`; prioridade vazia e responsável nulo representam ausência de atribuição; serviços usam transações e bloqueio de linhas no PostgreSQL. HistóricoStatus é derivado automaticamente da auditoria de Problema, incluindo a abertura. As rotas de Problemas aguardam os templates para serem montadas em `config/urls.py`. Não há escrita pelo admin nem operação genérica de edição de Problema.

Os registros de 08/11 acima preservam o contexto histórico; a dependência anterior de aguardar a F1 foi substituída pela ampliação de escopo desta etapa.


## Fechamento do backend F2 do MVP — 09/11/2026

A F2 solicitou concluir o backend do MVP, preservando as telas com a F3. Conferência do planejamento ajustado da AV2, seções 4/4.1/5/6.2: RF15, RF17, RF20, RF21 e RF23/RF24 pertencem ao MVP. A classificação anterior do módulo KEDB inteiro como versão final estava incorreta: RF17 é MVP; RF18 (pesquisa) e RF29 (alerta de recorrência) são versão final. Ver [escopo-backend-mvp.md](escopo-backend-mvp.md).

| Regra confirmada pelo responsável pela F2 | Implementação |
|---|---|
| Uma CausaRaiz e um ErroConhecido por Problema; qualquer Desenvolvedor cadastra/atualiza; sem exclusão | OneToOneField para Problema, formulários, serviços e views auditados |
| Análise dos 5 Porquês em texto; salvar causa/erro não muda automaticamente o status de Problema | Campos textuais obrigatórios e transição de Problema mantida como operação separada |
| Responsável da ação deve ser Desenvolvedor; prazo como data; status inicial Aberta | Validação em formulário e modelo; prazo sem restrições adicionais |
| Desenvolvedor e Gestor criam ações; qualquer Desenvolvedor altera status por Aberta → Em andamento → Concluída | Autorização e transições validadas nos serviços; sem saltos, retorno ou edição dos outros campos |
| Encerramento exige ao menos uma ação e todas Concluídas | Integração ao serviço de status de Problema, exclusiva do Gestor com exceção de superusuário |
| Após Encerrado, nenhuma nova ação ou alteração do status das ações | Validação sob bloqueio do Problema na mesma transação da gravação/auditoria |

Escolhas técnicas: referências com `PROTECT`; status e FK de Problema fora dos campos controlados pelos formulários; mesma ordem de bloqueio (Problema antes de AçãoCorretiva) para evitar disputa entre encerramento e alterações de ações no PostgreSQL. A unicidade de CausaRaiz/ErroConhecido é garantida no banco. A auditoria de ações usa django-simple-history, conforme seção 6.2, sem outro modelo HistóricoStatus.

O detalhe do Problema reúne os dados e seus históricos em uma linha do tempo. As rotas continuam aguardando as telas da F3. A decisão anterior de bloquear todo encerramento enquanto faltava Ações Corretivas é substituída pela validação funcional acima. Não foram implementados pesquisa global na KEDB, alerta de recorrência, dashboard, reabertura ou validação final de encerramento.

Migrations novas: `problemas/0002_causaraiz_historicalcausaraiz.py`, `acoes/0001_initial.py` e `kedb/0001_initial.py`. Dependências Python permanecem fixadas e inalteradas.


## Integração das telas (F3) e fechamento do MVP — 13/11/2026

| Decisão | Aplicação | Motivo |
|---|---|---|
| Layout com barra lateral escura e navegação por perfil | `templates/base.html` e `static/css/estilo.css` | Seguir os protótipos das Figuras 4 a 7 do planejamento e manter as telas principais a até três cliques |
| Códigos exibidos INC-001, PRB-001 e AC-001, derivados do `pk` | Filtro `codigo` em `contas/templatetags/interface.py` | Os protótipos identificam Incidentes e Problemas por código; sem campo novo no banco |
| Avanço de status por botão "Avançar para …" com o próximo status da sequência | Detalhe do Problema e das Ações | Reforça a regra de sequência sem saltos; o serviço continua sendo quem valida |
| RF02 com telas próprias para o Gestor de TI | `contas/views.py`, `contas/forms.py` e templates em `contas/templates/contas/` | RF02 é MVP no planejamento (Tabela 3); antes só existia pelo admin do Django |
| Lista global de Ações Corretivas, com filtro por status e responsável | `acoes:listar` | Protótipo da Figura 6; respeita o escopo do Responsável pelo sistema |
| Dados de demonstração pelo comando `carregar_demo`, gravando pelos serviços | `problemas/management/commands/carregar_demo.py`; opcional no Render com `CARREGAR_DEMO=True` | Tarefa da F6; garante regras e auditoria iguais às do uso real |
| Fluxo sem saltos (Em investigação → Erro conhecido é obrigatório) | Mantida a decisão da F2 de 09/11 | A Figura 1 do planejamento mostra um atalho "correção definitiva imediata"; a diferença fica registrada para a atualização do diagrama na documentação final |
