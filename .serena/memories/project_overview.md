
# FinTwin AI — Project Overview (atualizado 2026-07-24)

## Status geral
- **VS-01 a VS-07**: ✅ completas e verificadas.
- **Próxima slice**: **VS-08 — Planos preventivos** (gerador por regras a partir de fragilidades/simulações/metas/fluxo projetado, cards, aprovação/rejeição, acompanhamento, impacto esperado). Ainda não iniciada.

## VS-07 (Simulador de Decisões) — Back-end (completo)
- `src/domain/decisions/` (antes só tinha `FinancialGoal`/`Simulation` como placeholder) ganhou:
  - `scenario_override.py::ScenarioOverride` — cenário personalizado (Spec 10.4), todos os campos opcionais, preenche defaults do cenário provável quando omitidos.
  - `context.py::DecisionContext` — bundle das 6 listas de entidades (contas/rendas/obrigações/dívidas/metas/eventos), com `.copy()` para não mutar o original.
  - `types.py::DECISION_TYPES` — registro estático dos 9 tipos de decisão da seção 12.1 (mesmo padrão do `RULES` da fragilidade), cada um com applier próprio em `appliers.py`.
  - `appliers.py` — 9 funções puras (`apply_cash_purchase`, `apply_installment_purchase`, `apply_financing`/`apply_loan` (loan reaproveita financing com down_payment=0), `apply_income_loss`/`apply_salary_reduction` (ambos via `_apply_income_adjustment`, que usa `dataclasses.replace` no `IncomeSource` para reduzir e depois retomar a renda), `apply_new_recurring_expense`, `apply_new_goal`, `apply_reserve_increase`). Nenhuma exigiu mudança no motor de projeção (VS-04) ou autonomia (VS-05) — só sintetizam novas entidades (`Debt`, `FinancialObligation`, `FinancialEvent`, `IncomeSource` modificada, `FinancialGoal`).
  - `engine.py::simulate_decision(...)` — roda baseline (cenário provável, sem decisão) e simulado (decisão aplicada + cenário customizado se houver) via `project_cashflow`/`calculate_autonomy` reaproveitados; calcula `impact` (autonomy_delta_months, closing_balance_delta, new_first_deficit_period, goal_delay_months usando a meta de maior prioridade) e `total_cost` (seção 12.3, só para FINANCING/LOAN/INSTALLMENT_PURCHASE).
  - **Achado confirmado nos testes**: perda de renda (`INCOME_LOSS`) não muda `autonomy_delta_months` — `calculate_autonomy` mede ativos/despesas (burn), não depende de renda; o impacto de perda de renda aparece só como déficit projetado no fluxo de caixa. Mesmo padrão já observado na VS-05 com o cenário `income_loss`.
  - **Custo de oportunidade do financiamento NÃO é calculado** — decisão consciente: a Spec não define a fórmula quando há taxa informada (só diz "poderá ser calculada"), documentado como limitação em `assumptions` em vez de inventar fórmula.
- **Persistência nova** (terceira tabela desde VS-02): `SimulationModel` (`simulations`), migração Alembic `0a457ffa0a4d`. Ao contrário da fragilidade (que substitui snapshot), cada `/simulations` **cria um novo registro** — histórico acumulado, porque a Spec pede explicitamente histórico de simulações (seção 12/18.9).
- Endpoints (Spec seção 18.9, literal): `POST/GET /profiles/{id}/simulations`, `GET/DELETE /simulations/{id}`.
- 120 testes de backend passando no total (22 novos: appliers, engine, scenario_override, integração).

## VS-07 — Front-end (completo)
- `src/features/simulation/`: `types.ts`, `api.ts`, `decisionFields.ts` (configuração declarativa dos campos por tipo de decisão + `buildParameters` que monta o payload, incluindo agrupamento de `recurring_costs`/`one_off_costs` do financiamento), `DecisionForm.tsx` (form único com campos condicionais pelos 9 tipos + seção opcional de cenário personalizado), `SimulationComparison.tsx` (cards base vs. simulado + gráfico de barras comparando saldo final/menor saldo, já que a API só persiste resumo escalar da projeção, não a série mês a mês — simplificação consciente do plano original que previa "sobrepor curvas", pois isso exigiria persistir os `periods` completos), `SimulationHistory.tsx`.
- Rotas `dashboard/[profileId]/simulations/page.tsx` (form + histórico) e `.../simulations/[simulationId]/page.tsx` (comparação), seguindo o padrão Server Component (`await params`) + Client Component filho para hooks (`useRouter`, `useQuery`).
- Card "Simular decisão (em breve)" do dashboard virou link real.
- **Bug pego pelo teste**: `SimulationComparison` inicialmente desestruturava `impact`/`total_cost`/`assumptions` de `simulation` em vez de `simulation.simulated_result` (esses campos só existem dentro do `simulated_result`, não no nível raiz) — corrigido antes de reportar a slice como pronta.
- 23 testes de frontend passando no total (6 novos: DecisionForm, SimulationComparison, SimulationHistory).

