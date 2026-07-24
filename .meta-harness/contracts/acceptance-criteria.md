# Critérios de aceitação: VS-07 — Simulador visual

> Extraído da seção "Verificação" do plano aprovado em `C:\Users\david\.claude\plans\fancy-jingling-sprout.md`.

1. **Testes automatizados**: `pytest` cobre `appliers.py` (1 teste por tipo de decisão), `ScenarioOverride`, `engine.py::simulate_decision` (baseline vs. simulado, custo total, impacto), use cases, endpoints e repositório — suíte completa sem regressões.
2. **Migração aplicada**: `alembic upgrade head` aplicado no Postgres real (via `docker compose exec api`), criando a tabela `simulations`.
3. **Testes de frontend**: `npx vitest run` cobre formulário (`DecisionForm`), comparação (`SimulationComparison`) e histórico (`SimulationHistory`).
4. **Fluxo manual real**: via `docker compose`, com o perfil de demonstração, simular pelo menos uma compra parcelada (ou financiamento) e uma perda de renda; o `impact` retornado deve fazer sentido (delta de autonomia negativo quando aplicável, novo déficit quando aplicável); a simulação deve aparecer no histórico.
5. **Pureza de domínio**: `src/domain/decisions/` sem imports de framework (`fastapi`, `sqlalchemy`, `next`).
6. **Sem scope creep**: nenhuma lógica financeira duplicada no frontend; nenhuma capacidade de VS-08+ (planos preventivos, agente conversacional) implementada nesta slice.
7. **Contratos de API**: schemas Pydantic (`SimulationRequest`/`SimulationResponse`) consistentes com os tipos TypeScript (`SimulationDto`), especialmente a serialização de `Decimal` como string.
8. **Endpoints exatos da Spec seção 18.9**: `POST/GET /profiles/{profile_id}/simulations`, `GET/DELETE /simulations/{simulation_id}` — nenhuma rota extra ou divergente.
