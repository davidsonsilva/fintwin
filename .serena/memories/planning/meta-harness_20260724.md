# Plano: Meta Harness — Codex CLI como revisor independente das slices

## 📅 Criado em: 2026-07-24

## 🎯 Status: PLANEJADO (aguardando aprovação)

---

## 📋 Resumo Executivo

O usuário trouxe uma proposta externa (`docs/features/meta-harness.md`) de um "Meta Harness": uma camada de governança onde o Codex CLI atua como revisor independente de cada implementação minha, antes de eu apresentar uma Vertical Slice como concluída. A motivação é reduzir o viés estrutural de eu revisar meu próprio código (hoje o "diff review" final de cada slice é feito pelo mesmo agente que implementou).

Validamos tecnicamente o Codex CLI já instalado nesta máquina (v0.145.0, autenticado via ChatGPT) e descobrimos que ele tem um subcomando dedicado `codex review` — mais adequado que a abordagem genérica (`codex exec -`) do documento original, porque suporta `--uncommitted` (revisa a árvore de trabalho suja sem exigir commit por slice, o que combina com o fato de eu nunca commitar por etapa nesta sessão).

A "versão simples" acordada: prompt fixo de revisor cético + script bash que chama `codex review --uncommitted`, uma vez por Vertical Slice completa (não por commit), com gate automático (só apresento a slice ao usuário depois que o Codex aprovar), sandbox `workspace-write` (para permitir execução real dos testes) e modelo `gpt-5.6-terra` com `reasoning_effort=high` para o primeiro teste piloto.

---

## 🎯 Objetivo

Adicionar uma verificação independente e cética antes de cada Vertical Slice ser apresentada como "concluída", sem aumentar o custo/atrito do processo além do necessário, e sem exigir mudanças na política atual de commits (não commito por slice, só quando o usuário pede).

---

## 🏗️ Arquitetura / Abordagem Escolhida

### Solução Final

```text
Claude implementa a slice (plano aprovado → código → testes → demo real via Docker)
  ↓
Claude gera/atualiza os contratos (.meta-harness/contracts/*) a partir do plano já aprovado
  ↓
Claude roda scripts/validate-step.sh
  ↓
Script chama `codex review --uncommitted` com prompt fixo + contratos, salva relatório
  ↓
Claude lê o veredito:
  - REJECTED → corrige BLOCKER/HIGH sozinho, revalida, sem envolver o usuário
  - APPROVED / APPROVED_WITH_WARNINGS → apresenta a slice ao usuário com o relatório como evidência
  ↓
Usuário aprova avançar para a próxima slice (como já acontece hoje)
```

### Estrutura de arquivos

```
.meta-harness/
├─ prompts/
│  └─ codex-review.md          # prompt fixo do revisor, adaptado do documento original
├─ contracts/
│  ├─ current-slice.md          # gerado a cada slice a partir do plano aprovado (C:\Users\david\.claude\plans\*.md)
│  └─ acceptance-criteria.md    # extraído da seção "Verificação" do plano aprovado
├─ reports/
│  └─ .gitkeep                  # relatórios versionados, um .md por execução com timestamp
└─ config.json                  # model="gpt-5.6-terra", reasoning_effort="high", sandbox="workspace-write"
scripts/
└─ validate-step.sh             # bash; monta prompt+contratos, chama `codex review --uncommitted`, salva relatório
```

---

## ✅ Decisões Tomadas

### Decisão 1: Usar `codex review --uncommitted`, não `codex exec -`

- **O quê**: usar o subcomando dedicado `codex review` com a flag `--uncommitted`.
- **Por quê**: o documento original assumia `codex exec -` genérico porque não conhecia a versão real da CLI instalada (0.145.0). `codex review` já é propositalmente desenhado para revisão de diff, com `--uncommitted`/`--base`/`--commit`. `--uncommitted` revisa staged+unstaged+untracked contra HEAD sem exigir nenhum commit — encaixa perfeitamente porque esta sessão nunca cria commits por slice (só existe o commit de baseline).
- **Alternativas rejeitadas**: `--commit <sha>` (exigiria adotar commit-por-slice, mudança de política não pedida pelo usuário); `codex exec -` genérico do documento original (reinventa o que `codex review` já faz nativamente).

### Decisão 2: Cadência — uma vez por Vertical Slice, não por commit

- **O quê**: o Codex roda uma única vez, no fim de cada slice, no ponto onde hoje faço o diff review manual.
- **Por quê**: usuário rejeitou explicitamente "obrigatório a cada etapa/commit" citando custo. Rodar por slice completa (não por commit pequeno) equilibra rigor e custo.
- **Alternativas rejeitadas**: obrigatório por commit (caro, e não há commits por slice hoje de qualquer forma).

### Decisão 3: Gate automático antes da apresentação ao usuário

