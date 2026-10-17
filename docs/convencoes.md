# Convenções de nomes (fonte da verdade)

Este arquivo é a **fonte da verdade** para todos os nomes usados no projeto: texto da documentação, diagramas, banco de dados e telas. Se um nome precisar mudar, mude **primeiro aqui**, avise o grupo e depois atualize código, diagramas e documento.

- **Código**: identificador usado no Python e gravado no banco.
- **Rótulo**: texto exibido nas telas, no documento e nos diagramas.

## Perfis de usuário

Definidos em `contas/models.py` (classe `Perfil`).

| Código | Rótulo |
|---|---|
| `SUPORTE` | Suporte |
| `DESENVOLVEDOR` | Desenvolvedor |
| `GESTOR_TI` | Gestor de TI |
| `RESPONSAVEL_SISTEMA` | Responsável pelo sistema |

## Status do Problema

Definidos em `problemas/constantes.py` (classe `StatusProblema`).

| Ordem | Código | Rótulo |
|---|---|---|
| 1 | `REGISTRADO` | Registrado |
| 2 | `EM_INVESTIGACAO` | Em investigação |
| 3 | `ERRO_CONHECIDO` | Erro conhecido |
| 4 | `EM_CORRECAO` | Em correção |
| 5 | `RESOLVIDO` | Resolvido |
| 6 | `ENCERRADO` | Encerrado |

## Status da Ação corretiva

Definidos em `acoes/constantes.py` (classe `StatusAcaoCorretiva`).

| Código | Rótulo |
|---|---|
| `ABERTA` | Aberta |
| `EM_ANDAMENTO` | Em andamento |
| `CONCLUIDA` | Concluída |

## Entidades

| Nome no documento e nas telas | Nome no código (classe) | App |
|---|---|---|
| Usuário | `Usuario` | `contas` |
| Sistema | `Sistema` | `sistemas` |
| Incidente | `Incidente` | `incidentes` |
| Problema | `Problema` | `problemas` |
| CausaRaiz | `CausaRaiz` | `problemas` |
| ErroConhecido | `ErroConhecido` | `kedb` |
| AçãoCorretiva | `AcaoCorretiva` | `acoes` |
| HistóricoStatus | `HistoricoStatus` | `problemas` |

No código os nomes de classe não levam acento (`AcaoCorretiva`, `HistoricoStatus`); nas telas e no documento usa-se a forma acentuada.

> A coluna "App" indica onde cada modelo deve ficar, de acordo com a estrutura de pastas. O modelo de dados completo (atributos) será proposto pela F2 até 23/10 em `docs/modelo-de-dados.md`.

## Relação central

**Um Problema se relaciona com vários Incidentes.** Cada Incidente pode estar vinculado a no máximo um Problema; vários incidentes com o mesmo erro apontam para o mesmo Problema, e é isso que permite contar ocorrências e identificar recorrência.

## Incidente x Problema

| | Incidente | Problema |
|---|---|---|
| O que é | Interrupção ou degradação de um serviço | Causa raiz desconhecida de um ou mais incidentes |
| Objetivo | Restaurar rápido, com solução de contorno | Investigar, corrigir de forma definitiva e evitar reincidência |

## Testes que protegem estes nomes

Os testes `contas/tests.py`, `problemas/tests.py` e `acoes/tests.py` comparam as choices do código com as tabelas acima. Se alguém alterar um nome só no código, o CI falha.
