# Roteiro de demonstração da versão final (cerca de 6 minutos)

Pré-requisito: `python manage.py migrate` e `python manage.py carregar_demo` (no Render, `CARREGAR_DEMO=True`). Senha de todos os usuários: `demo1234`. No Render gratuito, abra o site alguns minutos antes, porque o primeiro acesso depois da hibernação demora cerca de 1 minuto.

| Passo | Perfil (login) | O que fazer | O que mostrar |
|---|---|---|---|
| 1 | Suporte (`suporte`) | Em Incidentes, filtrar o Portal do Aluno e abrir um Problema com os Incidentes "Frequência não atualiza" e "Erro ao baixar boleto". | Problema criado como Registrado, com 2 ocorrências (RF09, RF12). |
| 2 | Suporte (`suporte`) | Em Base de erros conhecidos, pesquisar "conexões". | Solução de contorno reaproveitável do Problema do Sistema de Matrícula (RF18). |
| 3 | Gestor de TI (`gestor`) | Atribuir Carla Mendes como responsável, com prioridade Alta, e avançar para Em investigação. | Priorização e ciclo de status (RF10, RF11). |
| 4 | Desenvolvedor (`dev`) | Registrar a causa raiz (5 Porquês) e o erro conhecido; avançar para Erro conhecido e Em correção; criar uma ação corretiva, levá-la até Concluída e avançar para Resolvido. | RF15, RF17, RF20 e RF21; o encerramento não aparece para o Desenvolvedor. |
| 5 | Responsável pelo sistema (`responsavel`) | No Problema resolvido, clicar em Validar solução. | Validação da solução (RF13). Se rejeitar, o Problema volta para Em investigação. |
| 6 | Gestor de TI (`gestor`) | Encerrar o Problema e abrir o Histórico de alterações. | Encerramento só depois da validação; autor e data de cada etapa (RF23, RF24). |
| 7 | Gestor de TI (`gestor`) | Abrir o Dashboard. | Indicadores (RF25, RF26) e alerta de recorrência do Sistema de Matrícula, com 5 Incidentes em 30 dias (RF29). |
| 8 | Responsável pelo sistema (`responsavel2`) | Abrir Incidentes e Problemas. | Escopo por Sistema: só aparece o E-mail institucional. |

Plano B: `docker compose up --build` e, em outro terminal, `docker compose exec web python manage.py carregar_demo`.
