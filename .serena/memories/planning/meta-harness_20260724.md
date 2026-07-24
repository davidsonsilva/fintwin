
# Plano: Meta Harness — Codex CLI como revisor independente das slices

## 📅 Criado em: 2026-07-24

## 🎯 Status: IMPLEMENTADO E ESTÁVEL (5 rodadas reais, incluindo 3 de auto-revisão que encontraram e corrigiram bugs no próprio harness)

---

## 📋 Resumo Executivo

O Meta Harness está funcional e maduro: `.meta-harness/` (prompt, config, contratos, baselines, raw, reports, state) + 3 scripts (`capture-baseline.sh`, `validate-step.sh`, `normalize-codex-review.py`). `codex review` (sem flags de escopo, prompt customizado via stdin) revisa um commit específico; um normalizador determinístico (sem gastar outra chamada de IA) parseia a saída nativa (Markdown ou JSON) e deriva um veredito por regra fixa, cruzando com uma baseline de quality gates para distinguir falha nova de falha pré-existente.

**O harness já se provou revisando a si mesmo**: nas rodadas de melhoria pós-piloto, ele encontrou 3 bugs reais e sucessivos na própria lógica de matching de baseline do `normalize-codex-review.py`, cada um corrigido antes da próxima rodada — um caso raro e valioso de uma ferramenta de qualidade sendo validada pelo próprio processo que ela implementa.

---

## 🏗️ Arquitetura Final (estável)

```
Antes de implementar uma slice: scripts/capture-baseline.sh <slug>
  → captura exit codes + falhas conhecidas (pytest/tsc/lint/vitest) em .meta-harness/baselines/<slug>-before.json
  ↓
Claude implementa a slice (plano aprovado → código → testes → demo real via Docker)
  ↓
Claude cria um commit de checkpoint ao final da slice
  ↓
Claude gera/atualiza os contratos (.meta-harness/contracts/*) a partir do plano já aprovado
  ↓
scripts/validate-step.sh [commit] [baseline.json]
  → monta prompt (codex-review.md + contratos + baseline embutida + BASE_COMMIT/TARGET_COMMIT)
  → chama `codex review` sem flag de escopo, prompt via stdin
  → salva saída nativa em .meta-harness/raw/codex-review-<timestamp>.txt
  → chama normalize-codex-review.py (raw → relatório padronizado em reports/, veredito derivado por regra fixa)
  → grava .meta-harness/state/current-review.json
  → exit code: 0 = APPROVED/APPROVED_WITH_WARNINGS, 2 = REJECTED, 1 = erro de ferramenta
  ↓
Claude lê o relatório padronizado; se REJECTED, corrige e roda de novo (loop até limpo)
  ↓
Claude apresenta a slice ao usuário com o(s) relatório(s) como evidência
```

## Estrutura de arquivos (implementada e estável)

```
.meta-harness/
├─ prompts/codex-review.md   # prompt fixo — escopo reforçado (não auditar repo inteiro),
│                              exige NEW_FAILURE/PRE_EXISTING_FAILURE + código exato do diagnóstico
├─ contracts/current-slice.md, acceptance-criteria.md
├─ baselines/<slug>-before.json   # capturado por capture-baseline.sh antes de cada slice
├─ raw/codex-review-<timestamp>.txt      # saída nativa do Codex, preservada sem alteração
├─ reports/codex-review-<timestamp>.md   # relatório padronizado, gerado deterministicamente
├─ state/current-review.json             # metadados da última execução (commit, veredito, paths)
└─ config.json                # model="gpt-5.6-terra", reasoning_effort="high", sandbox="read-only" (real)
scripts/
├─ capture-baseline.sh         # bash; roda pytest/tsc/lint/vitest, salva baseline JSON
├─ validate-step.sh            # bash; orquestra tudo (prompt → codex review → normalizador → state)
├─ normalize-codex-review.py   # parser determinístico Markdown/JSON, veredito por regra fixa
└─ test_normalize_codex_review.py   # 7 testes de regressão, sem framework externo
```

---

## ✅ Decisões Tomadas (estado final)

