"""
Configura o repositório no GitHub (rodar uma única vez, pela F1).

Pré-requisitos: GitHub CLI instalado e autenticado (`gh auth status`), e o
repositório git local com as branches `main` e `develop`.

    python scripts/configurar_github.py

O que faz (pulando o que já existir, sem apagar nada):
1. cria o repositório privado e envia `main` e `develop`;
2. define `develop` como branch padrão;
3. cria labels, milestones e as issues do plano de tarefas;
4. tenta proteger a branch `main` (planos gratuitos podem não permitir em repositório privado).
"""

import json
import subprocess
import sys

NOME_REPO = "governanca-ti-grupo7-gestao-problemas"
DESCRICAO = (
    "Sistema de Gestão de Problemas (ITIL 4 / COBIT 2019) - Grupo 7 - Governança de TI - UNINASSAU"
)

LABELS = {
    "F1": ("1F3A5F", "Função 1 - Líder técnico e arquiteto"),
    "F2": ("2E75B6", "Função 2 - Back-end e modelo de dados"),
    "F3": ("0F9D8A", "Função 3 - Front-end e interface"),
    "F4": ("C77D0A", "Função 4 - Requisitos e documentação"),
    "F5": ("7B4FA0", "Função 5 - Governança"),
    "F6": ("B23A48", "Função 6 - Qualidade e entregas"),
    "todos": ("5A6472", "Tarefa de todo o grupo"),
    "entrega-1": ("BFD4F2", "Entrega 1 - Planejamento"),
    "entrega-2": ("A2C4EC", "Entrega 2 - MVP"),
    "entrega-3": ("7FA8DB", "Entrega 3 - Versão final"),
    "apresentacao": ("FBCA04", "Apresentação"),
    "bloqueado": ("000000", "Tarefa impedida por outra"),
    "bug": ("D73A4A", "Algo não funciona como deveria"),
}

# milestone: (prazo, label da entrega)
MILESTONES = {
    "Entrega 1 - Planejamento": ("2026-10-30", "entrega-1"),
    "Entrega 2 - MVP": ("2026-11-13", "entrega-2"),
    "Entrega 3 - Versão final": ("2026-11-23", "entrega-3"),
    "Apresentação": ("2026-11-27", "apresentacao"),
}

