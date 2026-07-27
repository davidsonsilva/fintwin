
# FinTwin AI — Project Overview (atualizado 2026-07-27)

## Status geral
- **VS-01 a VS-10: ✅ MVP COMPLETO** — todas as 10 Vertical Slices implementadas, testadas e aprovadas pelo Meta Harness (VS-10 aprovada na 1ª rodada). Os 25 critérios de aceitação do MVP (Spec seção 31) estão atendidos.
- **Próximo passo**: nenhuma slice pendente — decidir com o usuário o que vem depois (polish visual `/ui-material3`, ou funcionalidades pós-MVP).

## VS-10 (Consolidação do MVP) — completo, ver `planning/vs10-consolidacao-mvp_20260726` para o detalhe completo
- Slice de fechamento, sem domínio novo: 1 fluxo E2E crítico via Playwright + axe-core (`apps/web/e2e/critical-flow.spec.ts`), hardening pontual de segurança (rate limit em memória no `POST /agent/messages`), README.md da raiz reescrito (setup Windows/Docker, testes, roteiro de demonstração, limitações conhecidas).
- E2E cobre onboarding via seed demo → dashboard → simular decisão → comparar antes/depois → detectar fragilidades → gerar e aprovar plano preventivo — **não passa pelo agente conversacional** de propósito (evita não-determinismo de chamada real à Anthropic num teste automatizado).
- Auditoria axe-core encontrou e corrigiu 3 violações reais: `SelectTrigger` (Base UI) sem nome acessível quando não usa `id`+`<Label htmlFor>` pareado — regra para componentes futuros: todo `Select` do design system precisa de label pareado OU `aria-label` direto.
- 189 testes de backend (185 + 4 do `RateLimiter`) + 34 de frontend + 1 E2E passando.
- **Meta Harness aprovou na 1ª rodada** (`APPROVED`, commit `051f325`) — único ponto notado foi a dívida técnica pré-existente de `tsc` em `ProjectionChart.tsx:99`, corretamente classificada como não-regressão via a baseline capturada com `git stash` (isolando o estado limpo pós-VS-09 antes de implementar).
- Descoberto durante a implementação: simulações normais (`DecisionForm`) **não têm passo de confirmação** — `POST /simulations` persiste direto ao submeter; o padrão propose→confirm é exclusivo do agente conversacional (VS-09). E fragilidades exigem `POST /fragilities/detect` explícito antes de `POST /plans/generate` retornar algo (senão volta `201` com lista vazia, sem erro).

## VS-09 (Agente conversacional) — completo e verificado, ver `planning/vs09-agente-conversacional_20260725` para o detalhe completo
- Agente via API da Anthropic direta (Claude Haiku 4.5, tool calling nativo, sem LangChain/LangGraph), painel lateral persistente no AppShell (`features/agent/`).
- Tools allowlisted: `get_dashboard_summary`, `get_autonomy`, `list_fragilities` (leitura real) + `propose_simulation` (nunca persiste — só valida via `validate_decision_parameters` reaproveitado da VS-07).
- Fluxo de confirmação em 2 chamadas: `POST .../agent/messages` propõe (não persiste) → `POST .../agent/actions/{id}/confirm` confirma e persiste, **sem nunca voltar a chamar o LLM**.
- Persistência: `conversations` + `agent_messages` (com coluna dedicada `confirmed`, não um campo dentro do JSON — necessário para claim atômico via `UPDATE ... WHERE confirmed=false`).
- 182 testes de backend (11 novos da VS-09) + 34 de frontend (4 novos: `AgentPanel`) passando.
- **Passou por 4 rodadas de Meta Harness** (3 REJECTED com achados reais, 1 APPROVED) — ver lições abaixo, são importantes para qualquer slice futura que mexa em confirmação de ações, migrações, ou isolamento entre perfis.
- **Verificação manual real confirmada** (2026-07-26): rebuild dos containers + migração aplicada em Postgres real + usuário testou via `http://localhost:3000` — o agente respondeu com os valores reais do perfil demo (saldo R$12.500,00, obrigações R$4.950,00), confirmando que chama `get_dashboard_summary`/`get_autonomy` de verdade, sem inventar números. Fluxo de confirmação de simulação não testado manualmente (usuário optou por não testar; coberto pelos 182 testes automatizados).

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

