# Escopo do backend F2 no MVP

## Fonte e objetivo

Conferência em 09/11/2026 do [Planejamento ajustado da AV2](https://drive.google.com/file/d/1lEc7vGRQy9dLvFSo6MaVAGorN_kbnqKA/view), seções **4 / Tabela 3**, **4.1**, **4.2**, **5 / Tabela 4** e **6 / 6.2**. O pedido desta etapa é concluir o backend atribuído à F2 no MVP, incluindo o backend de Problemas que a F2 assumiu na conversa. As telas continuam com a F3.

A documentação anterior do repositório agrupava todo o módulo KEDB na versão final. A fonte acadêmica diferencia **RF17 (criação de ErroConhecido, MVP)** de **RF18 (consulta e pesquisa na KEDB, versão final)**. RF17 faz parte desta entrega; RF18 e RF29 não fazem parte do fechamento do MVP.

## Requisitos incluídos

| Requisito | Backend abrangido |
|---|---|
| RF04 | Cadastro, edição e listagem de Sistemas |
| RF05 / RF06 | Incidentes e filtros por sistema, período e vínculo |
| RF07 | Vínculo de incidentes a Problema e contagem |
| RF09–RF12 | Abertura de Problema, ciclo de status, atribuição e detalhe |
| RF15 | CausaRaiz com descrição e análise dos 5 Porquês em texto |
| RF17 | ErroConhecido com sintoma, causa e solução de contorno |
| RF20 | AçãoCorretiva com descrição, responsável, prazo e Problema |
| RF21 | Atualização do status da AçãoCorretiva pelo Desenvolvedor |
| RF23 / RF24 | Auditoria e consulta ao histórico no detalhe de Problema |

RF01/RF02 são da base de Acesso e Usuários (F1). A presente entrega não declara concluídas tarefas de outras funções nem o MVP completo na interface.

## Permissões definidas pelo planejamento

- **RF15 e RF17:** Desenvolvedor.
- **RF20:** Desenvolvedor e Gestor de TI.
- **RF21:** Desenvolvedor.
- **RF24:** todos os perfis, preservando o escopo dos sistemas do Responsável pelo sistema.
- **Encerramento no MVP:** Gestor de TI, após conclusão das Ações Corretivas. A validação do Responsável pelo sistema é RF13, da versão final.
- A exceção existente de superusuário é preservada, sem dispensar validações de negócio.

## Estrutura confirmada

- `problemas.CausaRaiz`: `id`, `descricao`, `analise_5_porques`, `problema`.
- `kedb.ErroConhecido`: `id`, `sintoma`, `causa`, `solucao_contorno`, `problema`.
- `acoes.AcaoCorretiva`: `id`, `descricao`, `prazo`, `status`, `problema`, `responsavel`.
- Todos seguem a auditoria com `HistoricalRecords`.
- `HistoricoStatus` continua sendo a entidade de eventos de Problema; o histórico de Ações Corretivas é mantido pelo django-simple-history, conforme seção 6.2. Não é necessário criar uma entidade adicional nem alterar o significado da FK existente.

## Decisões complementares

Confirmadas pela F2 em 09/11/2026 e implementadas:

- Um registro de CausaRaiz e um de ErroConhecido por Problema, cadastráveis e atualizáveis por qualquer Desenvolvedor; sem exclusão e com auditoria. Não alteram automaticamente o status do Problema.
- Responsável pela ação com perfil Desenvolvedor; prazo como data; status inicial Aberta. Qualquer Desenvolvedor avança sequencialmente até Concluída, sem saltos ou retornos. Edição dos demais campos fora desta etapa.
- Encerramento exige pelo menos uma ação e todas Concluídas; após Encerrado, novas ações e alterações de status das ações são bloqueadas.
- A exceção de superusuário mantém todas as validações de negócio.

O backend dos requisitos incluídos acima está implementado. As telas de Problemas/CausaRaiz, ErroConhecido e Ações Corretivas permanecem com a F3. O contrato de integração está em [integracao-problemas-f3.md](integracao-problemas-f3.md); os testes do fluxo completo estão em `problemas/test_mvp.py`.

## Fora desta entrega

RF13 (validação final de encerramento), RF18 (pesquisa na KEDB), RF25/RF26 (dashboard/indicadores) e RF29 (alerta de recorrência) são da versão final. RF14 (reabertura), RF16 (Ishikawa), RF19 (tags), RF22 (alertas de atraso) e notificações/exportações são futuros. Não serão criados API REST, exclusão, deploy, push ou PR nesta tarefa.
