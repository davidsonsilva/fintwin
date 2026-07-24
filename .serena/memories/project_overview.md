
# FinTwin AI — Project Overview (atualizado 2026-07-24)

## Status geral
- **VS-01 a VS-08**: ✅ completas e verificadas.
- **Próxima slice**: **VS-09 — Agente conversacional** (painel lateral, schemas de intenção, tool calling, explicações fundamentadas, atualização do dashboard, tratamento de dados insuficientes, histórico básico). Ainda não iniciada.

## VS-08 (Planos Preventivos) — Back-end (completo)
- `src/domain/preventive_plans/` (antes só tinha `PreventivePlan` como placeholder) ganhou:
  - `validation.py::PLAN_STATUS_TRANSITIONS`/`validate_status_transition` — ciclo de status da Spec seção 6.7: `proposed→{approved,rejected}`, `approved→{in_progress,cancelled}`, `in_progress→{completed,cancelled}`; demais são terminais.
  - `generator.py::generate_preventive_plans(...)` — 11 templates (1 por código de fragilidade da VS-06: `INCOME_CONCENTRATION`, `ESSENTIAL_EXPENSE_RATIO`, `DEBT_SERVICE_RATIO`, `RECURRING_CREDIT_FOR_ESSENTIALS`, `PROJECTED_RESERVE_DECLINE`, `CONCENTRATED_DUE_DATES`, `PROJECTED_DEFICIT_90_DAYS`, `RESERVE_BELOW_THREE_MONTHS`, `UNPROVISIONED_ANNUAL_EXPENSE`, `UNCOVERED_FUTURE_INSTALLMENTS`, `INCOMPATIBLE_GOAL`). Reaproveita `FragilityContext` (`src.domain.fragility.detector`) recomputado a partir de projeção+autonomia — nunca faz parsing de strings da `evidence` persistida para valores monetários, só para rótulos descritivos. Cada ação usa `_money_dict()` (mesmo padrão de `decisions/engine.py::_money_dict`) para serializar `expected_monthly_impact` como `{amount, currency}`, não string crua.
  - **Regra de não-duplicação**: só gera plano novo para um `risk_code` sem plano em status não-terminal (`proposed`/`approved`/`in_progress`) já existente para o perfil — planos terminais (`rejected`/`completed`/`cancelled`) permitem regeneração. Confirmado via curl real: risk codes terminais voltaram a gerar propostas novas, o `proposed` não foi duplicado.
- **Persistência nova** (4ª tabela desde VS-02): `PreventivePlanModel` (`preventive_plans`), migração Alembic `cc81d6a213fa`. `actions`/`expected_result` embutidos como JSON (mesma decisão consciente da VS-07 para `Simulation` — a lista de "entidades mínimas" da Spec seção 24, incluindo `preventive_plan_actions` como tabela separada, é tratada como catálogo geral, não mandato rígido).
- Endpoints (Spec seção 18.10, literal): `POST /profiles/{id}/plans/generate`, `GET /profiles/{id}/plans`, `PATCH /plans/{id}/status`.
- 168 testes de backend passando no total (37 novos: generator, validation, use cases, integração).

## VS-08 — Front-end (completo)
- `src/features/preventive-plans/`: `types.ts` (inclui `RISK_CODE_LABELS`/`STATUS_LABELS` — mesmo padrão de `DECISION_LABELS` da VS-07), `api.ts` (`generate`/`list`/`updateStatus`), `PlanCard.tsx` (ações + impacto esperado, botões Aprovar/Rejeitar quando `proposed`, seletor de acompanhamento quando `approved`/`in_progress`), `PreventivePlanList.tsx`.
- Rota `dashboard/[profileId]/plans/page.tsx`; botão "Planos preventivos" adicionado ao lado de "Simular decisão" no dashboard.
- `apiClient` ganhou método `patch` (só tinha get/post/put/delete) — necessário para `PATCH /plans/{id}/status`.
- 37 testes de frontend passando no total (7 novos: PlanCard, PreventivePlanList).

