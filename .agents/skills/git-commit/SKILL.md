---
name: git-commit
description: 'Use esta skill quando o usuário quiser fazer um commit no Git ou dividir as alterações em mais de um commit. Use também quando o usuário digitar "/commit", pedir para "commitar", "fazer commit" ou pedir um commit no padrão Conventional Commits. A skill examina o diff, adiciona à área de preparação (stage) os arquivos relacionados, escreve uma mensagem de commit em português brasileiro no padrão Conventional Commits e executa git commit. Não use quando o usuário quiser apenas a mensagem de commit, sem o commit. Não use para fazer push, abrir pull request, fazer rebase ou alterar o histórico de commits.'
license: MIT
compatibility: 'Requer Git. A opção `--resolved` do `git add` requer Git 2.56 ou superior. Versões mais antigas usam a alternativa descrita no passo 3.'
allowed-tools: shell(git:*)
---

# Git Commit com Conventional Commits em português brasileiro

Faça commits no Git que sigam a especificação [Conventional Commits 1.0.0](https://www.conventionalcommits.org/pt-br/v1.0.0/). Obtenha o tipo, o escopo e o resumo a partir do diff.

## Idioma

- Escreva em **português brasileiro** o resumo, o corpo e o valor dos rodapés comuns (por exemplo, o texto depois de `Refs:`).
- Mantenha em **inglês** os elementos que fazem parte da especificação, porque ferramentas os leem como estão: o `tipo` (`feat`, `fix`, `docs` etc.), o token `BREAKING CHANGE` e os tokens dos rodapés (`Closes`, `Refs` etc.).
- O escopo segue o nome do módulo ou da pasta como aparece no código. Não o traduza.
- Se o repositório usar outro idioma nas mensagens ou tiver uma regra própria sobre o idioma, siga a regra do repositório (veja o passo 1).
- Use acentos e cedilha normalmente. Salve a mensagem em UTF-8.

## Formato da mensagem

```text
<tipo>(<escopo>): <resumo>

<corpo>

<rodapé>
```

- O escopo, o corpo e o rodapé são opcionais. Sem escopo, escreva `<tipo>: <resumo>`.
- Escreva o resumo com o verbo no infinitivo: "adicionar", não "adicionado" nem "adiciona".
- Mantenha a primeira linha com 72 caracteres ou menos. Não coloque ponto final.
- Comece o resumo com letra minúscula, a menos que a primeira palavra seja um nome próprio ou uma sigla.
- No corpo, diga o que mudou e por quê.
- Escreva cada rodapé como `Token: valor` ou `Token #valor`, por exemplo `Refs: #456` ou `Closes #123`. O Conventional Commits aceita as duas formas, mas o Git lê como trailer apenas `Token: valor`. No token, use `-` no lugar de espaço.
- Não adicione o trailer `Co-authored-by` às mensagens de commit.

## Tipos

O Conventional Commits define apenas `feat` e `fix`. Os outros tipos vêm da convenção Angular ([`@commitlint/config-conventional`](https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional)). Se o repositório tiver uma lista própria, use essa lista.

| Tipo       | Use para                                                  |
| ---------- | --------------------------------------------------------- |
| `feat`     | Uma nova funcionalidade                                   |
| `fix`      | Uma correção de bug                                       |
| `docs`     | Apenas documentação                                       |
| `style`    | Apenas formatação, sem mudança na lógica                  |
| `refactor` | Uma mudança de código que não é funcionalidade nem correção |
| `perf`     | Uma melhoria de desempenho                                |
| `test`     | Testes novos ou alterados                                 |
| `build`    | O sistema de build ou as dependências                     |
| `ci`       | A configuração de CI                                      |
| `chore`    | Outras tarefas de manutenção                              |
| `revert`   | A reversão de um commit anterior                          |

## Mudanças incompatíveis (breaking changes)

Coloque `!` antes dos dois-pontos ou adicione um rodapé `BREAKING CHANGE:`. Escreva o token em maiúsculas e em inglês. `BREAKING-CHANGE:` também está correto. O texto depois do token fica em português.

```text
feat(api)!: remover os endpoints da v1

BREAKING CHANGE: os clientes devem usar os endpoints da v2.
```

## Fluxo de trabalho

### 1. Leia as regras do repositório

Encontre as regras de commit antes de escrever uma mensagem:

- Uma configuração do commitlint, por exemplo `commitlint.config.js` ou `.commitlintrc.json`.
- O `CONTRIBUTING.md`.
- As mensagens recentes: `git log --oneline -10`.

Se uma regra do repositório for diferente desta skill, use a regra do repositório. Isso vale também para o idioma da mensagem: se o repositório exigir inglês, por exemplo, escreva em inglês.

### 2. Examine as alterações

```bash
git status --porcelain
git diff --staged
git diff
```

Se não houver alterações, execute as verificações do início do passo 3. Se elas encontrarem `MERGE_HEAD`, continue. Se não, diga ao usuário o que `git status --long` mostra. Não faça um commit vazio.

### 3. Adicione os arquivos ao stage

Primeiro, verifique se há uma operação em andamento. Execute cada comando separadamente. Não os encadeie com `&&`. Em um subdiretório, execute todos os comandos deste passo como `git -C <raiz> ...`. O comando `git rev-parse --show-toplevel` mostra a raiz.

```bash
git rev-parse -q --verify --symbolic-full-name MERGE_HEAD
git rev-parse -q --verify --symbolic-full-name CHERRY_PICK_HEAD
git rev-parse -q --verify --symbolic-full-name REVERT_HEAD
git diff --name-only --diff-filter=U --no-relative
git status --long
```

Um comando `rev-parse` mostra o nome de uma referência se a operação correspondente estiver em andamento. Se não estiver, o comando não mostra nada e termina com status 1. O comando `git diff` lista os arquivos não mesclados (unmerged). Ele encontra conflitos que não têm referência, por exemplo os de `git stash pop`. O `git status --long` mostra os outros casos.

**Se houver uma operação em andamento ou arquivos não mesclados**, não remova arquivos do stage. Não divida o commit. O índice contém o resultado da operação. Se você remover um arquivo do stage, o Git descarta as alterações do outro lado ou apaga uma entrada de conflito.

- Pare e avise o usuário se `git status --long` mostrar "rebase in progress", "You are in the middle of an am session", "Cherry-pick currently in progress" ou "Revert currently in progress" (ou o texto equivalente na localização em português do Git).
- Execute `git status --porcelain=v2`. Uma linha que começa com `u` indica um arquivo não mesclado. Você pode resolver o arquivo somente se todas estas condições forem verdadeiras:
  - A linha começa com `u UU N...` ou `u AA N...`.
  - Cada modo na linha é `100644`, `100755` ou `000000`.
  - `git diff --no-relative` não mostra `Binary files differ` para o arquivo.
- Pergunte ao usuário como resolver todos os outros arquivos não mesclados. O Git não consegue encontrar marcadores de conflito nesses arquivos. `git add --resolved` e as verificações abaixo adicionam esses arquivos ao stage sem aviso. Adicione cada um deles ao stage somente depois que o usuário o resolver: `git add -- <caminho>`.
- Com Git 2.56 ou superior, adicione ao stage os arquivos que você pode resolver com `git add --resolved -- <caminhos>`.
- Com um Git mais antigo, verifique esses arquivos e adicione-os ao stage:

```bash
git diff --check -- caminho/do/arquivo1 caminho/do/arquivo2
git add -- caminho/do/arquivo1 caminho/do/arquivo2
```

- Adicione os arquivos ao stage somente se `git diff --check` não encontrar nenhuma linha "leftover conflict marker". Ignore os avisos de espaços em branco vindos do outro branch.
- Depois, em qualquer versão do Git, execute `git diff --name-only --no-relative` e `git ls-files --others --exclude-standard`. Eles listam as edições em outros arquivos. Ignore os arquivos que ainda estão não mesclados.
- Mostre esses caminhos ao usuário. Pergunte se eles pertencem ao commit. Adicione ao stage somente os caminhos aprovados com `git add -- <caminhos>`.
- O Git coloca entre aspas alguns caminhos, por exemplo caminhos com caracteres não ASCII (como nomes com acentos). O `git add` falha com um caminho entre aspas. Pergunte ao usuário sobre esses arquivos.

**Se não houver operação em andamento nem arquivo não mesclado**, coloque uma mudança lógica em cada commit. Se os arquivos no stage contiverem mais de uma mudança, primeiro remova do stage os arquivos das outras mudanças. Depois, adicione ao stage os arquivos desta mudança:

```bash
git reset -q -- caminho/do/outro-arquivo1 caminho/do/outro-arquivo2
git add -- caminho/do/arquivo1 caminho/do/arquivo2
git add -- '*.test.*'
git add -- src/components/
```

- Coloque um glob entre aspas. Sem aspas, o shell expande o glob e não encontra os arquivos nos subdiretórios.
- Não use `git add -p` nem `git add -i`. Esses comandos esperam uma entrada de uma pessoa.
- Examine a lista de arquivos no stage com `git diff --staged --name-only`. Não faça commit de segredos, por exemplo arquivos `.env`, `credentials.json` ou chaves privadas.

### 4. Escreva a mensagem

Obtenha cada parte a partir do diff:

- **Tipo**: o tipo de mudança.
- **Escopo**: o módulo ou a área que a mudança afeta.
- **Resumo**: o que mudou, em uma linha e em português brasileiro.

Exemplos de resumos:

- `feat(auth): adicionar renovação de token`
- `fix(parser): aceitar entrada vazia`
- `docs(readme): atualizar instruções de instalação`
- `refactor(pagamentos): extrair cálculo de juros para uma função`

### 5. Faça o commit

Quando o passo 3 encontrar `MERGE_HEAD`, `CHERRY_PICK_HEAD` ou `REVERT_HEAD`, execute `git commit --no-edit` sem caminhos e sem a opção `--cleanup`. Isso mantém a mensagem que o Git preparou. Não escreva uma nova mensagem com `-m`. A mensagem pode conter as linhas de comentário `Conflicts:` do Git. Não as remova.

Em todos os outros casos:

Passe cada parágrafo com uma opção `-m` diferente. O Git coloca uma linha em branco entre os parágrafos. Este comando funciona no Bash, no PowerShell e em outros shells.

```bash
git commit -m "feat(auth): adicionar renovação de token"
git commit -m "fix(parser): aceitar entrada vazia" -m "Um arquivo vazio causava uma falha." -m "Closes: #123"
```

Para uma mensagem longa, escreva a mensagem em um arquivo temporário. Depois execute `git commit -F <arquivo>`.

### 6. Confirme que o commit está correto

```bash
git log -1 --stat --first-parent
git status --porcelain
```

## Regras de segurança

- Não altere a configuração do Git.
- Não use `--no-verify`, a menos que o usuário peça. Os hooks podem estar em `.git/hooks` ou na configuração do Git.
- Se um hook falhar, o Git não faz o commit. Corrija o problema, adicione os arquivos ao stage de novo e execute o mesmo comando `git commit` outra vez. Não use `--amend`, porque ele altera o commit anterior.
- Não altere o histórico de commits, a menos que o usuário peça. Não use `git reset --hard`, `git rebase` nem o comando experimental `git history`.
- Não faça push, a menos que o usuário peça. Não faça force push no branch padrão.