## Meta Harness — lições cumulativas (VS-08 + VS-09 + VS-10)
- Fluxo: `capture-baseline.sh` → implementar → commit checkpoint → `validate-step.sh` → corrigir → revalidar. **Regenerar os contratos (`current-slice.md`/`acceptance-criteria.md`) antes de rodar o gate é obrigatório**, não opcional (esquecer isso gerou uma rejeição falsa de "scope creep" na VS-08).
- **Se a baseline não foi capturada antes de começar a implementar** (esquecimento de processo), dá pra capturar retroativamente com segurança: `git stash push -u` (isola as mudanças ainda não commitadas) → `capture-baseline.sh` → `git stash pop` (restaura). Usado na VS-10 sem problema.
- **Nunca editar uma migração Alembic já commitada, mesmo dentro da mesma sessão/PR** — o harness trata cada commit como um possível ponto de deploy real. Sempre criar uma migração nova em cima; se precisar ser resiliente a um estado histórico incerto (ex.: um commit anterior já rejeitado que alterou o schema de um jeito diferente), tornar a migração idempotente (checar via `sa.inspect(...).get_columns(...)` antes de `add_column`/`drop_column`) — achado da VS-09.
- **Campos que precisam de garantia atômica/idempotência não devem viver dentro de um blob JSON** — usar coluna dedicada permite `UPDATE ... WHERE coluna=valor` condicional (a única atomicidade real sem lock explícito). Achado da VS-09 (`AgentMessage.confirmed`).
- **Claims atômicos não devem commitar isoladamente** quando o efeito colateral real depende de passos posteriores na mesma operação — deixar tudo na mesma transação do `Session` por request faz uma falha no meio ser recuperável via rollback implícito do `get_session()` em vez de deixar um estado "confirmado" órfão. Achado da VS-09.
- **Cálculos financeiros divididos em parcelas iguais precisam arredondar para cima (`ROUND_UP`), não `ROUND_HALF_UP`** — achado da VS-08 (`RESERVE_BELOW_THREE_MONTHS`), vale para qualquer parcelamento futuro.
- `downgrade()` autogerado do Alembic não remove enums do Postgres — adicionar `sa.Enum(name='...').drop(op.get_bind(), checkfirst=True)` manualmente sempre que a tabela nova tiver uma coluna `Enum`.
- Guards de segurança/validação devem checar o sinal mais específico disponível, não um proxy mais amplo — ex.: `evidence` real (só tools de leitura) é diferente de "alguma tool foi chamada" (`propose_simulation` conta como tool_call mas não é evidência). Achado da VS-09.
- **Codex roda `next build` de verdade dentro do sandbox read-only** e reproduz erros de `tsc` reais — a baseline (com os erros pré-existentes já capturados) é o que permite ele classificar isso como `PRE_EXISTING_FAILURE` em vez de bloquear a aprovação. Achado da VS-10, confirma que a baseline não é só burocracia, é o que evita falso-positivo de regressão.

## Verificação manual confirmada (VS-08, sessão 2026-07-24)
- Migração `cc81d6a213fa` aplicada em Postgres real via `docker compose exec api python -m alembic upgrade head` (após rebuild dos containers `api`/`web` com `docker compose up -d --build`).
- Fluxo real via curl: detectar fragilidades → gerar 3 planos → aprovar um → mover para `in_progress` → `completed` → rejeitar outro → transição inválida retornou 422 → regenerar não duplicou o `proposed` ainda ativo, mas recriou propostas para os risk codes terminais — comportamento exatamente como projetado.
- **Falso alarme de encoding**: `python -m json.tool` no Windows/Git Bash exibe acentos como mojibake por causa do stdout codec do console, não é um bug real — preferir `python -c "print(...)"` para não se enganar com um artefato de exibição do console.