## Meta Harness aplicado pela primeira vez como gate operacional (não piloto) nesta slice
- Fluxo seguido à risca: `capture-baseline.sh` → implementar → commit checkpoint → `validate-step.sh` → corrigir → revalidar.
- **1ª rodada: REJECTED** (4 findings). Achados reais:
  1. HIGH (falso-positivo de processo, não bug de código): os contratos `.meta-harness/contracts/current-slice.md`/`acceptance-criteria.md` ainda descreviam a VS-07 — eu esqueci de regenerá-los para a VS-08 antes de rodar o gate, então o Codex viu "trabalho da VS-08 dentro do contrato da VS-07" e rejeitou por scope creep. **Lição**: regenerar os contratos é parte obrigatória do fluxo por slice, não opcional — adicionar isso explicitamente ao checklist mental antes de rodar `validate-step.sh`.
  2. HIGH real: `RESERVE_BELOW_THREE_MONTHS` calculava o **gap total** (`shortfall_months × essential_expenses_monthly`) mas rotulava como `expected_monthly_impact`/"por mês" — prometia uma contribuição mensal só do tamanho do déficit total, não dividida por um período de aporte. Corrigido dividindo pelo período de vencimento (`_FUNDING_PERIOD_MONTHS = due_offset_days/30 = 3`).
  3. MEDIUM real: `GET /plans?status=X` com valor inválido gerava 500 (`PlanStatus(status)` sem try/except) em vez de 422.
  4. MEDIUM real: downgrade da migração Alembic não removia o enum `planstatus` do Postgres, causando erro de tipo duplicado num upgrade posterior — mesmo padrão de bug pré-existente (não corrigido) na migração `fragility_findings` (enum `severity`), mas só corrigi a migração nova (fora de escopo tocar a antiga).
- **2ª rodada (após corrigir os 4): APPROVED_WITH_WARNINGS**, 1 finding novo MEDIUM: o arredondamento `ROUND_HALF_UP` do `Money` em 3 parcelas mensais podia somar menos que o gap total quando o valor não dividia exatamente por 3 centavos (ex.: gap R$2000,02 → 3×R$666,67 = R$2000,01, faltando 1 centavo). Corrigido com `ROUND_UP` explícito no cálculo da parcela mensal (garante que 3 parcelas sempre cobrem o total).
- **3ª rodada (após o fix de arredondamento): APPROVED, 0 findings.** Gate fechado.
- Reforça a lição já registrada na `planning/meta-harness_20260724`: nunca aceitar a primeira versão de um cálculo financeiro sem considerar casos-limite de arredondamento quando ele é dividido em parcelas.

## Verificação manual confirmada nesta sessão (VS-08)
- Migração `cc81d6a213fa` aplicada em Postgres real via `docker compose exec api python -m alembic upgrade head` (após rebuild dos containers `api`/`web` com `docker compose up -d --build`).
- Fluxo real via curl: detectar fragilidades → gerar 3 planos (`INCOME_CONCENTRATION`, `RESERVE_BELOW_THREE_MONTHS`, `UNPROVISIONED_ANNUAL_EXPENSE`) → aprovar um → mover para `in_progress` → `completed` → rejeitar outro → transição inválida (`rejected→approved`) retornou 422 → regenerar não duplicou o `proposed` ainda ativo, mas recriou propostas para os 2 risk codes que viraram terminais (`completed`/`rejected`) — comportamento exatamente como projetado.
- `/dashboard/{profileId}` e `/dashboard/{profileId}/plans` respondem 200 sem erros nos logs do container `web`.
- **Falso alarme de encoding**: `python -m json.tool` no Windows/Git Bash exibe acentos como mojibake (`reforÃ§ar`) por causa do stdout codec do console, não é um bug real — confirmado re-decodificando a mesma resposta com `python -c "...print(...)"`, que mostrou "reforçar"/"segurança"/"Salário" corretos. **Lição**: ao depurar encoding via curl+python no Windows, preferir `python -c "print(...)"` a `python -m json.tool` para não se enganar com um artefato de exibição do console.

