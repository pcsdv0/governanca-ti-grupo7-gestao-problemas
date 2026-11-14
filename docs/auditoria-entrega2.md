# Auditoria da Entrega 2: planejamento (Entrega 1) × sistema

Comparação feita em 13/11/2026 entre o documento de planejamento entregue na Entrega 1 e o código deste repositório.

## Requisitos do MVP (Tabela 3, Seção 4.1)

| RF | Funcionalidade | Antes desta auditoria | Agora |
|---|---|---|---|
| RF01 | Login/logout com controle por perfil | Pronto | Pronto, com navegação por perfil |
| RF02 | Cadastro/edição de Usuários e perfil (Gestor de TI) | **Só pelo admin do Django** | Telas em Cadastros → Usuários |
| RF04 | Sistemas | Pronto | Pronto |
| RF05/RF06 | Registrar e listar Incidentes com filtros | Pronto | Pronto, com código INC e coluna Problema |
| RF07/RF09 | Vincular Incidentes e abrir Problema | Backend sem tela | Tela: seleção na lista e "Vincular Incidentes" no Problema |
| RF10/RF11/RF12 | Status, atribuição e detalhe do Problema | Backend sem tela | Detalhe com barra de status, abas e botões por perfil |
| RF15/RF17 | CausaRaiz e ErroConhecido | Backend sem tela | Abas e formulários |
| RF20/RF21 | Ações Corretivas | Backend sem tela | Aba no Problema e lista global (Figura 6) |
| RF23/RF24 | Histórico e consulta | Backend sem tela | Aba Histórico (status e linha do tempo) |

## Demais seções

| Seção do planejamento | Situação | Observação |
|---|---|---|
| 1 – Nomes padronizados | Consistente | Protegidos por testes contra `docs/convencoes.md`. |
| 2 – Tecnologias | Consistente | Chart.js entra com o dashboard (versão final). |
| 4.4 – Requisitos não funcionais | Consistente | Telas principais a até três cliques pela barra lateral. |
| 5 – Modelo de dados | Consistente | Atributos idênticos; CausaRaiz e ErroConhecido são 1:1 com Problema (definição da implementação). |
| 6.1 – Fluxo (Figura 1) | **Atualizar diagrama** | A figura tem um atalho "correção definitiva imediata" que pula Erro conhecido; o sistema segue a sequência sem saltos (decisão da F2 de 09/11). |
| 7.7 – Matriz RACI | Consistente | Validação do Responsável pelo sistema é RF13 (versão final). |
| 8 – Protótipos | Consistente | Diferenças menores: vínculo a Problema existente fica no detalhe do Problema; período por datas De/Até; sem o seletor "Perfil simulado" dos protótipos. |
| Dados de demonstração (tarefa F6) | Feito | `python manage.py carregar_demo`. |

## Pendências para a Entrega 3

RF13, RF18, RF25, RF26 e RF29; atualização da Figura 1 e do diagrama ER (cardinalidade 1:1); deploy no Render; consolidação da documentação.