## Armadilhas confirmadas neste projeto (cumulativo)
- `apps/web/AGENTS.md`: Next.js 16.2.11 tem breaking changes reais vs. treinamento (`params` é `Promise`).
- shadcn/ui usa Base UI (`@base-ui/react`): usar `render={<Link>...</Link>}` **e** `nativeButton={false}` ao invés de `asChild`. `Select.onValueChange` do Base UI entrega `string | null` (não só `string`) — tratar o `null` explicitamente ao gravar em estado tipado como `string`. **Todo `SelectTrigger` precisa de `id`+`<Label htmlFor>` pareado OU `aria-label` direto** — sem isso, axe-core acusa violação crítica de acessibilidade (o texto do `SelectValue` não conta como accessible name). Achado da VS-10.
- CORS precisa de `CORSMiddleware` explícito no FastAPI.
- Dockerfile da API precisa copiar `alembic.ini`/`alembic/`; `data/demo/` precisa de volume mount + `DEMO_DATA_DIR`.
- Pydantic serializa `Decimal` como **string** no JSON — DTOs TypeScript usam `string` para todos os campos monetários/percentuais/meses; valores monetários usam sempre `{amount, currency}` (padrão `MoneyDto`/`_money_dict`), nunca uma string crua de valor sem moeda.
- Migração Alembic gerada via SQLite temporário (`_autogen_tmp.db`) precisa ser aplicada manualmente no Postgres de dev depois (`docker compose exec api python -m alembic upgrade head`) — repetido em toda slice com tabela nova (VS-06, VS-07, VS-08, VS-09).
- `calculate_autonomy` (VS-05) mede ativos/despesas, é **independente de renda e de serviço de dívida** — decisões/fragilidades que só afetam renda ou dívida não mudam `autonomy_change_months`; o efeito aparece só no fluxo de caixa. Já são 3 achados independentes (VS-05, VS-07, VS-08) confirmando o mesmo comportamento de design.
- `npx tsc --noEmit` no front-end já acusa 5 erros pré-existentes (ProjectionChart, FragilityList, ProfileStep×2, ResourceStepForm) que não bloqueiam `npm test`/build — não são regressões novas, mas checar `tsc` ao adicionar componentes com recharts/Select para não somar mais erros.
- No Windows/Git Bash, testar migrações Alembic contra SQLite: usar path relativo (`sqlite:///arquivo.db`) em vez de path absoluto estilo `/d/...` (que o Python nativo do Windows não resolve corretamente) — achado da VS-09.
- `.venv` local da API (`apps/api/.venv`) existe e pode ser usado diretamente (`.venv/Scripts/python.exe`) para pytest/scripts sem precisar do Docker — útil quando Docker não está disponível na sessão.
- **Containers Docker já "Up" não têm o código novo automaticamente** — uma sessão que implementa mudanças enquanto os containers de uma sessão anterior ainda estão rodando precisa de `docker compose up -d --build` explícito antes de testar; senão o sintoma é "cliquei e não aconteceu nada" com a build antiga.
- **`docker compose` lê um `.env` na raiz do projeto automaticamente** — segredos como `ANTHROPIC_API_KEY` podem viver lá em vez de precisar de `export` manual toda sessão.
- **`apps/web/Dockerfile` roda `npm run dev` (não build de produção)** — Next.js compila cada rota sob demanda na primeira visita; qualquer E2E (Playwright) contra essa stack precisa de timeout generoso (`expect.timeout` ~15s) na primeira navegação a uma rota ainda não visitada nesta execução do container. Achado da VS-10.
- **Simulações normais (`DecisionForm`) não têm passo de "confirmar"** — `POST /simulations` persiste direto ao submeter o formulário; o padrão propose→confirm de 2 chamadas é exclusivo do agente conversacional (VS-09). Achado da VS-10.
- **Fragilidades exigem detecção explícita** (`POST /fragilities/detect`) antes de `GET /fragilities` retornar algo ou de `POST /plans/generate` gerar planos — não é automático; sem detecção prévia, `generate` retorna `201` com lista vazia (não erro). Achado da VS-10.

## Pendências conhecidas (adiadas por decisão do usuário)
- Polish visual de todo o front-end (onboarding + dashboard) com `/ui-material3` — sessão dedicada futura, não bloqueia o MVP.
- Medir mais 2 execuções do Meta Harness (`gpt-5.6-terra`+`reasoning_effort=high`) antes de fixá-lo como padrão definitivo — ver `planning/meta-harness_20260724`.
- Comparar cenários via agente, gerar plano preventivo via agente, navegação guiada pelo agente (capacidades da VS-09 adiadas por decisão do plano).
- Autenticação de usuário — fora do escopo dos critérios de aceite do MVP (Spec seção 31); `profile_id` continua livre nas rotas, documentado como limitação conhecida no README.
- Dívida técnica pré-existente de `tsc`/`lint` (5 erros desde VS-07/VS-08, ver acima) — não corrigida, não é regressão de nenhuma slice.

## Tasks trackeadas (Task tool)
IDs #9–#19 (VS-02), #20–#26 (VS-03), #27–#37 (VS-04), #38–#46 (VS-05), #47–#56 (VS-06), #57–#69 (VS-07), #86–#93 (VS-08) — todas `completed`. VS-09 e VS-10 trackeadas via tasks internas da sessão (Fase 1-5 cada), não IDs numerados nesta lista.

## Próxima sessão
MVP completo — nenhuma slice pendente. Perguntar ao usuário o que vem a seguir:
1. Polish visual via `/ui-material3` sobre onboarding + dashboard (pendência conhecida, mencionada acima).
2. Alguma funcionalidade pós-MVP (ex.: as capacidades do agente adiadas na VS-09 — comparar cenários, gerar plano preventivo via agente).
3. Corrigir a dívida técnica pré-existente de `tsc`/`lint` (não bloqueia nada, mas está pendente desde a VS-07).