# (função, prazo interno, título) por milestone. "Todos" usa o label `todos`.
TAREFAS = {
    "Entrega 1 - Planejamento": [
        (
            "F6",
            "20/10",
            "Criar o esqueleto do documento com a estrutura prevista e o quadro de nomes padronizados",
        ),
        ("F1", "21/10", "Fechar a stack com o grupo e registrar na seção de tecnologias"),
        (
            "F1",
            "22/10",
            "Criar o repositório Git, a estrutura de pastas, o README inicial e o esboço da arquitetura",
        ),
        ("F4", "22/10", "Redigir a descrição do problema, o público-alvo e os perfis de usuário"),
        ("F2", "23/10", "Rascunhar o modelo de dados: entidades e atributos"),
        ("F4", "23/10", "Listar as funcionalidades por módulo, com o MVP destacado"),
        (
            "F4",
            "26/10",
            "Produzir os diagramas em Mermaid: fluxo, entidade-relacionamento e casos de uso (opcional)",
        ),
        (
            "F5",
            "26/10",
            "Redigir a seção de conceitos de governança, com a tabela conceito → funcionalidade",
        ),
        ("F5", "26/10", "Montar a matriz RACI com os 4 perfis de usuário"),
        ("F3", "26/10", "Fazer o protótipo das telas principais"),
        ("F6", "27/10", "Consolidar os textos e checar a consistência de nomes"),
        ("Todos", "28/10", "Revisão cruzada"),
        ("F6", "29/10", "Enviar a Entrega 1"),
    ],
    "Entrega 2 - MVP": [
        ("F6", "03/11", "Escrever o plano de testes e os casos de teste do fluxo completo"),
        ("F1", "03/11", "Login com os 4 perfis e projeto rodando em ambiente comum"),
        ("F2", "04/11", "Implementar Incidentes: cadastro, edição e listagem"),
        ("F3", "04/11", "Criar as telas base e a navegação por perfil"),
        ("F1", "06/11", "Implementar Problemas: criação a partir de incidente e ciclo de status"),
        ("F2", "06/11", "Implementar o vínculo incidente-problema e a contagem de ocorrências"),
        ("F1", "09/11", "Implementar histórico e auditoria (quem, o quê, quando)"),
        ("F2", "09/11", "Implementar causa raiz simples (5 Porquês) e ações corretivas"),
        ("F3", "09/11", "Integrar as telas de incidentes e problemas às views"),
        ("F3", "10/11", "Criar as telas de causa raiz, ações corretivas e histórico"),
        ("F6", "10/11", "Preparar os dados de demonstração com incidentes recorrentes"),
        ("F4", "10/11", "Atualizar diagramas e funcionalidades com o que foi implementado"),
        ("Todos", "11/11", "Integração e correção de bugs"),
        ("F6", "11/11", "Rodar os testes de ponta a ponta e listar bugs"),
        ("F5", "11/11", 'Rascunho de "conceitos aplicados" com prints do MVP'),
        ("Todos", "12/11", "Congelar o MVP e enviar a Entrega 2"),
        ("F1", "28/10", "Criar o banco PostgreSQL e o serviço no Render"),
    ],
    "Entrega 3 - Versão final": [
        ("F2", "17/11", "Implementar a KEDB com busca por palavra-chave"),
        (
            "F1",
            "17/11",
            "Implementar os indicadores (problemas abertos, incidentes recorrentes por sistema, tempo médio de resolução, % de ações no prazo, reincidência)",
        ),
        (
            "F2",
            "18/11",
            "Implementar o alerta de recorrência (3 ou mais incidentes semelhantes em 30 dias)",
        ),
        ("F3", "18/11", "Montar o dashboard completo"),
        (
            "F1",
            "19/11",
            "Implementar aprovação de encerramento pelo gestor e validação pelo responsável; ajustes finais e implantação",
        ),
        ("F3", "19/11", "Refinamentos de interface"),
        ("F6", "19/11", "Testes finais e de regressão"),
        (
            "F4",
            "19/11",
            "Fechar a documentação (funcionalidades, diagramas finais, tecnologias, cronograma, conclusão)",
        ),
        ("F5", "19/11", "Fechar a seção de governança e verificar as referências"),
        ("F6", "20/11", "Revisão geral e formatação do documento"),
        ("Todos", "20/11", "Congelar o código"),
        ("F6", "22/11", "Enviar a Entrega 3"),
    ],
    "Apresentação": [
        ("F6", "24/11", "Montar slides e roteiro com tempo de fala"),
        ("F1", "25/11", "Gravar o vídeo de reserva da demonstração (com a F3)"),
        ("Todos", "25/11", "Ensaio completo, cronometrado (25 e 26/11)"),
        (
            "F1",
            "25/11",
            "Garantir o plano B da apresentação (Docker local) e conferir o banco do Render antes de 27/11",
        ),
    ],
}

# Observações extras no corpo de issues específicas.
OBSERVACOES = {
    "Criar o banco PostgreSQL e o serviço no Render": (
        "Não criar antes de 28/10: o banco gratuito do Render expira 30 dias após a criação. "
        "Usar o blueprint `render.yaml` e seguir a seção de deploy do README."
    ),
}


def gh(*args, entrada=None, checar=True):
    """Executa o GitHub CLI e devolve a saída (texto)."""
    resultado = subprocess.run(
        ["gh", *args], input=entrada, capture_output=True, text=True, encoding="utf-8"
    )
    if checar and resultado.returncode != 0:
        sys.exit(f"Erro em `gh {' '.join(args)}`:\n{resultado.stderr}")
    return resultado


def git(*args):
    subprocess.run(["git", *args], check=True)


