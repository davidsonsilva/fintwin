# Plano: Meta Harness — Codex CLI como revisor independente das slices

## 📅 Criado em: 2026-07-24

## 🎯 Status: IMPLEMENTADO E VALIDADO (piloto rodou com sucesso; ajustes pós-piloto pendentes de decisão do usuário)

---

## 📋 Resumo Executivo

Implementado o Meta Harness: `.meta-harness/` (prompt fixo, config, contratos, relatórios) + `scripts/validate-step.sh`, que chama `codex review` para revisar um commit específico com prompt customizado.

**Descobertas técnicas importantes durante a implementação (mudaram o design em relação ao plano original):**

1. `codex review --uncommitted` **não aceita prompt customizado** — é mutuamente exclusivo com `[PROMPT]` nesta versão da CLI (erro de parsing). O mesmo vale para `--commit <sha>` e (por extensão) `--base <branch>`. Ou seja: **nenhuma das flags de escopo da CLI (`--uncommitted`/`--base`/`--commit`) pode ser combinada com instruções de prompt customizadas** — só dá pra usar uma coisa ou outra.
2. Solução adotada: chamar `codex review` **sem nenhuma flag de escopo**, passando o prompt customizado via stdin, e colocar no próprio prompt (seção "CONTEXTO DE EXECUÇÃO") o SHA do commit a revisar + instrução explícita para o Codex rodar `git diff <pai>..<commit>` e `git show --stat <commit>` ele mesmo. Funciona porque o Codex é agentic e executa comandos git por conta própria.
3. **Sandbox sempre `read-only` no `codex review`** — a flag `--sandbox` não existe nesse subcomando (só em `codex`/`codex exec` top-level); o banner de execução mostrou `sandbox: read-only` mesmo com `config.json` pedindo `workspace-write`. Isso **impediu a execução completa dos testes** no piloto: pytest bloqueado (venv referenciava Python 3.12 indisponível no ambiente do Codex + sem acesso Docker), Vitest bloqueado por permissão de escrita em TEMP. **Decisão 4 do plano original (`workspace-write`) não é aplicável a `codex review` nesta versão — precisa ser revisitada.**
4. **O relatório final não seguiu o formato customizado pedido** (não tem `## Veredito`, `## Resumo executivo` etc.) — o Codex usou o formato nativo dele (parágrafo de resumo + lista de comentários com prioridade P1/P2 e severidade BLOCKER/HIGH/MEDIUM/LOW). As instruções de formato do nosso prompt foram parcialmente ignoradas em favor do template interno da ferramenta `codex review`.
5. O repositório nunca tinha commits além de um scaffold vazio (`apps/` inteiro estava untracked) — foi necessário criar um **commit de checkpoint** (`eff1199`, "chore: checkpoint commit through VS-07") consolidando VS-01 a VS-07 antes do piloto rodar de forma útil. Decisão tomada com confirmação explícita do usuário via AskUserQuestion.
6. **Custo**: execução via ChatGPT auth (não API key — `codex doctor` confirmou `stored auth mode: chatgpt`, `stored API key: false`), então **não há custo em dólares por chamada**, apenas consumo de quota/uso do plano ChatGPT do usuário. Tempo total do piloto: ~3,5 minutos (10:29:56 → 10:33:17) para revisar um diff de ~27 mil linhas com `reasoning_effort=high`, mesmo com a execução de testes bloqueada pelo sandbox.

## 🎯 Resultado do piloto (útil apesar das limitações acima)

O Codex encontrou **findings reais e genuínos na VS-07**, mesmo sem rodar os testes:

- **HIGH** — `LOAN` (empréstimo) delega para `apply_financing` e só adiciona a dívida de reembolso, nunca credita o principal emprestado como entrada/evento — a simulação piora o saldo em vez de refletir o dinheiro recebido. Bug real em `apps/api/src/domain/decisions/appliers.py:162-166`.
- **HIGH** — custo total de financiamento (`engine.py::_total_cost`) soma os custos recorrentes apenas uma vez, não ao longo da duração do financiamento — `Custo Total` fica subestimado. `apps/api/src/domain/decisions/engine.py:99-107`.
- **HIGH** — nenhuma validação dos parâmetros específicos de cada tipo de decisão (`required_parameters` do registro `DECISION_TYPES` nunca é checado) — request vazio ou negativo gera 500 em vez de 422. `apps/api/src/interfaces/http/schemas/simulation.py:31-35`.
- **HIGH** — `scenario_override` não é persistido junto com a simulação (só os `parameters` da decisão) — viola a seção 10.4 da Spec ("todos os parâmetros deverão ser visíveis e persistidos junto à simulação"). `apps/api/src/application/use_cases/simulation_use_cases.py:70-75`.
- **HIGH** — `DecisionForm.tsx` não expõe todos os campos do `ScenarioOverride` no cenário personalizado (faltam duração de perda de renda e capacidade de redução de despesas). `apps/web/src/features/simulation/DecisionForm.tsx:147-148`.
- **MEDIUM** — `ResourceStepConfig<any>` em `resourceConfigs.ts` quebra `npm run lint` (pré-existente, não é da VS-07, mas bloqueia o lint do projeto).
- Também reafirmou os erros de `tsc --noEmit` pré-existentes já conhecidos (ProjectionChart, FragilityList, ProfileStep, ResourceStepForm) como **bloqueadores reais de build/lint**, não apenas ruído cosmético como eu vinha tratando.

