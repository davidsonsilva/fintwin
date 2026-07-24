# Slice atual: VS-08 — Planos preventivos

> Gerado a partir do plano aprovado em `C:\Users\david\.claude\plans\fancy-jingling-sprout.md` (sessão de 2026-07-24).

## Contexto

VS-01–07 entregaram persistência, onboarding, dashboard, projeção (VS-04), autonomia (VS-05), radar de fragilidade (VS-06) e simulador de decisões (VS-07). A VS-08 (Spec seção 13, seção 6.7, seção 18.10) entrega Planos Preventivos: a partir das fragilidades já detectadas e persistidas (VS-06), o sistema gera propostas de ação por regras fixas (sem IA generativa), o usuário aprova/rejeita via cards, e o plano é acompanhado através de um ciclo de status (`proposed → approved/rejected → in_progress → completed/cancelled`).

Nenhuma mudança foi necessária nos motores de projeção/autonomia/fragilidade — o gerador só lê as saídas já existentes, reaproveitando `FragilityContext` (`src.domain.fragility.detector`).

## Escopo entregue

### Domínio (`apps/api/src/domain/preventive_plans/`)
- `entities.py::PreventivePlan` — já existia como placeholder, sem mudanças.
- `validation.py` — `PLAN_STATUS_TRANSITIONS` + `validate_status_transition` (transições válidas do ciclo de status da seção 6.7).
- `generator.py::generate_preventive_plans(...)` — 11 templates (1 por código de fragilidade da VS-06), cada um calculando ação + `expected_result` a partir de `FragilityContext` recomputado (projeção + autonomia). Regra de não-duplicação: só gera plano novo para um `risk_code` sem plano não-terminal (`proposed`/`approved`/`in_progress`) já existente.

### Persistência (4ª tabela desde a VS-02)
- `PreventivePlanModel` (`preventive_plans`), migração Alembic `cc81d6a213fa` — `actions`/`expected_result` como JSON embutido (mesma decisão consciente da VS-07 para `Simulation`).
- `PreventivePlanRepository` (Protocol + SQLAlchemy).

### Aplicação (`apps/api/src/application/use_cases/preventive_plan_use_cases.py`)
- `GeneratePreventivePlansUseCase`, `ListPreventivePlansUseCase`, `UpdatePlanStatusUseCase`.

### Interface HTTP (Spec seção 18.10, literal)
- `POST /api/v1/profiles/{profile_id}/plans/generate`
- `GET /api/v1/profiles/{profile_id}/plans`
- `PATCH /api/v1/plans/{plan_id}/status`

### Front-end (`apps/web`)
- `src/features/preventive-plans/`: `types.ts`, `api.ts`, `PlanCard.tsx` (ações, impacto esperado, aprovar/rejeitar, acompanhamento), `PreventivePlanList.tsx`.
- Rota `dashboard/[profileId]/plans/page.tsx`.
- Botão "Planos preventivos" no dashboard, ao lado de "Simular decisão".

## Fora de escopo (não implementado nesta slice)

- Execução financeira real de qualquer ação do plano (Spec seção 5: nenhuma ação financeira é executada no MVP — aprovar só registra estado).
- Agente conversacional (VS-09).
- Edição de ações de um plano já gerado — só a transição de status é editável.
