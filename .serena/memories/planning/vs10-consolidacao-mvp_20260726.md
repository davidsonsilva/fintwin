# Plano: VS-10 — Consolidação do MVP

## 📅 Criado em: 2026-07-26

## 🎯 Status: ✅ CONCLUÍDA (Meta Harness APPROVED na 1ª rodada)

---

## 📋 Resumo Executivo

VS-10 é a última slice do MVP FinTwin AI (Spec seção "VS-10" + critérios de aceite seção 31). Diferente das slices anteriores, não adiciona domínio novo — consolida o que já existe (VS-01 a VS-09, todas aprovadas pelo Meta Harness) em um produto demonstrável e documentado. Entrega: 1 fluxo E2E automatizado via Playwright + axe-core, hardening pontual de segurança (rate limit no agente), README.md na raiz reescrito (setup Windows/Docker + limitações + roteiro de demonstração reprodutível).

Dos 25 critérios de aceite da seção 31, os já cobertos por slices anteriores (#1-21, #26) não foram retrabalhados; o foco foi fechar #22 (testes automatizados — parte E2E), #23 (premissas/limitações), #24 (demonstração ponta a ponta) e #25 (README Windows/Docker).

**Meta Harness aprovou na primeira rodada** (`APPROVED`, commit `051f325`, 0 findings novos) — único ponto notado pelo Codex foi o erro de `tsc`/build em `ProjectionChart.tsx:99` (pré-existente, já na baseline `vs10-before.json`, não é regressão desta slice).

---

## 🎯 Objetivo

Fechar o MVP como entregável real: qualquer pessoa consegue clonar o repo, subir via Docker Compose, seguir um roteiro documentado e ver o produto funcionando ponta a ponta, com riscos de segurança/acessibilidade conhecidos endereçados ou documentados, e com um teste automatizado que protege esse fluxo de regressões futuras.

---

## 🏗️ Arquitetura / Abordagem Final

- **E2E**: Playwright (`apps/web/e2e/critical-flow.spec.ts`) — onboarding via seed demo → dashboard → simular decisão → comparar antes/depois → detectar fragilidades → gerar e aprovar plano preventivo. Roda contra a stack Docker Compose local. **Não passa pelo agente conversacional** (evita não-determinismo de chamada real à Anthropic).
- **Segurança**: CORS já estava restrito a `localhost:3000`; nenhuma chamada de log/print expõe `ANTHROPIC_API_KEY`; FastAPI sem `--reload`/debug (sem stack trace exposto); rate limit em memória (`RateLimiter`, janela fixa por IP, 20 req/60s) adicionado só em `POST /agent/messages`.
- **Acessibilidade**: `@axe-core/playwright` integrado ao E2E, 4 pontos varridos, 3 violações reais corrigidas (`aria-label` em `SelectTrigger`s sem label pareado).
- **Documentação**: `README.md` reescrito por completo na raiz (existia um README obsoleto da VS-01).
- **Seed**: `data/demo/` reaproveitado (já existia).

---

## ✅ Decisões Tomadas

### Decisão 1: Escopo de E2E — 1 fluxo crítico, não cobertura ampla
Playwright cobrindo só onboarding→dashboard→simulação→fragilidades→plano preventivo — maior cobertura de camadas com menor custo de manutenção numa slice de fechamento.

### Decisão 2: Segurança — hardening pontual, sem auth de usuário
Nenhum critério de aceite da seção 31 exige autenticação; adicionar login seria overengineering fora de escopo.

### Decisão 3: Acessibilidade — auditoria automatizada rigorosa (axe-core)
Nível mais rigoroso escolhido pelo usuário nas perguntas de planejamento.

### Decisão 4: Documentação — README único na raiz com limitações embutidas
Sem arquivo `LIMITATIONS.md` separado — README único cobre tudo.

### Decisão 5: Demonstração ponta a ponta é um roteiro manual, não o teste Playwright
Propósitos diferentes: validação humana visual vs. proteção automatizada contra regressão.

---

## ❌ Lições das Correções (OURO!)

### Correção 1: Simulação normal não tem passo de "confirmar"
- **Erro que cometi**: o plano assumia (por analogia com o agente da VS-09) que toda simulação exige confirmação explícita.
- **Realidade**: `DecisionForm.tsx` → `POST /simulations` persiste imediatamente ao submeter; não há botão de confirmar na tela de comparação. O padrão propose→confirm é exclusivo do agente conversacional (VS-09).
- **Como aplicar**: não presumir confirmação em fluxos de simulação normal — é side-effect imediato no submit.

### Correção 2: `<Select>` (Base UI) sem `id`+`<Label htmlFor>` não tem nome acessível
- **Achado real do axe-core**: 3 `SelectTrigger` sem `aria-label` nem `id`/`htmlFor` pareado (`ProjectionChart.tsx` — cenário/horizonte, `FragilityList.tsx` — severidade, `PlanCard.tsx` — acompanhamento). Os que já usavam `id={field.name}` + `<Label htmlFor>` (`DecisionForm.tsx`, `ResourceStepForm.tsx`) já eram acessíveis.
- **Correção**: `aria-label` direto no `SelectTrigger` para os 3 casos.
- **Regra para componentes futuros**: todo `SelectTrigger` do design system precisa de `<Label htmlFor>` pareado via `id` OU `aria-label` direto — nunca depender só do texto do `SelectValue`.

### Correção 3: Fragilidades exigem detecção explícita antes de gerar planos
- `GET /fragilities` só lista achados já persistidos; `POST /fragilities/detect` precisa ser chamado primeiro (botão "Detectar fragilidades"). `POST /plans/generate` sem detecção prévia retorna `201` com lista vazia (não erro) — mascara o problema até investigar a resposta da API diretamente.
- **Como aplicar**: sempre detectar fragilidades explicitamente antes de gerar planos, tanto no roteiro de demonstração quanto em qualquer E2E futuro.

### Correção 4: `next dev` no Docker é lento na primeira navegação a cada rota
- `apps/web/Dockerfile` roda `npm run dev` (não build de produção) — compilação sob demanda estourava o timeout padrão de 5s do Playwright.
- **Correção**: `timeout: 60_000` e `expect.timeout: 15_000` no `playwright.config.ts`.
- **Como aplicar**: qualquer E2E futuro contra esta stack Docker precisa do mesmo timeout generoso — não é flakiness real.

### Correção 5 (processo): usar `Write`/`Read`, não heredoc via Bash, para criar arquivos
- Usuário interrompeu uma tentativa de `cat > arquivo << EOF` no Bash tool para um spec de debug. Preferir sempre `Write`/`Edit` a heredocs em Bash, mesmo para arquivos temporários.

### Achado do próprio Meta Harness (não uma correção, mas confirma a robustez do gate)
- O Codex rodou `next build` (build de produção) dentro do sandbox read-only e reproduziu o mesmo erro de `tsc` já documentado na baseline (`ProjectionChart.tsx:99`, `TS2322` no `formatter` do `Tooltip` do Recharts) — corretamente classificado como `PRE_EXISTING_FAILURE`, não bloqueou a aprovação. `pytest`/`vitest`/`playwright` ficaram `NOT_VERIFIED` no sandbox (venv Python inválido, sem permissão de escrita em cache/Temp/Docker) — esperado e já coberto pelo protocolo do harness (Claude já havia rodado as 3 suítes localmente com sucesso antes do gate).

---

## 🔧 Estado Final

### Critérios de Aceite — todos atendidos
- [x] #22 testes automatizados reforçado com E2E real.
- [x] #23 premissas e limitações documentadas no README.
- [x] #24 demonstração ponta a ponta documentada como roteiro reproduzível.
- [x] #25 README Windows/Docker existe na raiz.
- [x] Teste Playwright passa localmente contra Docker Compose (2 execuções consecutivas, sem flakiness).
- [x] axe-core sem violações críticas/sérias (3 achados reais corrigidos).
- [x] 189 backend (185 + 4 novos do rate limiter) + 34 frontend passando, sem regressão.
- [x] **Meta Harness APPROVED** — commit `051f325`, base `c84b645`, 0 findings novos.

### Arquivos alterados/criados (commit `051f325`)
- `apps/web/e2e/critical-flow.spec.ts`, `apps/web/playwright.config.ts` (novos)
- `apps/web/vitest.config.ts` (+exclude e2e/**)
- `apps/web/package.json`/`package-lock.json` (+@playwright/test, @axe-core/playwright, script test:e2e)
- `apps/web/src/features/dashboard/ProjectionChart.tsx`, `.../fragility/FragilityList.tsx`, `.../preventive-plans/PlanCard.tsx` (+aria-label)
- `apps/api/src/interfaces/http/rate_limit.py` (novo), `.../routers/agent.py` (+dependency)
- `apps/api/tests/unit/test_rate_limit.py` (novo, 4 testes)
- `README.md` (reescrito)
- `.meta-harness/contracts/current-slice.md`, `acceptance-criteria.md` (regenerados para VS-10)
- `.meta-harness/baselines/vs10-before.json` (capturado via `git stash` do estado limpo pós-VS-09)

### Processo do Meta Harness usado (para referência futura)
1. `git stash push -u` (isolar mudanças da VS-10)
2. `bash scripts/capture-baseline.sh vs10` (captura pytest/tsc/lint/vitest do estado limpo)
3. `git stash pop` (restaurar mudanças)
4. Commit de checkpoint (`051f325`)
5. `bash scripts/validate-step.sh HEAD .meta-harness/baselines/vs10-before.json`
6. Resultado: `APPROVED` na 1ª rodada — sem necessidade de correções.

---

## 📚 Pendências conhecidas (não bloqueiam o MVP, adiadas por decisão prévia)
- Auth de usuário, comparar cenários via agente, gerar plano preventivo via agente, navegação guiada pelo agente — fora do escopo dos critérios de aceite / adiadas por decisão da VS-09.
- Dívida técnica pré-existente de `tsc`/`lint` (5 erros já documentados desde VS-07/VS-08) — não é regressão desta slice, não corrigida.
- Rate limit é em memória, por processo — não distribuído; documentado como limitação no README.

---

## 📚 Contexto e Referências
- Spec: seção "VS-10" (linha ~1590) e seção 31 "Critérios de Aceitação do MVP" (linha ~1607)
- Memórias relacionadas: `project_overview`, `planning/vs09-agente-conversacional_20260725`, `planning/meta-harness_20260724`
- Commit de checkpoint: `051f325` (base `c84b645`)
- Relatório Meta Harness: `.meta-harness/reports/codex-review-20260727-072421.md`

---

## 🚦 Próximo Passo
MVP completo (VS-01 a VS-10). Próxima sessão: atualizar `project_overview` marcando o MVP como concluído (todos os 25 critérios da seção 31) e decidir com o usuário o que vem depois (polish visual `/ui-material3`, ou funcionalidades pós-MVP).