## Armadilhas confirmadas neste projeto (cumulativo)
- `apps/web/AGENTS.md`: Next.js 16.2.11 tem breaking changes reais vs. treinamento (`params` é `Promise`).
- shadcn/ui usa Base UI (`@base-ui/react`): usar `render={<Link>...</Link>}` **e** `nativeButton={false}` ao invés de `asChild`. `Select.onValueChange` do Base UI entrega `string | null` (não só `string`) — tratar o `null` explicitamente ao gravar em estado tipado como `string`.
- CORS precisa de `CORSMiddleware` explícito no FastAPI.
- Dockerfile da API precisa copiar `alembic.ini`/`alembic/`; `data/demo/` precisa de volume mount + `DEMO_DATA_DIR`.
- Pydantic serializa `Decimal` como **string** no JSON — DTOs TypeScript usam `string` para todos os campos monetários/percentuais/meses; valores monetários usam sempre `{amount, currency}` (padrão `MoneyDto`/`_money_dict`), nunca uma string crua de valor sem moeda.
- Migração Alembic gerada via SQLite temporário (`_autogen_tmp.db`) precisa ser aplicada manualmente no Postgres de dev depois (`docker compose exec api python -m alembic upgrade head`) — repetido em toda slice com tabela nova (VS-06, VS-07, VS-08). **Nova lição da VS-08**: o `downgrade()` autogerado não remove enums do Postgres — adicionar `sa.Enum(name='...').drop(op.get_bind(), checkfirst=True)` manualmente sempre que a tabela nova tiver uma coluna `Enum`.
- `calculate_autonomy` (VS-05) mede ativos/despesas, é **independente de renda e de serviço de dívida** — decisões/fragilidades que só afetam renda ou dívida (perda de renda, redução salarial, `DEBT_SERVICE_RATIO`, `UNCOVERED_FUTURE_INSTALLMENTS`) não mudam `autonomy_change_months`/`autonomy_delta_months`; o efeito aparece só no fluxo de caixa (déficit projetado). Já são 3 achados independentes (VS-05, VS-07, VS-08) confirmando o mesmo comportamento de design — documentar como `None`/limitação em vez de inventar uma fórmula.
- **Cálculos financeiros divididos em parcelas iguais precisam arredondar para cima (`ROUND_UP`), não `ROUND_HALF_UP`** — senão a soma das parcelas pode ficar abaixo do total prometido por causa de centavos não representáveis exatamente na divisão. Achado pelo Meta Harness na VS-08 (`RESERVE_BELOW_THREE_MONTHS`); vale para qualquer parcelamento futuro de valor calculado (ex.: planos preventivos com múltiplas ações, custos futuros).
- Contratos do Meta Harness (`.meta-harness/contracts/*.md`) **precisam ser regenerados a cada nova slice antes de rodar `validate-step.sh`** — esquecer isso gera uma rejeição falsa de "scope creep" contra o contrato da slice anterior.
- `npx tsc --noEmit` no front-end já acusa alguns erros pré-existentes (recharts `Tooltip formatter` typing, Base UI `Select.onValueChange` em `ProfileStep`/`FragilityList`, zod resolver typing) que não bloqueiam `npm test`/build — não são regressões novas, mas checar `tsc` ao adicionar componentes com recharts/Select para não somar mais erros.

## Pendências conhecidas (adiadas por decisão do usuário)
- Polish visual de todo o front-end (onboarding + dashboard) com `/ui-material3` — sessão dedicada futura, não bloqueia novas slices.
- Medir mais 2 execuções do Meta Harness (`gpt-5.6-terra`+`reasoning_effort=high`) antes de fixá-lo como padrão definitivo — ver `planning/meta-harness_20260724`.

## Tasks trackeadas (Task tool)
IDs #9–#19 (VS-02), #20–#26 (VS-03), #27–#37 (VS-04), #38–#46 (VS-05), #47–#56 (VS-06), #57–#69 (VS-07), #86–#93 (VS-08) — todas `completed`.

## Próxima sessão
1. Iniciar VS-09 — Agente conversacional: ler Spec seção 6.8 (agente visual), seção 18.11 (`POST /profiles/{id}/agent/messages`, retorno com resposta textual + ferramentas acionadas + referências aos cálculos + componentes a atualizar + perguntas pendentes + limitações). Seguir o processo padrão (plano → decisões técnicas → critérios de aceite → implementar → testar → demo real → Meta Harness gate → memória → próxima slice). Usar `capture-baseline.sh`/`validate-step.sh` desde o início, e **regenerar os contratos do harness antes de rodar o gate** (lição da VS-08).
2. (Quando o usuário pedir) Polish visual via `/ui-material3` sobre onboarding + dashboard.