### `codex review` sem flags de escopo
`--uncommitted`/`--base`/`--commit` são mutuamente exclusivos com `[PROMPT]` nesta versão da CLI (0.145.0). Chamamos `codex review` puro, com BASE_COMMIT/TARGET_COMMIT e instruções de `git diff` explícitas no próprio prompt.

### Commit de checkpoint obrigatório por slice
Sem commit não há "pai" para o Codex comparar. Todas as correções desta sessão (VS-07 fixes + melhorias do harness) seguiram esse padrão: cada rodada de correção = um commit novo, revisado separadamente.

### Sandbox `read-only` aceito como definitivo
`codex review` não expõe `--sandbox`; roda sempre `read-only`. O Codex não executa a suíte de testes de ponta a ponta neste ambiente (falta venv/Docker equivalentes), mas isso não impediu achar bugs reais via análise estática cuidadosa — inclusive nos próprios scripts do harness.

### Baseline de quality gates (`capture-baseline.sh`)
Captura ANTES da implementação: pytest exit code, `tsc --noEmit` com lista de erros (`file(line,col): error TSxxxx: ...`), `npm run lint` com o log completo (não filtrado — o cabeçalho de arquivo por bloco é necessário para associar erros de lint ao arquivo certo), vitest exit code. Usada pelo normalizador para classificar findings como `NEW_FAILURE` ou `PRE_EXISTING_FAILURE`.

### Normalizador determinístico (`normalize-codex-review.py`)
Parseia tanto o formato Markdown-com-prioridade-P# quanto JSON estruturado (os dois formatos nativos já observados do `codex review`). Deriva veredito por regra fixa (BLOCKER/HIGH → REJECTED; só MEDIUM → APPROVED_WITH_WARNINGS; só LOW/INFO ou vazio → APPROVED), sem gastar outra chamada de IA.

### Matching de baseline: EXIGE identidade exata do diagnóstico (código TS / regra ESLint), não gate genérico
**Esta foi a decisão que levou 3 rodadas de auto-revisão para amadurecer** (ver seção abaixo). A versão final: `_extract_known_locations` extrai trios (arquivo, linha, código-TS-ou-regra-ESLint) da baseline; um finding só é `PRE_EXISTING_FAILURE` se arquivo + linha baterem **e** o código/regra exato aparecer na descrição do finding. O prompt (`codex-review.md`) agora **exige explicitamente** que o Codex cite esse código/regra ao reportar findings de typecheck/lint — sem isso, o normalizador não tem como confirmar que é o mesmo diagnóstico. Trade-off aceito conscientemente: se o Codex não citar o código, o finding vira `NEW_FAILURE` por padrão (nunca mascara um bug real; na pior hipótese, gera falso-positivo de "novo" para dívida técnica antiga).

---

## 🎯 Os 3 bugs de auto-revisão encontrados e corrigidos (cronologia)

1. **Matching só por nome de arquivo** (sem checar linha) — um finding novo em qualquer linha de um arquivo com falha conhecida era mascarado. Corrigido exigindo também a linha.
2. **Matching por arquivo+linha, sem identidade** — um finding novo e DIFERENTE (ex: bug de segurança) que caía por coincidência na mesma linha de uma falha de lint/typecheck conhecida ainda era mascarado. Corrigido exigindo que a descrição do finding mencionasse o mesmo *gate* (tsc/lint).
3. **Matching por gate genérico, não por diagnóstico exato** — dois diagnósticos DIFERENTES do MESMO gate na MESMA linha (ex: TS2769 conhecido vs. TS2322 novo) ainda podiam ser confundidos. Corrigido definitivamente: o prompt agora exige que o Codex cite o código/regra exato, e o normalizador compara por essa identidade específica.

Cada um desses foi encontrado pelo próprio `codex review` ao revisar o commit que implementou a correção do bug anterior — uma cadeia de auto-revisão genuína, não hipotética.

---

## 🎯 Findings reais na VS-07 (rodada 1, commit de checkpoint) — todos corrigidos