def main():
    # Evita erro de acentuação no terminal do Windows.
    sys.stdout.reconfigure(encoding="utf-8")
    usuario = gh("api", "user", "--jq", ".login").stdout.strip()
    repo = f"{usuario}/{NOME_REPO}"
    print(f"Conta autenticada: {usuario}")

    # 1. Repositório
    if gh("repo", "view", repo, checar=False).returncode == 0:
        print(f"Repositório {repo} já existe.")
    else:
        gh(
            "repo",
            "create",
            NOME_REPO,
            "--private",
            "--description",
            DESCRICAO,
            "--source",
            ".",
            "--remote",
            "origin",
        )
        print(f"Repositório {repo} criado.")
    git("push", "-u", "origin", "main")
    git("push", "-u", "origin", "develop")

    # 2. Branch padrão
    gh("repo", "edit", repo, "--default-branch", "develop")
    print("Branch padrão: develop")

    # 3. Labels (não altera os que já existem)
    existentes = {
        item["name"]
        for item in json.loads(
            gh("label", "list", "-R", repo, "--limit", "200", "--json", "name").stdout
        )
    }
    for nome, (cor, descricao) in LABELS.items():
        if nome in existentes:
            print(f"Label {nome} já existe.")
            continue
        gh("label", "create", nome, "-R", repo, "--color", cor, "--description", descricao)
        print(f"Label {nome} criado.")

    # 4. Milestones
    atuais = {
        m["title"]
        for m in json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100").stdout)
    }
    for titulo, (prazo, _) in MILESTONES.items():
        if titulo in atuais:
            print(f"Milestone {titulo} já existe.")
            continue
        # Meio-dia UTC evita que o fuso mostre o dia anterior.
        gh(
            "api",
            f"repos/{repo}/milestones",
            "-f",
            f"title={titulo}",
            "-f",
            f"due_on={prazo}T12:00:00Z",
        )
        print(f"Milestone {titulo} criado.")

    # 5. Issues (pula títulos que já existem)
    titulos = {
        i["title"]
        for i in json.loads(
            gh(
                "issue", "list", "-R", repo, "--state", "all", "--limit", "500", "--json", "title"
            ).stdout
        )
    }
    for milestone, tarefas in TAREFAS.items():
        prazo_ms, label_entrega = MILESTONES[milestone]
        for funcao, prazo, titulo in tarefas:
            label_funcao = "todos" if funcao == "Todos" else funcao
            titulo_issue = f"[{funcao}] {titulo}"
            if titulo_issue in titulos:
                print(f"Issue já existe: {titulo_issue}")
                continue
            corpo = (
                f"**Função responsável:** {funcao}\n"
                f"**Prazo interno:** {prazo}/2026\n"
                f"**Milestone:** {milestone} (prazo oficial {prazo_ms[8:]}/{prazo_ms[5:7]}/2026)\n"
            )
            if titulo in OBSERVACOES:
                corpo += f"\n{OBSERVACOES[titulo]}\n"
            corpo += "\nNomes padronizados: `docs/convencoes.md`.\n"
            gh(
                "issue",
                "create",
                "-R",
                repo,
                "--title",
                titulo_issue,
                "--body",
                corpo,
                "--label",
                f"{label_funcao},{label_entrega}",
                "--milestone",
                milestone,
            )
            print(f"Issue criada: {titulo_issue}")

    # 6. Proteção da main (exige PR com 1 aprovação e CI verde)
    protecao = {
        "required_status_checks": {"strict": False, "contexts": ["testes"]},
        "enforce_admins": False,
        "required_pull_request_reviews": {"required_approving_review_count": 1},
        "restrictions": None,
    }
    resultado = gh(
        "api",
        "-X",
        "PUT",
        f"repos/{repo}/branches/main/protection",
        "--input",
        "-",
        entrada=json.dumps(protecao),
        checar=False,
    )
    if resultado.returncode == 0:
        print("Branch main protegida.")
    else:
        print(
            "AVISO: não foi possível proteger a main (o plano gratuito pode não permitir "
            f"em repositório privado):\n{resultado.stderr.strip()}"
        )

    print(f"\nPronto: https://github.com/{repo}")


if __name__ == "__main__":
    main()
