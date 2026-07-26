
# FinTwin AI — Project Overview (atualizado 2026-07-26)

## Status geral
- **VS-01 a VS-09**: ✅ completas e verificadas (Meta Harness APPROVED em todas).
- **Próxima slice**: **VS-10 — Consolidação do MVP** (testes E2E, melhorias de UX, acessibilidade, documentação, segurança, seed, demonstração ponta a ponta, relatório de limitações). Ainda não iniciada.

## VS-09 (Agente conversacional) — completo, ver `planning/vs09-agente-conversacional_20260725` para o detalhe completo
- Agente via API da Anthropic direta (Claude Haiku 4.5, tool calling nativo, sem LangChain/LangGraph), painel lateral persistente no AppShell (`features/agent/`).
- Tools allowlisted: `get_dashboard_summary`, `get_autonomy`, `list_fragilities` (leitura real) + `propose_simulation` (nunca persiste — só valida via `validate_decision_parameters` reaproveitado da VS-07).
- Fluxo de confirmação em 2 chamadas: `POST .../agent/messages` propõe (não persiste) → `POST .../agent/actions/{id}/confirm` confirma e persiste, **sem nunca voltar a chamar o LLM**.
- Persistência: `conversations` + `agent_messages` (com coluna dedicada `confirmed`, não um campo dentro do JSON — necessário para claim atômico via `UPDATE ... WHERE confirmed=false`).
- 182 testes de backend (11 novos da VS-09) + 34 de frontend (4 novos: `AgentPanel`) passando.
- **Passou por 4 rodadas de Meta Harness** (3 REJECTED com achados reais, 1 APPROVED) — ver lições abaixo, são importantes para qualquer slice futura que mexa em confirmação de ações, migrações, ou isolamento entre perfis.
- **Pendência**: verificação manual real via Docker Compose (critério de aceite #10) não foi executada — Docker não estava disponível no ambiente da sessão de implementação. Rodar antes de considerar a slice fechada para produção (ver memória do plano para o passo a passo).

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

## Meta Harness — lições cumulativas (VS-08 + VS-09)
- Fluxo: `capture-baseline.sh` → implementar → commit checkpoint → `validate-step.sh` → corrigir → revalidar. **Regenerar os contratos (`current-slice.md`/`acceptance-criteria.md`) antes de rodar o gate é obrigatório**, não opcional (esquecer isso gerou uma rejeição falsa de "scope creep" na VS-08).
- **Nunca editar uma migração Alembic já commitada, mesmo dentro da mesma sessão/PR** — o harness trata cada commit como um possível ponto de deploy real. Sempre criar uma migração nova em cima; se precisar ser resiliente a um estado histórico incerto (ex.: um commit anterior já rejeitado que alterou o schema de um jeito diferente), tornar a migração idempotente (checar via `sa.inspect(...).get_columns(...)` antes de `add_column`/`drop_column`) — achado da VS-09.
- **Campos que precisam de garantia atômica/idempotência não devem viver dentro de um blob JSON** — usar coluna dedicada permite `UPDATE ... WHERE coluna=valor` condicional (a única atomicidade real sem lock explícito). Achado da VS-09 (`AgentMessage.confirmed`).
- **Claims atômicos não devem commitar isoladamente** quando o efeito colateral real depende de passos posteriores na mesma operação — deixar tudo na mesma transação do `Session` por request faz uma falha no meio ser recuperável via rollback implícito do `get_session()` em vez de deixar um estado "confirmado" órfão. Achado da VS-09.
- **Cálculos financeiros divididos em parcelas iguais precisam arredondar para cima (`ROUND_UP`), não `ROUND_HALF_UP`** — achado da VS-08 (`RESERVE_BELOW_THREE_MONTHS`), vale para qualquer parcelamento futuro.
- `downgrade()` autogerado do Alembic não remove enums do Postgres — adicionar `sa.Enum(name='...').drop(op.get_bind(), checkfirst=True)` manualmente sempre que a tabela nova tiver uma coluna `Enum`.
- Guards de segurança/validação devem checar o sinal mais específico disponível, não um proxy mais amplo — ex.: `evidence` real (só tools de leitura) é diferente de "alguma tool foi chamada" (`propose_simulation` conta como tool_call mas não é evidência). Achado da VS-09.

## Verificação manual confirmada (VS-08, sessão 2026-07-24)
- Migração `cc81d6a213fa` aplicada em Postgres real via `docker compose exec api python -m alembic upgrade head` (após rebuild dos containers `api`/`web` com `docker compose up -d --build`).
- Fluxo real via curl: detectar fragilidades → gerar 3 planos → aprovar um → mover para `in_progress` → `completed` → rejeitar outro → transição inválida retornou 422 → regenerar não duplicou o `proposed` ainda ativo, mas recriou propostas para os risk codes terminais — comportamento exatamente como projetado.
- **Falso alarme de encoding**: `python -m json.tool` no Windows/Git Bash exibe acentos como mojibake por causa do stdout codec do console, não é um bug real — preferir `python -c "print(...)"` para não se enganar com um artefato de exibição do console.

## Armadilhas confirmadas neste projeto (cumulativo)
- `apps/web/AGENTS.md`: Next.js 16.2.11 tem breaking changes reais vs. treinamento (`params` é `Promise`).
- shadcn/ui usa Base UI (`@base-ui/react`): usar `render={<Link>...</Link>}` **e** `nativeButton={false}` ao invés de `asChild`. `Select.onValueChange` do Base UI entrega `string | null` (não só `string`) — tratar o `null` explicitamente ao gravar em estado tipado como `string`.
- CORS precisa de `CORSMiddleware` explícito no FastAPI.
- Dockerfile da API precisa copiar `alembic.ini`/`alembic/`; `data/demo/` precisa de volume mount + `DEMO_DATA_DIR`.
- Pydantic serializa `Decimal` como **string** no JSON — DTOs TypeScript usam `string` para todos os campos monetários/percentuais/meses; valores monetários usam sempre `{amount, currency}` (padrão `MoneyDto`/`_money_dict`), nunca uma string crua de valor sem moeda.
- Migração Alembic gerada via SQLite temporário (`_autogen_tmp.db`) precisa ser aplicada manualmente no Postgres de dev depois (`docker compose exec api python -m alembic upgrade head`) — repetido em toda slice com tabela nova (VS-06, VS-07, VS-08, VS-09).
- `calculate_autonomy` (VS-05) mede ativos/despesas, é **independente de renda e de serviço de dívida** — decisões/fragilidades que só afetam renda ou dívida não mudam `autonomy_change_months`; o efeito aparece só no fluxo de caixa. Já são 3 achados independentes (VS-05, VS-07, VS-08) confirmando o mesmo comportamento de design.
- `npx tsc --noEmit` no front-end já acusa 5 erros pré-existentes (ProjectionChart, FragilityList, ProfileStep×2, ResourceStepForm) que não bloqueiam `npm test`/build — não são regressões novas, mas checar `tsc` ao adicionar componentes com recharts/Select para não somar mais erros.
- No Windows/Git Bash, testar migrações Alembic contra SQLite: usar path relativo (`sqlite:///arquivo.db`) em vez de path absoluto estilo `/d/...` (que o Python nativo do Windows não resolve corretamente) — achado da VS-09.
- `.venv` local da API (`apps/api/.venv`) existe e pode ser usado diretamente (`.venv/Scripts/python.exe`) para pytest/scripts sem precisar do Docker — útil quando Docker não está disponível na sessão.

## Pendências conhecidas (adiadas por decisão do usuário)
- Polish visual de todo o front-end (onboarding + dashboard) com `/ui-material3` — sessão dedicada futura, não bloqueia novas slices.
- Medir mais 2 execuções do Meta Harness (`gpt-5.6-terra`+`reasoning_effort=high`) antes de fixá-lo como padrão definitivo — ver `planning/meta-harness_20260724`.
- **Verificação manual real da VS-09 via Docker Compose** (ver seção VS-09 acima) — pendente, ambiente sem Docker rodando na sessão de implementação.
- Comparar cenários via agente, gerar plano preventivo via agente, navegação guiada pelo agente (capacidades da VS-09 adiadas por decisão do plano).

## Tasks trackeadas (Task tool)
IDs #9–#19 (VS-02), #20–#26 (VS-03), #27–#37 (VS-04), #38–#46 (VS-05), #47–#56 (VS-06), #57–#69 (VS-07), #86–#93 (VS-08) — todas `completed`. VS-09 trackeada via tasks internas da sessão (Fase 1-5), não IDs numerados nesta lista.

## Próxima sessão
1. **Verificação manual da VS-09 via Docker** (pendência acima), se o usuário quiser fechar definitivamente antes de avançar.
2. Iniciar VS-10 — Consolidação do MVP: testes E2E, melhorias de UX, acessibilidade, documentação, segurança, seed, demonstração ponta a ponta, relatório de limitações (Spec seção "VS-10"). Seguir o processo padrão (plano → decisões técnicas → critérios de aceite → implementar → testar → demo real → Meta Harness gate → memória → próxima slice).
3. (Quando o usuário pedir) Polish visual via `/ui-material3` sobre onboarding + dashboard.