Estes 4 findings HIGH da VS-07 (LOAN, custo total, validação de parâmetros, persistência do scenario_override, campos faltando no form) ainda **não foram corrigidos** — ficam como próxima ação, a combinar com o usuário se corrige agora ou registra como dívida técnica.

---

## 🏗️ Arquitetura Final (como implementado, difere do plano original nos pontos acima)

```
Claude implementa a slice (plano aprovado → código → testes → demo real via Docker)
  ↓
Claude cria um commit de checkpoint ao final da slice (NOVO — não estava no plano original,
  necessário porque `--uncommitted` não aceita prompt customizado)
  ↓
Claude gera/atualiza os contratos (.meta-harness/contracts/*) a partir do plano já aprovado
  ↓
Claude roda scripts/validate-step.sh [commit-sha opcional, default HEAD]
  ↓
Script resolve o SHA e o pai, monta prompt+contratos+instruções de git diff, chama
  `codex review` SEM flags de escopo (só -c model=... -c model_reasoning_effort=...),
  prompt via stdin, salva relatório em .meta-harness/reports/codex-review-<timestamp>.md
  ↓
Claude lê o relatório (formato nativo do Codex, não o template customizado pedido)
  ↓
Claude decide: corrigir findings HIGH/BLOCKER sozinho e revalidar, ou apresentar ao usuário
```

## Estrutura de arquivos (implementada)

```
.meta-harness/
├─ prompts/codex-review.md       # prompt fixo — ESCOPO ajustado para "diff da etapa atual" via CONTEXTO DE EXECUÇÃO, não mais "não commitado"
├─ contracts/current-slice.md    # gerado a partir do plano da VS-07 (+ nota sobre o piloto ser baseline VS-01-07)
├─ contracts/acceptance-criteria.md
├─ reports/                       # 5 relatórios do piloto (4 falhas de argumento + 1 sucesso), todos versionados
└─ config.json                    # model="gpt-5.6-terra", reasoning_effort="high", sandbox="workspace-write" (campo sandbox não é aplicável a `codex review`, mantido só como documentação da intenção)
scripts/validate-step.sh          # bash; aceita SHA opcional (default HEAD), resolve pai via git rev-parse, chama codex review sem flags de escopo
```

---

## ✅ Decisões Tomadas (atualizadas após o piloto)

### Decisão 1 (revisada): `codex review` sem flags de escopo, git diff explícito no prompt
- **O quê**: em vez de `--uncommitted`/`--commit`/`--base`, o script chama `codex review` puro (sem flag de escopo), e o próprio prompt instrui o Codex a rodar `git diff <pai>..<commit>` para descobrir o que revisar.
- **Por quê**: `--uncommitted`/`--commit`/`--base` são mutuamente exclusivos com `[PROMPT]` nesta versão da CLI (0.145.0) — não dá pra ter os dois. Descoberto empiricamente após 3 tentativas falhas.
- **Alternativas rejeitadas**: usar `--uncommitted`/`--commit` e abrir mão do prompt customizado (perderia o formato estruturado e os contratos — não testado se valeria a pena, mas o usuário priorizou manter o prompt customizado implicitamente ao aprovar seguir corrigindo).

### Decisão 1b (nova): commit de checkpoint por slice, a partir de agora
- **O quê**: cada Vertical Slice concluída recebe um commit ao final (não existia essa prática antes). Foi necessário um commit de checkpoint único (`eff1199`) consolidando VS-01–VS-07 para o piloto funcionar.
- **Por quê**: sem commit, não há um "SHA + pai" para o Codex diferenciar via `git diff` — e commitar também é o único jeito de manter o repositório num estado historicamente rastreável (requisito indireto do Meta Harness).
- **Confirmado explicitamente pelo usuário** via AskUserQuestion ("Eu crio um commit de checkpoint agora") depois que o conflito `--uncommitted`/prompt foi descoberto.