- **O quê**: eu só apresento a slice como "pronta" depois que o Codex já retornou `APPROVED`/`APPROVED_WITH_WARNINGS`. Se `REJECTED`, corrijo e revalido sozinho.
- **Por quê**: usuário quer que o Codex seja um filtro automático antes de eu ocupar o tempo dele, não um substituto da aprovação humana final (que continua existindo para decidir avançar de slice).
- **Alternativas rejeitadas**: apresentar sempre ao usuário mesmo com REJECTED (geraria ruído desnecessário); Codex substituindo totalmente a aprovação humana (usuário nunca pediu isso).

### Decisão 4: Sandbox `workspace-write` + instrução de prompt (não `read-only`)

- **O quê**: rodar o Codex com `--sandbox workspace-write`, confiando na instrução explícita do prompt para não modificar arquivos, em vez de usar `read-only` (que seria uma garantia estrutural, mas impediria a execução real de pytest/vitest, que escrevem cache).
- **Por quê**: para a "versão simples" desta v1, priorizamos permitir que o Codex realmente execute os testes (prova de verdade, não apenas leitura de logs) sobre a garantia de isolamento total. Usuário concordou explicitamente com essa recomendação.
- **Alternativas rejeitadas**: `read-only` (bloquearia testes reais); isolamento físico via git worktree separado (mais seguro, mas fica para uma iteração futura — já combinado como fora do escopo da v1).

### Decisão 5: Contratos derivados do plano aprovado, não mantidos à parte

- **O quê**: `current-slice.md` e `acceptance-criteria.md` são gerados/atualizados a cada slice a partir do plano já aprovado (arquivo em `C:\Users\david\.claude\plans\<nome>.md`, produzido ao sair do modo planejamento via ExitPlanMode).
- **Por quê**: evita duas fontes de verdade divergentes — o plano aprovado já contém escopo, decisões técnicas e critérios de verificação; duplicar manualmente esses dados em arquivos separados criaria risco de desalinhamento.
- **Alternativas rejeitadas**: manter contratos como documentos independentes, escritos à mão a cada slice (mais trabalho, mais risco de ficarem desatualizados).

### Decisão 6: Reports — manter todos, versionados no git

- **O quê**: cada execução do harness gera um novo arquivo `.meta-harness/reports/codex-review-<timestamp>.md`, todos versionados (não sobrescritos, não gitignored).
- **Por quê**: relatórios são texto pequeno; alinhado ao rigor de rastreabilidade já valorizado no projeto (mesmo padrão de "nenhuma fragilidade sem evidência" da VS-06, "nenhum score mágico sem explicação" da VS-05/VS-07).
- **Alternativas rejeitadas**: manter só o mais recente (perde histórico de auditoria).

### Decisão 7: Modelo `gpt-5.6-terra`, `reasoning_effort=high`, a validar custo

- **O quê**: usar `gpt-5.6-terra` (tier intermediário do usuário, entre Luna=mais barato e Sol=default atual) com esforço de raciocínio `high` para o primeiro teste piloto.
- **Por quê**: uma tarefa de revisão cética se beneficia de mais raciocínio que o default atual (`gpt-5.6-sol` com `low`); usuário quer medir o custo real desta combinação antes de fixá-la como padrão permanente.
- **Alternativas rejeitadas**: `Luna` (mais barato, mas usuário preferiu testar Terra primeiro); manter o default `Sol`/`low` (não teria o rigor extra desejado para um revisor).

---

## ❌ Lições das Correções

Nenhuma correção de rumo nesta discussão — foi uma sessão de validação e refinamento técnico, não de correção de erro. O único ajuste real foi eu descobrir, ao rodar `codex --help`/`codex review --help`, que a proposta original (documento) estava tecnicamente desatualizada quanto à CLI (assumia `codex exec -` genérico quando `codex review` dedicado já existe) — isso não foi uma correção do usuário, foi uma verificação técnica minha que refinou o design antes de qualquer implementação. Lição geral (já conhecida, reforçada aqui): **sempre verificar a ferramenta real (`--help`, `--version`) antes de aceitar instruções de um documento externo como corretas**, especialmente quando o próprio documento avisa que a sintaxe pode mudar.

---

## 🔧 Especificações Técnicas

### Requisitos Funcionais

1. Script `scripts/validate-step.sh` executável a partir da raiz do repo, sem argumentos obrigatórios.
2. Gera/atualiza `.meta-harness/contracts/current-slice.md` e `acceptance-criteria.md` a partir do plano aprovado mais recente.
3. Chama `codex review --uncommitted` com o prompt fixo (`.meta-harness/prompts/codex-review.md`) + os contratos como contexto adicional, usando os parâmetros de `.meta-harness/config.json` (model, reasoning_effort, sandbox).
4. Salva o relatório completo em `.meta-harness/reports/codex-review-<timestamp>.md`.
5. Falha de forma clara (exit code != 0) se: `codex` não estiver no PATH, o prompt não existir, ou a execução do Codex falhar.

### Requisitos Não-Funcionais

