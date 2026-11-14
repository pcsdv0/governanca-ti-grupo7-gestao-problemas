# Roteiro de demonstração do MVP (cerca de 5 minutos)

Pré-requisito: `python manage.py migrate` e `python manage.py carregar_demo`. Senha de todos os usuários: `demo1234`.

| Passo | Perfil (login) | O que fazer | O que mostrar |
|---|---|---|---|
| 1 | Suporte (`suporte`) | Em **Incidentes**, marcar **INC-011** e **INC-012** (Portal do Aluno) e clicar em **Abrir Problema com os selecionados**. Preencher título e descrição e salvar. | Problema criado como **Registrado**, com 2 ocorrências (RF09, RF12). |
| 2 | Gestor de TI (`gestor`) | No novo Problema, clicar em **Atribuir responsável e prioridade** (Carla Mendes, Alta). Depois, **Avançar para “Em investigação”**. | Atribuição e avanço de status (RF10, RF11). |
| 3 | Desenvolvedor (`dev`) | Registrar a **CausaRaiz** (5 Porquês) e o **ErroConhecido**. Avançar para **Erro conhecido** e **Em correção**. Criar uma **AçãoCorretiva** e marcá-la como **Em andamento** e **Concluída**. Avançar para **Resolvido**. | RF15, RF17, RF20, RF21; o botão de encerrar não aparece para o Desenvolvedor. |
| 4 | Gestor de TI (`gestor`) | **Avançar para “Encerrado”** e abrir a aba **Histórico**. | Encerramento exclusivo do Gestor e linha do tempo com autor, perfil e data (RF23, RF24). |
| 5 | Responsável pelo sistema (`responsavel2`) | Abrir Incidentes, Problemas e Ações corretivas. | Escopo por Sistema: só aparece o E-mail institucional. |

Casos já prontos para mostrar: **PRB-001** (Sistema de Matrícula, em correção, 5 ocorrências, 3 ações) e **PRB-003** (E-mail institucional, ciclo completo até Encerrado).

Plano B: `docker compose up --build` e, em outro terminal, `docker compose exec web python manage.py carregar_demo`.
