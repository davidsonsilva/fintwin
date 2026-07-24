# Critérios de aceitação: VS-08 — Planos preventivos

> Extraído da seção "Verificação" do plano aprovado em `C:\Users\david\.claude\plans\fancy-jingling-sprout.md`.

1. **Testes automatizados**: `pytest` cobre `generator.py` (1 teste por código de fragilidade), `validate_status_transition` (transições válidas e inválidas), use cases e endpoints — suíte completa sem regressões.
2. **Migração aplicada**: `alembic upgrade head` aplicado no Postgres real (via `docker compose exec api`), criando a tabela `preventive_plans`.
3. **Testes de frontend**: `npx vitest run` cobre `PlanCard` (aprovar/rejeitar/acompanhamento) e `PreventivePlanList` (gerar/listar).
4. **Fluxo manual real**: via `docker compose`, com o perfil de demonstração, detectar fragilidades, gerar planos, aprovar um plano e movê-lo para `in_progress`/`completed`, rejeitar outro, e confirmar que gerar de novo não duplica planos com `risk_code` já não-terminal.
5. **Pureza de domínio**: `src/domain/preventive_plans/` sem imports de framework (`fastapi`, `sqlalchemy`, `next`).
6. **Sem scope creep**: nenhuma execução financeira real de ação de plano; nenhuma capacidade de VS-09+ (agente conversacional) implementada nesta slice.
7. **Contratos de API**: schema Pydantic (`PreventivePlanResponse`) consistente com o tipo TypeScript (`PreventivePlanDto`), especialmente a serialização de `Decimal` como `{amount, currency}` (mesmo padrão de `MoneyDto` já usado na VS-07).
8. **Endpoints exatos da Spec seção 18.10**: `POST /profiles/{profile_id}/plans/generate`, `GET /profiles/{profile_id}/plans`, `PATCH /plans/{plan_id}/status` — nenhuma rota extra ou divergente.