### Decisão 4 (revisada): sandbox `workspace-write` não é aplicável ao `codex review`
- **O quê**: `config.json` mantém `sandbox: "workspace-write"` como intenção documentada, mas **não há como aplicá-la** — `codex review` não expõe a flag `--sandbox` e roda sempre em `read-only`.
- **Impacto real observado**: pytest/vitest não rodaram de verdade no piloto (bloqueados por sandbox + ambiente do Codex não ter o mesmo venv/Docker). O Codex ainda encontrou bugs reais analisando código estaticamente, mas **não temos ainda a "prova de execução real dos testes" que era o objetivo original da Decisão 4**.
- **Em aberto**: decidir com o usuário se isso é aceitável (Codex como revisor estático + eu já rodo os testes antes) ou se vale investigar `codex exec`/outro subcommand com sandbox configurável para official test execution.

### Demais decisões (2, 3, 5, 6, 7) permanecem como no plano original — não foram invalidadas pelo piloto.

---

## ❌ Lições / Achados Técnicos (críticos para não repetir)

1. **Sempre testar a combinação exata de flags antes de assumir que funciona**, mesmo com `--help` consultado — o `--help` mostrava `[PROMPT]` na mesma linha de uso que `--uncommitted`/`--commit`, mas a implementação real rejeita a combinação. `--help` documenta os argumentos aceitos individualmente, não necessariamente as combinações válidas.
2. **`codex review` tem seu próprio template de saída** e pode não obedecer 100% a um formato de relatório customizado pedido via prompt — os "achados" vieram em formato nativo (P1/P2, texto livre), não na estrutura `## Veredito` / `## Findings` etc. que pedimos. Se o formato exato importa muito, pode ser necessário pós-processar a saída do Codex, ou aceitar o formato nativo dele.
3. **`--sandbox` só existe no `codex`/`codex exec` de nível superior, não no `codex review`** — checar `<subcomando> --help` especificamente, não só o `--help` do comando pai.
4. Repositório sem histórico de commits granulares (`apps/` inteiro untracked desde sempre) é incompatível com qualquer estratégia de review baseada em diff de commit — precisa de commits por slice para o harness funcionar de forma barata e focada.

---

## 🔧 Especificações Técnicas (atualizadas)

### Requisitos Funcionais
1. `scripts/validate-step.sh [sha-ou-ref opcional, default HEAD]` — resolve o commit e seu pai via `git rev-parse`.
2. Monta prompt = `codex-review.md` + `current-slice.md` + `acceptance-criteria.md` + bloco de contexto de execução (SHA, SHA do pai, instruções de git diff explícitas).
3. Chama `codex review -c model="..." -c model_reasoning_effort="..." -` (prompt via stdin), **sem flags de escopo**.
4. Salva relatório em `.meta-harness/reports/codex-review-<timestamp>.md` (via `tee`, preservado mesmo se o Codex falhar).
5. Falha com exit code não-zero se `codex` não estiver no PATH, prompt/config não existirem, ou a chamada ao Codex retornar erro.

### Pendências técnicas em aberto
- [ ] Decidir se corrigimos os 4 findings HIGH da VS-07 encontrados no piloto (LOAN, custo total, validação de parâmetros, persistência de scenario_override, campos faltando no form) antes de seguir para VS-08.
- [ ] Decidir se aceitamos sandbox read-only (sem execução real de testes pelo Codex) como suficiente, ou investigar alternativa.
- [ ] Decidir se vale a pena pós-processar a saída do Codex para forçar o formato `## Veredito` etc., ou adotar o formato nativo dele no processo.

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_20260724_150000` (deletada)
- Documento de origem: `docs/features/meta-harness.md`
- Codex CLI: v0.145.0, autenticado via ChatGPT (sem custo em $ por chamada, consome quota do plano)
- Commit de checkpoint: `eff1199` (chore: checkpoint commit through VS-07)
- Relatório do piloto bem-sucedido: `.meta-harness/reports/codex-review-20260724-102956.md`
- Repo: `D:\IA Projects\gemeo-financeiro`, branch `master`

---

## 🚦 Próximo Passo

Reportar ao usuário: piloto funcionou tecnicamente (após 3 ajustes de CLI), achou 4 bugs reais de HIGH severity na VS-07 mesmo sem rodar testes, mas revelou 3 limitações do harness que precisam de decisão (sandbox sempre read-only, formato de saída não customizável via prompt, necessidade de commit por slice). Perguntar: corrigir os findings agora, e/ou ajustar o design do harness antes de torná-lo padrão para VS-08 em diante.
