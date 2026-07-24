
# Plano: Meta Harness — Codex CLI como revisor independente das slices

## 📅 Criado em: 2026-07-24

## 🎯 Status: IMPLEMENTADO, VALIDADO E COM FINDINGS CORRIGIDOS (2 rodadas reais concluídas)

---

## 📋 Resumo Executivo

O Meta Harness (`.meta-harness/` + `scripts/validate-step.sh`) está funcional: `codex review` (sem flags de escopo, prompt customizado via stdin, instruções de `git diff <pai>..<commit>` embutidas no prompt) revisa um commit específico de forma independente.

**Duas rodadas reais já rodaram:**
1. Piloto contra o commit de checkpoint (`eff1199`, VS-01–VS-07 inteiras) — achou 4 bugs HIGH reais (LOAN não creditava o principal; custo total de financiamento não escalava por duração; parâmetros de decisão sem validação; `scenario_override` não persistido) + 1 MEDIUM pré-existente (lint quebrado em `resourceConfigs.ts`).
2. Após eu corrigir os 4 HIGH e commitar (`28f0a58`), rodei o harness de novo contra esse commit menor (~17 arquivos) para validar — **achou mais 1 bug real**, introduzido pela própria correção: o novo campo `expense_reduction_capacity` no `DecisionForm` aceitava valores fora de 0–1 e gerava 500 em vez de 422. Corrigido e commitado (`próximo commit` — ver git log).

Isso confirma o valor do harness: ele pegou um bug genuíno numa correção feita *depois* do primeiro relatório, não só na implementação original.

---

## 🏗️ Arquitetura Final (estável, validada em 2 execuções reais)

```
Claude implementa a slice (plano aprovado → código → testes → demo real via Docker)
  ↓
Claude cria um commit de checkpoint ao final da slice (obrigatório — ver Decisão 1b)
  ↓
Claude gera/atualiza os contratos (.meta-harness/contracts/*) a partir do plano já aprovado
  ↓
Claude roda scripts/validate-step.sh [commit-sha opcional, default HEAD]
  ↓
Script resolve SHA + pai, monta prompt+contratos+instruções de git diff, chama
  `codex review` SEM flags de escopo (só -c model=... -c model_reasoning_effort=...),
  prompt via stdin, salva relatório em .meta-harness/reports/codex-review-<timestamp>.md
  ↓
Claude lê o relatório (formato pode ser Markdown livre OU JSON — ver Decisão sobre formato)
  ↓
Se achar findings reais → corrige, commita de novo, roda o harness de novo (loop até limpo)
  ↓
Claude apresenta a slice ao usuário com o(s) relatório(s) como evidência
```

## Estrutura de arquivos (implementada e estável)

```
.meta-harness/
├─ prompts/codex-review.md       # prompt fixo — sandbox read-only assumido explicitamente,
│                                  formato de saída flexibilizado (aceita nativo do Codex)
├─ contracts/current-slice.md    # gerado a partir do plano aprovado da slice em curso
├─ contracts/acceptance-criteria.md
├─ reports/                       # todos os relatórios versionados (Markdown ou JSON, conforme o Codex escolher)
└─ config.json                    # model="gpt-5.6-terra", reasoning_effort="high", sandbox="read-only" (refletindo a realidade)
scripts/validate-step.sh          # bash; aceita SHA opcional (default HEAD), resolve pai via git rev-parse
```

---

## ✅ Decisões Tomadas (estado final, pós-2-rodadas)

### Decisão 1 (final): `codex review` sem flags de escopo, git diff explícito no prompt
`--uncommitted`/`--base`/`--commit` são mutuamente exclusivos com `[PROMPT]` nesta versão da CLI (0.145.0). Solução: chamar sem flag de escopo, prompt via stdin, com o SHA do commit e do pai embutidos no "CONTEXTO DE EXECUÇÃO", instruindo o Codex a rodar `git diff <pai>..<commit>` ele mesmo.

### Decisão 1b (final): commit de checkpoint obrigatório por slice
Cada Vertical Slice (ou correção pós-revisão) recebe um commit ao final. Sem isso, não há "pai" para o Codex comparar. Validado nas 2 rodadas: commit `eff1199` (checkpoint VS-01–07) e `28f0a58` (fixes), cada um revisado separadamente.

### Decisão 4 (final): sandbox `read-only` aceito como suficiente
`codex review` não expõe `--sandbox` e roda sempre `read-only`. **Aceito formalmente** (não mais um problema em aberto): o Codex não consegue rodar pytest/vitest de ponta a ponta neste ambiente (falta de venv/Docker equivalentes, sem permissão de escrita em TEMP), mas mesmo assim achou 5 bugs reais nas 2 rodadas via análise estática cuidadosa do diff. O prompt foi ajustado para tratar comandos bloqueados pelo sandbox como `NOT_VERIFIED` (não como falha do processo), e para basear a análise principalmente na leitura do diff quando a execução não for possível. Claude continua sendo responsável por rodar os quality gates de verdade (pytest/vitest/tsc) antes de cada revisão — o Codex é um revisor estático independente, não um substituto disso.

### Decisão sobre formato de saída (nova, final): aceitar o formato nativo do Codex
O `codex review` não obedece um template Markdown rígido — na 1ª rodada devolveu prosa+lista com prioridade P1/P2; na 2ª rodada devolveu **JSON estruturado** (`findings[]`, `overall_correctness`, `overall_explanation`). O prompt foi ajustado para não exigir cabeçalhos exatos, só garantir que os elementos essenciais apareçam em algum lugar (veredito explícito, evidências executadas, critérios de aceitação, findings com severidade). **Claude deve estar preparado para parsear tanto Markdown quanto JSON ao ler os relatórios.**

