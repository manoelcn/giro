---
name: git-branch-creator
description: Criador inteligente de branches Git. Analisa o repositório (git status, git diff, histórico de branches e CONTRIBUTING.md), identifica automaticamente a estratégia de branching do projeto (Git Flow, GitHub Flow, Trunk-Based ou padrão customizado) e cria uma branch semântica a partir da branch base correta. Use sempre que o usuário pedir para criar uma branch, abrir uma branch para as alterações atuais ("criar branch", "nova branch") ou perguntar qual tipo/nome de branch usar. Não use para fazer commits, push, merge ou rebase.
---
# Criador Inteligente de Branches Git

Esta skill analisa o estado atual do repositório (`git status`, `git diff`), detecta a convenção de branches usada no projeto e cria uma branch com nome semântico a partir da branch base adequada, sem alterar o histórico nem realizar commits ou push.

## Quando Usar

- Quando o usuário pedir para criar ou abrir uma branch para o trabalho atual ou para uma nova tarefa.
- Quando o usuário perguntar qual tipo de branch (ex.: `feature/`, `fix/`, `hotfix/`, `chore/`, `release/`) ou nome deve usar.
- Quando o usuário tiver alterações locais não commitadas e precisar movê-las para uma branch apropriada.

## Fluxo de Execução

1. **Detecte o padrão e as branches do repositório:**
   - Leia o `CONTRIBUTING.md` (ou documentação equivalente) e inspecione as branches locais e remotas (`git branch -a`) para descobrir o modelo adotado pelo projeto:
     - **Com `develop`:** Segue o modelo **Git Flow** (`feature/`, `release-` ou `release/`, `hotfix/`).
     - **Apenas `main` ou `master`:** Segue **GitHub Flow / Trunk-Based** (`feat/` ou `feature/`, `fix/` ou `bugfix/`, `hotfix/`, `chore/`, `docs/`, `refactor/`).
     - **Padrão próprio do repositório:** Se o projeto já segue um padrão específico (ex.: `feat/TICKET-123-descricao`, idioma inglês ou português), respeite o padrão existente.
   - Identifique a branch de produção (`main` ou `master`):
     ```bash
     git branch --list main master
     git branch -r --list 'origin/main' 'origin/master'
     ```
     Se existirem ambas (`main` e `master`) ou nenhuma branch base clara, pergunte ao usuário qual deve ser usada como origem antes de criar.

2. **Analise as alterações ou o contexto da tarefa:**
   - Execute `git status` para listar arquivos modificados, adicionados ou não rastreados.
   - Execute `git diff` e `git diff --cached` para entender a natureza das mudanças. Caso não haja alterações no working tree, baseie-se na descrição da tarefa fornecida pelo usuário (ou avise que não há alterações locais caso nenhum contexto tenha sido informado).

3. **Classifique a mudança e defina a branch de origem:**
   - **Novas funcionalidades / melhorias (`feature/` ou `feat/`):** Origem em `develop` (se existir) ou `<producao>` (`main`/`master`).
   - **Correções de bugs não críticos (`fix/` ou `bugfix/`):** Origem em `develop` (se existir) ou `<producao>`.
   - **Correções críticas em produção (`hotfix/` ou `hotfix-`):** Origem sempre em `<producao>` (`main`/`master`).
   - **Preparação de versão (`release/` ou `release-X.Y.Z`):** Origem em `develop` (quando aplicável).
   - **Manutenção, testes, docs ou refatoração (`chore/`, `docs/`, `refactor/`, `test/`):** Origem em `develop` (se existir) ou `<producao>`, quando o repositório utilizar prefixos estilo Conventional Commits.

4. **Gere o nome da branch:**
   - **Prefixo:** Sempre em inglês e minúsculo (`feature/`, `feat/`, `fix/`, `hotfix/`, `chore/`, `docs/`, `refactor/`, `release/`), conforme a convenção detectada no repositório.
   - **Descrição:** Em `kebab-case`, minúsculo, sem acentos, cedilha ou caracteres especiais (ex.: `feature/autenticacao-de-usuario` ou `fix/calculo-de-multa`). Use o mesmo idioma predominante nas branches do repositório (português brasileiro por padrão caso não haja histórico definido).
   - **Ticket / Issue:** Inclua o identificador se informado pelo usuário ou presente no contexto (ex.: `feature/123-login-oauth` ou `feat/PROJ-45-carrinho`).

5. **Valide segurança e casos especiais antes de criar:**
   - **Nome duplicado:** Verifique com `git branch --list <nome>` e `git branch -r --list origin/<nome>`. Se já existir, sugira uma alternativa ou sufixo incremental.
   - **Alterações não commitadas em outra branch:** Informe que o `git checkout -b` leva as alterações locais se não houver conflito entre a branch atual e a branch de origem. Se houver conflito potencial, pare e consulte o usuário. Nunca execute `git stash`, `git reset` ou descarte alterações sem autorização.
   - **Mudanças mistas:** Se o diff misturar funcionalidades e correções independentes, alerte o usuário e sugira dividir em branches separadas.

6. **Crie a branch e apresente o resumo:**
   - Execute `git checkout -b <nome-da-branch> <branch-de-origem>` e confirme com `git branch --show-current`.
   - Apresente um resumo curto contendo: modelo detectado, branch de origem, branch criada, justificativa da classificação, 2 sugestões de nomes alternativos e próximos passos (commit e push).

## Cuidados Comuns (Gotchas)

- **Escopo estrito:** Não faça `git add`, `git commit`, `git push`, `git merge` ou `git rebase`. Esta skill apenas analisa, cria a branch e faz checkout para ela.
- **Nunca invente branches base:** Não crie `develop`, `main` ou `master` automaticamente se elas não exist