## Verificação manual confirmada nesta sessão (VS-07)
- Migração `0a457ffa0a4d` aplicada em Postgres real via `docker compose exec api python -m alembic upgrade head`.
- Fluxo real via curl: compra parcelada (entrada+parcelas), delta de saldo e custo total corretos; listagem/detalhe/exclusão de simulação funcionando (create→200/201, get→200, delete→204, lista fica vazia depois).
- `/dashboard/{profileId}` e `/dashboard/{profileId}/simulations` respondem 200 sem erros nos logs do container `web`.
- Diff review final: domínio sem imports de framework; sem termos de VS-08+ (plano preventivo, agente conversacional) nos arquivos da slice.

## Armadilhas confirmadas neste projeto (cumulativo)
- `apps/web/AGENTS.md`: Next.js 16.2.11 tem breaking changes reais vs. treinamento (`params` é `Promise`).
- shadcn/ui usa Base UI (`@base-ui/react`): usar `render={<Link>...</Link>}` **e** `nativeButton={false}` ao invés de `asChild`. `Select.onValueChange` do Base UI entrega `string | null` (não só `string`) — tratar o `null` explicitamente ao gravar em estado tipado como `string`.
- CORS precisa de `CORSMiddleware` explícito no FastAPI.
- Dockerfile da API precisa copiar `alembic.ini`/`alembic/`; `data/demo/` precisa de volume mount + `DEMO_DATA_DIR`.
- Pydantic serializa `Decimal` como **string** no JSON — DTOs TypeScript usam `string` para todos os campos monetários/percentuais/meses.
- Migração Alembic gerada via SQLite temporário (`_autogen_tmp.db`) precisa ser aplicada manualmente no Postgres de dev depois (`docker compose exec api python -m alembic upgrade head`) — repetido em toda slice com tabela nova (VS-06 e VS-07).
- `calculate_autonomy` (VS-05) mede ativos/despesas, é **independente de renda** — decisões que só afetam renda (perda de renda, redução salarial) não mudam `autonomy_delta_months`; o efeito aparece no fluxo de caixa (déficit projetado), não na autonomia. Já eram 2 achados independentes (VS-05 e VS-07) confirmando o mesmo comportamento de design.
- `npx tsc --noEmit` no front-end já acusa alguns erros pré-existentes (recharts `Tooltip formatter` typing, Base UI `Select.onValueChange` em `ProfileStep`/`FragilityList`, zod resolver typing) que não bloqueiam `npm test`/build — não são regressões novas, mas checar `tsc` ao adicionar componentes com recharts/Select para não somar mais erros (o padrão que funciona: `formatter={(value) => Number(value).toFixed(2)}` em vez de tipar `value: number` diretamente).

## Pendências conhecidas (adiadas por decisão do usuário)
- Polish visual de todo o front-end (onboarding + dashboard) com `/ui-material3` — sessão dedicada futura, não bloqueia novas slices.

## Tasks trackeadas (Task tool)
IDs #9–#19 (VS-02), #20–#26 (VS-03), #27–#37 (VS-04), #38–#46 (VS-05), #47–#56 (VS-06), #57–#69 (VS-07) — todas `completed`.

## Próxima sessão
1. Iniciar VS-08 — Planos preventivos: ler Spec seção 13 (estrutura do plano, ações possíveis) e seção 18.10 (`POST /profiles/{id}/plans/generate`, `GET /profiles/{id}/plans`, `PATCH /plans/{id}/status`). Gerador por regras a partir de fragilidades detectadas (VS-06), simulações (VS-07), metas e fluxo projetado (VS-04). Seguir o processo padrão (plano → decisões técnicas → critérios de aceite → implementar só a slice → testar → demo real → diff review → memória → próxima slice).
2. (Quando o usuário pedir) Polish visual via `/ui-material3` sobre onboarding + dashboard.
