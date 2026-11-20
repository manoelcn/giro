---
name: github-pr-creator
description: Cria Pull Requests (PR) completos e padronizados no GitHub (ou prepara o título, descrição e comandos gh cli para abertura), adaptando-se automaticamente ao template do repositório (.github/pull_request_template.md) ou usando um modelo padrão de engenharia de software. Use sempre que o usuário pedir para criar um PR, abrir um Pull Request, gerar ou revisar a descrição de um PR, ou mencionar pull_request_template.md.
---
# Criador de Pull Request (PR)

Esta skill orienta o agente a preparar e criar Pull Requests completos no GitHub — desde a análise das alterações e validação da branch até a geração da descrição seguindo o template do repositório e a criação efetiva via GitHub CLI (`gh pr create`) ou fornecimento do comando pronto.

## Quando Usar

- Quando o usuário pedir para criar, abrir ou submeter um Pull Request no GitHub.
- Quando o usuário pedir para gerar, montar ou revisar o título e a descrição de um PR a partir de um `git diff`, histórico de commits ou resumo de implementação.
- Quando o usuário mencionar `.github/pull_request_template.md` ou quiser padronizar a entrega de código de qualquer repositório.

## Fluxo de Execução

1. **Inspecione o contexto e o template do repositório:**
   - Verifique se existe um arquivo `.github/pull_request_template.md` (ou variações em `.github/PULL_REQUEST_TEMPLATE/`) no repositório atual. Se existir, utilize exatamente a estrutura dele.
   - Caso o repositório não possua um template próprio, utilize o **Template Padrão** definido na seção abaixo.
   - Analise as alterações (commits da branch atual vs. branch base, `git diff`, arquivos modificados ou relato do usuário) para identificar o objetivo, impacto técnico, componentes afetados e eventuais Issues relacionadas.

2. **Valide o estado do Git (quando houver acesso ao terminal/repositório):**
   - Verifique a branch atual (`git branch --show-current`) e garanta que ela não seja a branch principal (`main`/`master`).
   - Confirme se há alterações não commitadas (`git status`) e se a branch já foi enviada para o remoto (`git push -u origin <branch>`).
   - Se o repositório não tiver acesso local/terminal no ambiente do agente, prepare o comando completo para o usuário executar.

3. **Elabore o Título e a Descrição do PR:**
   - **Título:** Crie uma frase curta, clara e no imperativo ou descrevendo a entrega (ex.: `Implementa cancelamento de reserva com cálculo de multa` ou `feat(auth): adiciona autenticação via OAuth2`). Respeite Conventional Commits se o histórico do repositório seguir esse padrão.
   - **Corpo:** Preencha todas as seções do template encontrado (ou do Template Padrão), substituindo comentários por informações concretas e marcando `[x]` apenas nos itens confirmados. Inclua `Closes #<numero>` se houver Issue vinculada.

4. **Crie o Pull Request:**
   - **Com acesso ao shell/terminal e `gh` autenticado:** Execute a criação do PR passando título, corpo e branch base (ex.: `gh pr create --base main --title "<titulo>" --body "<corpo>"`). Se o usuário pedir revisão antes de abrir, apresente a prévia e aguarde confirmação.
   - **Sem acesso ao shell ou fora do ambiente local:** Exiba o título sugerido, o Markdown completo da descrição em um bloco de código copiável e o comando `gh pr create` pronto para execução no terminal.

## Template Padrão (Fallback)

Utilize esta estrutura apenas quando o repositório não tiver um `.github/pull_request_template.md` próprio:

```markdown
## O que foi feito
<!-- Resumo claro em 2 ou 3 linhas do que este PR entrega e qual problema resolve -->

## Tipo de mudança
- [ ] Nova funcionalidade (feature)
- [ ] Correção de bug (fix)
- [ ] Refatoração / Melhoria de código
- [ ] Documentação / Infraestrutura / Testes

## Principais alterações e componentes envolvidos
<!-- Liste os arquivos, módulos, classes ou endpoints modificados e as decisões técnicas relevantes -->

## Como testar
1.
2.

## Checklist do autor
- [ ] O código segue os padrões de estilo, nomenclatura e arquitetura do projeto
- [ ] Os casos de erro e validações foram tratados adequadamente
- [ ] Foram adicionados ou atualizados testes cobrindo as alterações
- [ ] Testei as alterações localmente e o fluxo funciona conforme esperado
- [ ] Documentação (README, comentários ou diagramas) atualizada, se aplicável

## Evidências (opcional)
<!-- Prints de tela, payloads de resposta da API ou logs de execução dos testes -->

## Observações para o revisor
<!-- Pontos de atenção, trade-offs, dependências ou referência de Issue (ex.: Closes #12) -->
```

## Boas Práticas e Cuidados (Gotchas)

- **Priorize o template do repositório:** Nunca sobrescreva um `.github/pull_request_template.md` existente com o template padrão; respeite sempre as seções e caixas de seleção originais do projeto.
- **Escopo e tamanho do PR:** Se detectar múltiplas funcionalidades não relacionadas na mesma branch, alerte o usuário de que PRs menores e coesos facilitam a revisão e reduzem conflitos.
- **Idioma consistente:** Escreva os textos explicativos do PR em português, mas mantenha nomes de classes, métodos, variáveis e rotas em inglês conforme o código do projeto.
- **Checklist honesto:** Marque `[x]` apenas nos itens verificáveis pelo diff ou relato; deixe `[ ]` nos itens que exigem validação manual do autor.