# Slice atual: VS-07 — Simulador visual

> Gerado a partir do plano aprovado em `C:\Users\david\.claude\plans\fancy-jingling-sprout.md` (sessão de 2026-07-24).

> **NOTA PARA ESTA EXECUÇÃO (piloto do Meta Harness)**: o repositório nunca recebeu commits além de um scaffold inicial vazio, então o diff não commitado atual (`--uncommitted`) abrange **todas as slices VS-01 a VS-07**, não só a VS-07. Trate esta execução como uma auditoria de baseline única do projeto inteiro até aqui. A partir da próxima slice, um commit de checkpoint será criado ao final de cada VS, e o escopo voltará a ser apenas a slice em andamento — não repita esta observação como um "finding" de processo, é uma decisão já tomada e aceita pelo usuário.

## Contexto

VS-01 a VS-06 entregaram persistência, onboarding, dashboard, motor de projeção (VS-04), motor de autonomia (VS-05) e radar de fragilidade (VS-06). A VS-07 (Spec seção 12, seção 10.4, seção 18.9) entrega o Simulador de Decisões: o usuário monta uma decisão financeira hipotética (compra, financiamento, perda de renda, nova meta etc.), o sistema compara o cenário-base (estado atual, sem a decisão) com o cenário simulado (com a decisão aplicada) e mostra o impacto (delta de autonomia, delta de saldo final, novo primeiro déficit, atraso de meta). Inclui também o cenário personalizado completo (seção 10.4) e os 9 tipos de decisão da seção 12.1, sem corte de escopo.

Nenhuma mudança foi necessária no motor de projeção (`project_cashflow`, VS-04) nem no motor de autonomia (`calculate_autonomy`, VS-05) — ambos reaproveitados sem alteração.

## Escopo entregue

### Domínio (`apps/api/src/domain/decisions/`)
- `scenario_override.py::ScenarioOverride` — cenário personalizado (seção 10.4).
- `context.py::DecisionContext` — bundle das 6 listas de entidades.
- `types.py::DECISION_TYPES` — registro estático dos 9 tipos de decisão (seção 12.1).
- `appliers.py` — 9 funções puras (`apply_cash_purchase`, `apply_installment_purchase`, `apply_financing`/`apply_loan`, `apply_income_loss`/`apply_salary_reduction`, `apply_new_recurring_expense`, `apply_new_goal`, `apply_reserve_increase`).
- `engine.py::simulate_decision(...)` — baseline vs. simulado, custo total (seção 12.3), impacto (seção 12.2).

### Persistência
- `SimulationModel` (`simulations`), migração Alembic `0a457ffa0a4d`.
- `SimulationRepository` (Protocol + SQLAlchemy), cada `/simulations` cria um novo registro (histórico acumulado).

### Interface HTTP (Spec seção 18.9)
- `POST/GET /api/v1/profiles/{profile_id}/simulations`
- `GET/DELETE /api/v1/simulations/{simulation_id}`

### Front-end (`apps/web`)
- `src/features/simulation/`: `types.ts`, `api.ts`, `decisionFields.ts`, `DecisionForm.tsx`, `SimulationComparison.tsx`, `SimulationHistory.tsx`.
- Rotas `dashboard/[profileId]/simulations/page.tsx` e `.../simulations/[simulationId]/page.tsx`.
- Card "Simular decisão" no dashboard (antes placeholder desabilitado) agora é link real.

## Fora de escopo (não implementado nesta slice)

- Planos preventivos, agente conversacional (VS-08/VS-09).
- Custo de oportunidade do financiamento (fórmula não definida na Spec — documentado como limitação, não inventado).
- Edição de uma simulação existente (Spec só define criar/listar/obter/excluir).