### Demais decisões (2, 3, 5, 6, 7 do desenho original) permanecem válidas.

---

## 🎯 Findings reais encontrados e corrigidos (2 rodadas)

**Rodada 1** (commit `eff1199`, revisão completa VS-01–07):
1. HIGH — `LOAN` não creditava o principal recebido como renda → corrigido em `appliers.py::apply_loan` (evento de renda "loan_disbursement").
2. HIGH — custo total de financiamento não escalava custos recorrentes pela duração → corrigido em `engine.py::_total_cost` (multiplica por `installments`).
3. HIGH — parâmetros de decisão sem validação (500 em vez de 422) → corrigido com `src/domain/decisions/validation.py::validate_decision_parameters`, chamado no use case, convertido para 422 no router.
4. HIGH — `scenario_override` não persistido com a simulação → corrigido: `ScenarioOverride.to_dict()` + persistido em `parameters["scenario_override"]` no use case.
5. MEDIUM (pré-existente, não corrigido nesta rodada) — `resourceConfigs.ts` com `any` quebra `npm run lint`. Fica registrado como dívida técnica conhecida.

**Rodada 2** (commit `28f0a58`, revisão só das correções acima):
6. P2/MEDIUM — o novo campo `expense_reduction_capacity` no `DecisionForm` aceitava valores fora de 0–1, gerando 500 em vez de 422 → corrigido: router captura `InvalidPercentageError`/`InvalidMoneyError`/`InvalidOperation` na construção do `ScenarioOverride` e retorna 422; input do form ganhou `min={0} max={1}` como reforço de UX.

Todos os 6 findings reais (5 HIGH/MEDIUM da rodada 1 relevantes à VS-07 + 1 da rodada 2) foram corrigidos, exceto o lint pré-existente (fora do escopo da VS-07, registrado como dívida técnica separada). Testes: 133 backend / 23 frontend passando após todas as correções.

---

## ❌ Lições / Achados Técnicos (críticos para não repetir)

1. **Sempre testar a combinação exata de flags antes de assumir que funciona** — `--help` não deixa claro quais combinações são mutuamente exclusivas.
2. **`codex review` não tem formato de saída fixo** — varia entre prosa/Markdown e JSON estruturado dependendo da execução. O prompt deve pedir os elementos essenciais, não um template rígido, e Claude deve saber ler ambos os formatos.
3. **`--sandbox` só existe em `codex`/`codex exec`, não em `codex review`** — checar `<subcomando> --help` especificamente.
4. **O harness já provou valor real duas vezes seguidas**, inclusive achando um bug introduzido pela própria correção anterior — reforça que vale a pena manter o ciclo "corrige → commita → revalida" até o relatório não trazer findings novos, antes de apresentar a slice como pronta ao usuário.
5. Repositório sem histórico de commits granulares é incompatível com review baseado em diff de commit — commit por slice (ou por rodada de correção) é obrigatório para o harness funcionar.

---

## 📚 Pendências conhecidas (não resolvidas ainda, deliberadamente adiadas)

- **Não fixar ainda `gpt-5.6-terra` + `reasoning_effort=high` como padrão definitivo** — um documento de acompanhamento do usuário (`docs/features/ajustes-meta-harness.md`) sugere medir pelo menos mais 2 execuções (uma slice pequena, uma média) antes de comprometer essa combinação permanentemente, com foco em quota consumida/duração/quantidade de findings úteis por revisão, não em custo em dólar (que não existe aqui — auth via ChatGPT, não API key).
- O mesmo documento sugere um script `normalize-codex-review.py` para padronizar deterministicamente a saída do Codex (Markdown ou JSON) num relatório único, preservando o raw em `raw/`. **Não implementado ainda** — presente como sugestão a validar com o usuário antes de construir, não fazia parte do pedido explícito desta rodada ("faça os dois" = corrigir findings + ajustar decisões de sandbox/formato).
- Dívida técnica pré-existente identificada pelo Codex (não da VS-07): `apps/web/src/features/onboarding/resourceConfigs.ts` com `ResourceStepConfig<any>` quebra `npm run lint`; erros de `tsc --noEmit` em `ProjectionChart.tsx`, `FragilityList.tsx`, `ProfileStep.tsx`, `ResourceStepForm.tsx` (já conhecidos, documentados em `project_overview`).

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_20260724_150000` (deletada)
- Documentos de origem: `docs/features/meta-harness.md` (proposta inicial), `docs/features/ajustes-meta-harness.md` (ajustes pós-piloto, trazido pelo usuário)
- Codex CLI: v0.145.0, autenticado via ChatGPT (sem custo em $ por chamada, consome quota do plano)
- Commits: `eff1199` (checkpoint VS-01–07), `28f0a58` (fixes rodada 1), commit seguinte (fix rodada 2 — validação de scenario_override)
- Relatórios: `.meta-harness/reports/codex-review-20260724-102956.md` (rodada 1), `.meta-harness/reports/codex-review-20260724-112849.md` (rodada 2, formato JSON)
- Repo: `D:\IA Projects\gemeo-financeiro`, branch `master`

---

## 🚦 Próximo Passo

Reportar ao usuário: 2ª rodada limpa (achou e já corrigi o único finding novo). Perguntar se quer que eu rode uma 3ª rodada para confirmar que está tudo limpo agora, e decidir sobre as pendências (medições adicionais de modelo, normalize-codex-review.py) antes de seguir para VS-08.