1. HIGH — `LOAN` não creditava o principal recebido → corrigido em `appliers.py::apply_loan`.
2. HIGH — custo total de financiamento não escalava custos recorrentes pela duração → corrigido em `engine.py::_total_cost`.
3. HIGH — parâmetros de decisão sem validação (500 em vez de 422) → corrigido com `validation.py::validate_decision_parameters`.
4. HIGH — `scenario_override` não persistido → corrigido: `ScenarioOverride.to_dict()` + persistido no use case.
5. MEDIUM (rodada 2) — `expense_reduction_capacity` fora de 0–1 gerava 500 → corrigido no router.
6. MEDIUM (pré-existente, não da VS-07) — `resourceConfigs.ts` com `any` quebra `npm run lint` — dívida técnica registrada, não corrigida nesta sessão.

Testes: 133 backend / 23 frontend passando após todas as correções da VS-07. 7 testes de regressão do normalizador do harness.

---

## ❌ Lições / Achados Técnicos (críticos para não repetir)

1. **Sempre testar a combinação exata de flags antes de assumir que funciona** — `--help` não deixa claro quais combinações são mutuamente exclusivas.
2. **`codex review` não tem formato de saída fixo** — varia entre prosa/Markdown e JSON estruturado. O normalizador precisa suportar ambos.
3. **`--sandbox` só existe em `codex`/`codex exec`, não em `codex review`**.
4. **Matching de texto livre para "é o mesmo problema de antes?" é genuinamente difícil** — muito permissivo mascara bugs reais, muito rígido nunca casa nada. A solução robusta não é ajustar a heurística do lado do parser, é **instruir a fonte (o prompt do Codex) a incluir o dado estruturado necessário** (código do diagnóstico) — resolve na raiz em vez de tentar adivinhar depois.
5. **Bug em bash: paths do Windows com espaço (`D:\IA Projects\...`) quebram regex que assume `\S+` para "resto da linha"** — usar `.+` quando o campo é garantidamente o último da linha.
6. **Bug em bash: `python -c` com paths estilo `/d/...` do Git Bash não funciona no Python nativo do Windows** — sempre converter com `cygpath -w` antes de passar paths para o Python.
7. **RTK (hook de otimização de tokens do ambiente) condensa a saída de comandos quando rodados interativamente, mas não quando chamados de dentro de um script** — a saída "crua" (mais detalhada) vem de dentro de scripts, não de chamadas diretas no terminal — relevante para quem for depurar por que `capture-baseline.sh` captura mais detalhe que rodar `npm run lint` manualmente.

---

## 📚 Pendências conhecidas (deliberadamente adiadas)

- **Não fixar ainda `gpt-5.6-terra` + `reasoning_effort=high` como padrão definitivo** — medir mais 2 execuções (slice pequena, slice média) focando em quota consumida/duração/findings úteis por revisão antes de comprometer essa combinação. Não há custo em $ (auth via ChatGPT).
- Dívida técnica pré-existente (não da VS-07): `resourceConfigs.ts` com `any` quebra `npm run lint`; erros de `tsc --noEmit` em `ProjectionChart.tsx`, `FragilityList.tsx`, `ProfileStep.tsx`, `ResourceStepForm.tsx` (já documentados em `project_overview`).

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_20260724_150000` (deletada)
- Documentos de origem: `docs/features/meta-harness.md` (proposta inicial), `docs/features/ajustes-meta-harness.md` (ajustes pós-piloto)
- Codex CLI: v0.145.0, autenticado via ChatGPT (sem custo em $ por chamada)
- Commits desta sessão (ordem): `eff1199` (checkpoint VS-01–07) → `28f0a58` (fix 4 HIGH da VS-07) → fix scenario_override validation → `feat(meta-harness)` baseline+normalizador+raw/state → fix matching arquivo+linha → fix matching por gate → fix matching por identidade exata (final)
- Repo: `D:\IA Projects\gemeo-financeiro`, branch `master`

---

## 🚦 Próximo Passo

Meta Harness pronto para uso operacional a partir da VS-08. Fluxo por slice: `capture-baseline.sh` antes de implementar → implementar → commit → `validate-step.sh` com a baseline → ler relatório → corrigir se REJECTED → revalidar → apresentar ao usuário quando limpo.
