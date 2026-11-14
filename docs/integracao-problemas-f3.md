# Integração de Problemas com a F3

## Entrega e divisão desta etapa

O backend de Problemas, CausaRaiz, ErroConhecido, Ações Corretivas e sua integração com Incidentes foram implementados pela F2 por solicitação expressa nesta etapa. A F3 permanece responsável pelas telas e navegação. Isso não redefine a divisão geral da equipe no planejamento.

Referência: [planejamento ajustado da AV2](https://drive.google.com/file/d/1lEc7vGRQy9dLvFSo6MaVAGorN_kbnqKA/view), seções 4 (RF07, RF09–RF12, RF15, RF17, RF20/RF21, RF23/RF24), 5 (modelo de dados) e 6 (encerramento no MVP). Regras complementares confirmadas na conversa estão em [decisoes.md](decisoes.md).

A arquitetura continua monolítica: views, formulários e templates Django. Não há API REST.

## Ativação das telas

> **Concluída em 13/11/2026 (Entrega 2).** Os templates abaixo foram criados, os includes estão montados em `config/urls.py` e a navegação por perfil fica na barra lateral de `templates/base.html`. Além do contrato, foram acrescentadas a lista global de Ações Corretivas (`acoes:listar`, protótipo da Figura 6) e a pré-seleção de Incidentes na abertura do Problema (`/problemas/novo/?incidentes=<id>`). O aceite com templates reais está em `problemas/test_telas.py`.

A F3 criou:

1. `problemas/templates/problemas/lista.html`, estendendo `base.html`.
2. `problemas/templates/problemas/detalhe.html`, estendendo `base.html`.
3. `problemas/templates/problemas/form.html`, estendendo `base.html`.
4. `acoes/templates/acoes/form.html`, estendendo `base.html`.
5. `kedb/templates/kedb/form.html`, estendendo `base.html`.
6. A navegação por perfil, incluindo links desde Incidentes, a página inicial e o detalhe de Problema.
7. Depois de criar as telas, adicionar em `config/urls.py` os includes `path("problemas/", include("problemas.urls"))`, `path("acoes/", include("acoes.urls"))` e `path("kedb/", include("kedb.urls"))`. Verificar os fluxos reais no navegador.

Os templates em memória de `problemas/test_backend.py` e `problemas/test_mvp.py` existem somente para testar as views. Não são telas de produção. O filtro de vínculo de Incidentes já aparece no formulário genérico existente, sem novo template.

## Contrato das views

Os caminhos abaixo são relativos a `/problemas/`. Os nomes de URL usam o namespace `problemas`.

| Caminho | Nome | Método | Acesso | Template / contexto |
|---|---|---|---|---|
| `/` | `listar` | GET | Quatro perfis | `lista.html`: `problemas` |
| `/novo/` | `cadastrar` | GET/POST | Suporte | `form.html`: `form`, `titulo` |
| `/<pk>/` | `detalhe` | GET | Quatro perfis, respeitando escopo | `detalhe.html`: `problema`, `incidentes`, `historico_status`, `historico` |
| `/<pk>/vincular/` | `vincular` | GET/POST | Suporte | `form.html`: `form`, `problema`, `titulo` |
| `/<pk>/atribuir/` | `atribuir` | GET/POST | Gestor de TI | Mesmo contexto de formulário |
| `/<pk>/status/` | `alterar_status` | GET/POST | Desenvolvedor e Gestor de TI | Mesmo contexto de formulário |
| `/<pk>/causa-raiz/` | `registrar_causa_raiz` | GET/POST | Desenvolvedor | `form.html`: `form`, `problema`, `causa_raiz` (ou `None`), `titulo` |

- Cada item da listagem e o objeto do detalhe expõem `quantidade_incidentes`, calculada no banco.
- `historico_status` tem `status_anterior`, `status_novo`, `usuario` e `data_alteracao`. Os métodos `get_status_anterior_display` e `get_status_novo_display` fornecem os rótulos. O evento inicial tem status anterior vazio.
- `historico` contém snapshots de Problema, com `history_user`, `history_date` e `history_type`, incluindo mudanças de responsável e prioridade.
- Os formulários inválidos retornam a mesma página, com `form.errors`. Renderizar erros de campo e `form.non_field_errors`.
- Usar POST, `{% csrf_token %}`, mensagens Django e autoescape. Nenhum GET grava.
- Gravação válida redireciona para `problemas:detalhe`. Não há edição genérica ou exclusão.
- Anônimo vai para login. Perfil sem permissão recebe 403. ID inexistente recebe 404.
- Responsável pelo sistema consulta somente seus sistemas; detalhe fora desse escopo também retorna 404, sem expor existência ou histórico.
- Superusuário mantém a exceção de perfil, mas continua sujeito às regras de negócio.

## Formulários e regras

| Formulário | Campos aceitos |
|---|---|
| `AbrirProblemaForm` | `titulo`, `descricao`, `incidentes` (seleção múltipla obrigatória) |
| `VincularIncidentesForm` | `incidentes` (seleção múltipla obrigatória) |
| `AtribuirProblemaForm` | `responsavel` (Desenvolvedor), `prioridade` (`BAIXA`, `MEDIA`, `ALTA`) |
| `AlterarStatusForm` | `status`, limitado ao próximo status |
| `CausaRaizForm` | `descricao`, `analise_5_porques` (textos obrigatórios) |
| `ErroConhecidoForm` (`kedb.forms`) | `sintoma`, `causa`, `solucao_contorno` (textos obrigatórios) |
| `AcaoCorretivaForm` (`acoes.forms`) | `descricao`, `prazo` (AAAA-MM-DD), `responsavel` (Desenvolvedor) |
| `AlterarStatusAcaoForm` (`acoes.forms`) | `status`, limitado ao próximo status da ação |

A abertura exige ao menos um Incidente ainda sem vínculo. O Sistema é derivado dos incidentes selecionados; todos devem ser do mesmo Sistema. O status inicial é Registrado e responsável/prioridade ficam sem atribuição. Dados extras enviados pelo cliente não controlam esses valores.

O vínculo aceita Incidentes sem vínculo ou já vinculados ao mesmo Problema, sempre do mesmo Sistema. Repetir não duplica nem cria auditoria artificial. Vincular a outro Problema, transferir e desvincular não são operações desta etapa. Incidentes vinculados não podem mudar para outro Sistema na edição comum.

O Gestor atribui responsável e prioridade juntos. Não existe restrição de atividade adicional na seleção do Desenvolvedor. O responsável pelo Problema é distinto do Responsável pelo sistema.

Sequência aprovada: **Registrado → Em investigação → Erro conhecido → Em correção → Resolvido → Encerrado**. Desenvolvedor e Gestor avançam até Resolvido, sem saltos nem reabertura. Não há restrição de avanço apenas ao Desenvolvedor atribuído, nem obrigação de atribuir antes de avançar: essas regras adicionais não foram definidas.

**Encerramento funcional:** somente Gestor (ou superusuário) pode avançar de Resolvido para Encerrado. O serviço exige pelo menos uma ação e que todas estejam Concluídas. Depois de Encerrado, novas ações e alterações de status das ações retornam erro de validação. A validação do Responsável pelo sistema (RF13) não faz parte do MVP.

## Serviços e persistência

`problemas/services.py` oferece:

- `abrir_problema(usuario=..., titulo=..., descricao=..., incidentes_ids=[...])`;
- `vincular_incidentes(usuario=..., problema_id=..., incidentes_ids=[...])`;
- `atribuir_responsavel_prioridade(usuario=..., problema_id=..., responsavel_id=..., prioridade=...)`;
- `alterar_status(usuario=..., problema_id=..., status=...)`;
- `problemas_visiveis(usuario)` para consultas com escopo e contagem;
- `registrar_causa_raiz(usuario=..., problema_id=..., descricao=..., analise_5_porques=...)` para criar/atualizar a causa única.

As operações verificam perfil também fora de HTTP, validam novamente dados e vínculos e usam transação. IDs de Problema inexistentes nos serviços lançam `Problema.DoesNotExist`; as views traduzem referências inexistentes para 404. Seleções inválidas de formulário produzem erros de validação.

PostgreSQL usa bloqueio das linhas alteradas com `select_for_update`; SQLite usa suas transações e bloqueios próprios. Não foi executada validação concorrente em PostgreSQL nesta entrega.

Auditoria é feita por django-simple-history; o serviço atribui `_history_user`. Um sinal deriva automaticamente os eventos de HistóricoStatus a partir dos snapshots de Problema. Scripts de negócio devem usar os serviços: gravações diretas via ORM não aplicam todas as permissões/transições, e `QuerySet.update`/`bulk_update` não produzem esse histórico. Não há registro de Problemas, CausaRaiz, ErroConhecido ou Ações Corretivas no admin, evitando um segundo fluxo de escrita sem essas regras.

## Verificação e integrações pendentes

Aplicar migrations com `python manage.py migrate`. Conferir backend com `python manage.py test problemas incidentes acoes kedb`; o teste de rotas não publicadas deverá ser substituído pela verificação das telas reais quando a F3 ativar o include.

CausaRaiz, registro de ErroConhecido, Ações Corretivas, auditoria e encerramento condicionado à conclusão das ações estão implementados no backend. As telas continuam com a F3. Pesquisa global na KEDB, alerta de recorrência, aprovação final de encerramento, dashboard e reabertura não fazem parte desta entrega. Ver [escopo-backend-mvp.md](escopo-backend-mvp.md).


## Views de ErroConhecido e Ações Corretivas

| Caminho completo após ativação | Nome da URL | Métodos | Perfil | Template e contexto |
|---|---|---|---|---|
| `/kedb/problema/<problema_pk>/registrar/` | `kedb:registrar` | GET/POST | Desenvolvedor | `kedb/form.html`: `form`, `problema`, `erro_conhecido` (ou `None`), `titulo` |
| `/acoes/problema/<problema_pk>/nova/` | `acoes:cadastrar` | GET/POST | Desenvolvedor e Gestor | `acoes/form.html`: `form`, `problema`, `titulo` |
| `/acoes/<pk>/status/` | `acoes:alterar_status` | GET/POST | Desenvolvedor | `acoes/form.html`: `form`, `problema`, `acao`, `titulo` |

Todos redirecionam para `problemas:detalhe` após sucesso. Os IDs de Problema vêm da URL; campos extras enviados no POST não transferem o vínculo nem escolhem o autor da auditoria. O GET de CausaRaiz/ErroConhecido preenche o formulário se já existe o registro. O POST cadastra na primeira vez e atualiza o mesmo registro nas seguintes.

A análise dos 5 Porquês é texto livre obrigatório. Não há Ishikawa, exigência de cinco campos separados, publicação automática de erro ou alteração automática de status do Problema. A pesquisa global da KEDB (RF18) não foi implementada.

A ação inicia Aberta. Qualquer Desenvolvedor, inclusive diferente do responsável atribuído, pode avançar por Aberta → Em andamento → Concluída. O Gestor pode criar, mas não atualizar status de ação, salvo se for superusuário. O prazo aceita datas válidas sem restrições adicionais de passado/futuro. Não há edição de descrição/prazo/responsável, exclusão ou retorno de status.

Serviços adicionais:

- `kedb.services.registrar_erro_conhecido(usuario=..., problema_id=..., sintoma=..., causa=..., solucao_contorno=...)`.
- `acoes.services.criar_acao(usuario=..., problema_id=..., descricao=..., prazo=..., responsavel_id=...)`.
- `acoes.services.alterar_status_acao(usuario=..., acao_id=..., status=...)`.

## Contexto ampliado do detalhe de Problema

Além dos contextos anteriores, `problemas:detalhe` expõe:

| Chave | Conteúdo |
|---|---|
| `causa_raiz` | Objeto CausaRaiz ou `None` |
| `erro_conhecido` | Objeto ErroConhecido ou `None` |
| `acoes` | Ações do Problema, ordenadas por prazo/ID, com responsável carregado |
| `historico_causa_raiz` | Snapshots de CausaRaiz desse Problema |
| `historico_erro_conhecido` | Snapshots de ErroConhecido desse Problema |
| `historico_acoes` | Snapshots de todas as Ações Corretivas desse Problema |
| `linha_do_tempo` | Lista cronológica de eventos com `entidade`, `registro`, `data`, `usuario` |

Em `linha_do_tempo`, `entidade` é Problema, CausaRaiz, ErroConhecido ou AçãoCorretiva. `registro` é o snapshot histórico com os campos daquela entidade e `history_type` (`+` criação, `~` alteração). O registro da ação inclui `id`, `status`, `descricao`, `prazo` e `responsavel_id`; o evento identifica o autor da alteração, que não necessariamente é o responsável atribuído. Registros técnicos antigos sem autor podem ter `usuario=None`.

Renderizar conteúdo textual com autoescape. O queryset de Problemas é autorizado antes de carregar todos esses contextos; o Responsável pelo sistema não recebe dados nem histórico de outros sistemas.

## Roteiro de aceite após integrar as telas

1. Suporte registra Incidente e abre Problema a partir dele.
2. Gestor atribui Desenvolvedor e prioridade.
3. Desenvolvedor avança para Em investigação, registra CausaRaiz e ErroConhecido.
4. Desenvolvedor ou Gestor cria ação com responsável e prazo.
5. Desenvolvedor avança o Problema para Erro conhecido/Em correção e a ação para Em andamento/Concluída.
6. Desenvolvedor ou Gestor avança o Problema para Resolvido; Gestor encerra.
7. Conferir que a tentativa de encerrar sem ações ou com alguma pendente falha, e que não se criam ações após encerramento.
8. Conferir autores, valores e datas na linha do tempo e o escopo do Responsável pelo sistema.

O teste `BackendMvpTests.test_fluxo_completo_http_incidente_investigacao_correcao_encerramento` já exercita esse caminho no servidor com templates de teste. Ele não substitui o aceite visual e de navegação da F3/F6.

