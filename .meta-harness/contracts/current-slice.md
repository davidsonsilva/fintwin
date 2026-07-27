# Slice atual: VS-10 — Consolidação do MVP

> Gerado a partir do plano aprovado em `planning/vs10-consolidacao-mvp_20260726` (Serena, sessão de 2026-07-26/27).

## Contexto

VS-01–09 entregaram todo o domínio funcional do MVP (persistência, onboarding, dashboard, projeção, autonomia, radar de fragilidade, simulador de decisões, planos preventivos, agente conversacional). A VS-10 (Spec seção "VS-10", critérios de aceitação seção 31) é a slice de fechamento: **não adiciona domínio novo**, consolida o produto existente em um entregável demonstrável — testes E2E, acessibilidade, segurança, documentação, demonstração ponta a ponta, relatório de limitações.

Escopo deliberadamente limitado: 1 fluxo E2E crítico (não cobertura por slice individual), hardening pontual de segurança (sem autenticação de usuário — fora dos critérios de aceite), auditoria de acessibilidade automatizada (axe-core), README único na raiz.

Nenhuma mudança foi necessária no domínio financeiro, casos de uso de negócio existentes ou contratos HTTP já entregues em slices anteriores.

## Escopo entregue

### Testes end-to-end (`apps/web/e2e/`)
- `critical-flow.spec.ts` — Playwright cobrindo: onboarding via seed de demonstração → dashboard → simular decisão (CASH_PURCHASE) → comparação antes/depois → detectar fragilidades → gerar e aprovar plano preventivo. Roda contra a stack Docker Compose real (não mocka backend, não passa pelo agente conversacional — evita depender de uma chamada real e não-determinística à API da Anthropic num teste automatizado).
- `playwright.config.ts` — timeouts generosos (`timeout: 60_000`, `expect.timeout: 15_000`) porque o container web roda `next dev` (compilação sob demanda na primeira navegação a cada rota, não é flakiness).
- `apps/web/vitest.config.ts` — `exclude: ["e2e/**"]` para o vitest não tentar rodar os specs do Playwright.
- Novos scripts em `apps/web/package.json`: `test:e2e`.

### Acessibilidade (`@axe-core/playwright`, integrado ao E2E acima)
- Varredura em 4 pontos do fluxo crítico (dashboard, detalhe de simulação, radar de fragilidade, planos preventivos), falhando o teste se houver violação `critical`/`serious`.
- 3 violações reais encontradas e corrigidas: `SelectTrigger` (Base UI) sem nome acessível em `ProjectionChart.tsx` (filtros de cenário/horizonte), `FragilityList.tsx` (filtro de severidade), `PlanCard.tsx` (seletor de acompanhamento) — todos ganharam `aria-label` direto no trigger.

### Segurança (`apps/api/src/interfaces/http/`)
- `rate_limit.py` — `RateLimiter` em memória (janela fixa, 20 requisições/60s por IP), aplicado via `Depends` só no endpoint que chama a API paga da Anthropic (`POST /agent/messages`). Não é distribuído (não sobrevive a múltiplos workers/réplicas) — suficiente para mitigar abuso trivial num MVP de instância única, documentado como limitação conhecida.
- Auditoria confirmou sem necessidade de mudança: CORS já restrito a `http://localhost:3000`; nenhuma chamada de log/print expõe `ANTHROPIC_API_KEY`; FastAPI roda sem `--reload`/debug (sem vazamento de stack trace em erros 500).

### Documentação
- `README.md` (raiz) reescrito por completo — havia um README obsoleto da época da VS-01 (falava em "scaffold mínimo", sem dashboard/agente). Novo conteúdo: arquitetura, pré-requisitos, setup Docker Compose (Windows/PowerShell), como rodar cada suíte de testes (pytest/vitest/playwright), roteiro de demonstração ponta a ponta manual e reproduzível, seção "Limitações conhecidas".

## Fora de escopo (não implementado nesta slice)

- Autenticação/autorização de usuário — nenhum critério de aceite da seção 31 exige; `profile_id` continua livre nas rotas (limitação documentada no README).
- Cobertura E2E por Vertical Slice individual — só o fluxo crítico único, por decisão de custo/benefício.
- Qualquer mudança de domínio financeiro, motor de decisões, agente conversacional ou contratos HTTP já entregues.
- Correção da dívida técnica pré-existente de `tsc`/`lint` (erros em `ProjectionChart.tsx`, `ProfileStep.tsx`, `ResourceStepForm.tsx`, `resourceConfigs.ts`) — já documentada em `project_overview` desde a VS-07/VS-08, não é regressão desta slice.