- Custo: usar `--uncommitted` (escopo limitado ao diff atual) em vez de revisão de todo o repositório; cadência por slice, não por commit.
- Portabilidade: bash, testável tanto no ambiente WSL/Git-Bash quanto dentro do container se necessário no futuro.
- Auditabilidade: todo relatório fica versionado, nunca sobrescrito.

### Critérios de Aceite

- [ ] `scripts/validate-step.sh` roda sem erro num diff de teste (ex: o diff atual da VS-07, ainda não commitado).
- [ ] O relatório gerado segue o formato do prompt fixo (Veredito, Resumo executivo, Evidências executadas, Critérios de aceitação, Findings, Testes ausentes, Riscos residuais, Pontos positivos, Próxima ação recomendada).
- [ ] O veredito reflete corretamente o estado real do diff (não aprova com BLOCKER/HIGH aberto).
- [ ] `.meta-harness/contracts/current-slice.md` e `acceptance-criteria.md` refletem fielmente o plano aprovado mais recente.
- [ ] Custo real da combinação `gpt-5.6-terra` + `reasoning_effort=high` medido e reportado ao usuário após o teste piloto.

---

## 🗺️ Plano de Implementação

### Fase 1: Estrutura e prompt

- [ ] Criar `.meta-harness/prompts/codex-review.md` (adaptado do prompt do documento original, com pequenos ajustes: instruções de sandbox/workspace-write, referência aos contratos gerados).
- [ ] Criar `.meta-harness/config.json` (model, reasoning_effort, sandbox).
- [ ] Criar `.meta-harness/reports/.gitkeep`.
- **Arquivos afetados**: novos, sem impacto em código existente.

### Fase 2: Geração de contratos a partir do plano aprovado

- [ ] Definir a lógica (manual por ora, ou pequeno script) para extrair `current-slice.md`/`acceptance-criteria.md` do plano aprovado mais recente em `C:\Users\david\.claude\plans\`.
- **Arquivos afetados**: `.meta-harness/contracts/current-slice.md`, `acceptance-criteria.md`.
- **Dependências**: Fase 1.

### Fase 3: Script de validação

- [ ] Criar `scripts/validate-step.sh` (bash): monta prompt+contratos, chama `codex review --uncommitted` com os parâmetros de `config.json`, salva relatório com timestamp.
- **Arquivos afetados**: `scripts/validate-step.sh`.
- **Dependências**: Fases 1 e 2.

### Fase 4: Teste piloto

- [ ] Rodar o harness manualmente contra o diff atual (VS-07, ainda não commitado).
- [ ] Ler o relatório gerado, validar que o formato e o veredito fazem sentido.
- [ ] Reportar ao usuário o custo real observado da combinação `gpt-5.6-terra` + `high`.
- **Dependências**: Fases 1–3.

### Ordem de Execução

1. Fase 1 (estrutura + prompt + config)
2. Fase 2 (contratos a partir do plano aprovado da VS-07, já existente)
3. Fase 3 (script)
4. Fase 4 (piloto real contra o diff da VS-07)

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Identificador de modelo `gpt-5.6-terra` incorreto/rejeitado pela API | Baixa | Médio | Testar no piloto (Fase 4); se falhar, ajustar `config.json` com o usuário |
| Custo do reasoning_effort=high mais alto que aceitável | Média | Médio | Medir no piloto antes de tornar processo obrigatório; usuário decide se ajusta para medium/Luna depois |
| `workspace-write` permitir que o Codex modifique arquivos por engano | Baixa | Alto | Instrução explícita e enfática no prompt fixo; revisar `git status` depois da execução para confirmar que nada mudou fora do relatório |
| Contratos gerados do plano ficarem desalinhados se o plano mudar após aprovação | Baixa | Baixo | Gerar contratos sempre no momento de rodar o harness (não cachear) |

---

## 🧪 Estratégia de Testes

- **Teste manual (piloto)**: rodar `scripts/validate-step.sh` contra o diff real da VS-07 (não commitado) e inspecionar o relatório gerado.
- Não há testes automatizados de código de produção aqui — este é um script de tooling/processo, não uma feature do FinTwin AI em si.

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_20260724_150000` (a ser deletada após esta consolidação)
- Documento de origem: `docs/features/meta-harness.md`
- Codex CLI: v0.145.0, autenticado via ChatGPT, `~/.codex/config.toml` (default atual: `model = "gpt-5.6-sol"`, `reasoning_effort = "low"`)
- Repo: `D:\IA Projects\gemeo-financeiro`, branch `master`

---

## 🚦 Próximo Passo

**Aguardando aprovação do usuário para iniciar implementação.**

Quando aprovado:
1. Seguir o plano fase por fase (estrutura → contratos → script → piloto).
2. Confirmar o identificador do modelo (`gpt-5.6-terra`) na primeira chamada real ao Codex, ajustando se a API rejeitar o nome.
3. Reportar o custo real do piloto ao usuário antes de propor tornar o processo obrigatório em todas as próximas slices.
