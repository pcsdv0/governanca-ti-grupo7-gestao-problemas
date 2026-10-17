# Como contribuir

## Regra de ouro

**Nomes padronizados vêm de [docs/convencoes.md](docs/convencoes.md).** Perfis, status e entidades devem ser escritos exatamente como lá, no código, nas telas, nos diagramas e no documento. Precisa mudar um nome? Mude primeiro o `convencoes.md` e avise o grupo.

## Branches

| Branch | Uso |
|---|---|
| `main` | Protegida. Só recebe o que vai ser entregue (Entregas 1, 2, 3 e apresentação), via PR de `develop`. |
| `develop` | Integração. Branch padrão do repositório; todo trabalho entra aqui por PR. |
| `feat/<funcao>-<assunto>` | Trabalho do dia a dia. Ex.: `feat/f2-incidentes`, `feat/f3-tela-login`. |

Para correções use `fix/<funcao>-<assunto>` e para documentação `docs/<funcao>-<assunto>`.

## Passo a passo

```bash
git checkout develop
git pull
git checkout -b feat/f2-incidentes
# ... trabalhe ...
ruff check . && ruff format . && python manage.py test
git add .
git commit -m "feat(incidentes): cadastro e listagem de incidentes"
git push -u origin feat/f2-incidentes
```

Depois abra um Pull Request **para `develop`** no GitHub, preencha o checklist e peça revisão.

## Commits (Conventional Commits, em português)

Formato: `tipo(escopo): descrição no imperativo ou no presente, em minúsculas`.

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(problemas): criar problema a partir de incidente` |
| `fix` | Correção de bug | `fix(contas): corrigir redirecionamento após login` |
| `docs` | Só documentação | `docs: atualizar matriz RACI` |
| `test` | Só testes | `test(acoes): testar conclusão de ação corretiva` |
| `refactor` | Mudança sem alterar comportamento | `refactor(incidentes): extrair formulário` |
| `style` | Formatação | `style: aplicar ruff format` |
| `chore` | Configuração, dependências, CI | `chore: atualizar django para 5.2.19` |

Commits pequenos, um assunto por commit.

## Pull Requests

- Todo PR vai para `develop` e precisa da **revisão de pelo menos 1 pessoa** antes do merge.
- O CI (lint, checagens do Django, migrations e testes) precisa estar verde.
- Referencie a issue (`Fecha #12`) e anexe prints se mexeu em tela.
- Mexeu em modelos? Rode `python manage.py makemigrations` e commite a migration junto.

## Issues

Cada tarefa do plano é uma issue `[F#] título`, com o label da função, o label da entrega e o milestone. Use os modelos "Tarefa" e "Bug" ao abrir novas issues.
