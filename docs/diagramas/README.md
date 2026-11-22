# Diagramas da versão final

Código-fonte em Mermaid e imagem exportada de cada diagrama da documentação final (Seção 6).

| Arquivo | Diagrama | Figura |
|---|---|---|
| `fluxo.mmd` | Fluxo do processo, em três etapas: incidentes (DSS02), investigação (DSS03) e correção/validação/encerramento | Figura 1 |
| `er.mmd` | Entidade-relacionamento, com `validado_por_id` (RF13) e CausaRaiz/ErroConhecido 1:1 | Figura 2 |
| `casos.mmd` | Casos de uso dos quatro perfis, com RF13, RF18, RF25, RF26 e RF29 | Figura 3 |

Mudanças em relação ao planejamento: o fluxo não tem mais o atalho que pulava "Erro conhecido" (o status avança um passo por vez), e a rejeição da solução pelo Responsável pelo sistema devolve o Problema para "Em investigação", como o sistema faz.

## Como editar e exportar

- **Sem instalar nada:** cole o conteúdo do `.mmd` em <https://mermaid.live>, ajuste e baixe o PNG (Actions → PNG).
- **Pela linha de comando:** `npx -p @mermaid-js/mermaid-cli mmdc -i fluxo.mmd -o fluxo.png -b white -s 2`.

Ao alterar um diagrama, atualize o `.mmd` e o `.png` no mesmo commit.
