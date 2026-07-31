# Plano: Linha de 3 gráficos do dashboard (Distribuição das despesas + Evolução do saldo líquido + Comprometimento da renda)

## Status: CONCLUÍDO (2026-07-28) — Tarefas #1-#9 entregues, revisado e aprovado pelo Meta Harness

## Resumo
Substituiu a seção antiga do `DashboardView.tsx` (ProjectionChart + AutonomyPanel lado a lado +
card "Comprometimento da renda" isolado mais abaixo) por uma grid de 3 colunas iguais batendo
com `imagens/proposta-de-layout.png`: Distribuição das despesas (donut) | Evolução do saldo
líquido (linha, 6 meses) | Comprometimento da renda (gauge). ProjectionChart e AutonomyPanel
foram preservados, reposicionados logo abaixo dessa linha.

## Backend (Tarefas #1-#4)
- `GET /api/v1/profiles/{profile_id}/obligations/by-category` — agregação por categoria via
  `GetExpenseBreakdownByCategoryUseCase`. Retorna 409 se as obrigações do perfil tiverem moedas
  divergentes (usa `Money.add()`, que levanta `CurrencyMismatchError` — traduzido pro router).
- `GET /api/v1/profiles/{profile_id}/balance-history?months=6` — entidade `BalanceSnapshot`
  (`domain/balance_history/`), tabela `balance_snapshots` (migração `59331c899349`), captura
  idempotente lazy em todo `GET /dashboard` (`GetDashboardSummaryUseCase._capture_snapshot_if_absent`).
  `months` validado com `Query(ge=1, le=60)`. Repositório `SqlAlchemyBalanceSnapshotRepository.add()`
  só engole `IntegrityError` quando revalida que o snapshot do profile_id/period já existe (corrida
  esperada); qualquer outro `IntegrityError` é repropagado.
- Seed demo: `data/demo/balance_snapshots.json` (6 meses sintéticos, Jan-Jun 2026), carregado
  idempotentemente por `LoadDemoProfileUseCase`.
- Suite backend: 201 testes passando (inclui testes de moeda divergente via HTTP 409, corrida de
  snapshot idempotente, e IntegrityError não relacionado sendo repropagado).

## Frontend (Tarefas #5-#8)
- `IncomeCommitmentCard.tsx`, `ExpenseBreakdownChart.tsx`, `BalanceHistoryChart.tsx` (novos) em
  `apps/web/src/features/dashboard/`, todos com estados de loading/erro/vazio.
- `DashboardView.tsx` reorganizado: nova seção `ft-grid ft-grid--analytics` com os 3 componentes
  acima; seção seguinte (mesma classe reaproveitada) mantém ProjectionChart + AutonomyPanel.
- 4 variantes de badge (`.ft-badge--success/warning/purple/danger`) adicionadas a
  `design-system.css`, reaproveitando tokens `--ft-*` existentes.

## Meta Harness (Tarefa #9)
- `.meta-harness/contracts/current-slice.md` e `acceptance-criteria.md` reescritos pra descrever
  esta slice (substituindo o conteúdo da slice anterior de design system).
- 3 rodadas de `scripts/validate-step.sh` (Codex review): REJECTED (moeda cruzada sem validação +
  corrida de snapshot sem tratamento + `months` sem bound) → REJECTED (CurrencyMismatchError
  virando 500 sem tradução HTTP + IntegrityError sendo engolido genericamente demais) →
  **APPROVED_WITH_WARNINGS** (único warning: ramo de re-raise do IntegrityError sem teste — corrigido
  num commit extra de cobertura, sem nova rodada completa do harness pois o veredito já não era
  bloqueante).
- Commits da slice (`master`): feat inicial → fix (moeda/corrida/bounds) → fix (409 HTTP + supressão
  restrita de IntegrityError) → test (cobertura do warning residual).

## Achados técnicos (mantidos por relevância futura)
- Serena não tem symbols indexados pra Python neste projeto (`active_languages: ['typescript']`
  só) — usar `Read`/`Grep` pro backend.
- Alembic: sem wrapper de Makefile. Rodar autogenerate direto no container Docker
  (`docker compose exec api python -m alembic revision --autogenerate -m "..."`); venv local não
  alcança o hostname `db` do docker-compose. Fluxo: `docker compose build api` → `up -d api` →
  autogenerate → `docker cp` do arquivo gerado pra `apps/api/alembic/versions/` →
  `docker compose exec api python -m alembic upgrade head`.
- `scripts/validate-step.sh <sha> [baseline.json]` roda o Codex CLI como revisor independente
  (sandbox read-only) sobre `git diff BASE^..TARGET` de um commit — **precisa de um commit real**,
  não roda sobre working tree suja. Exit 0 = APPROVED/APPROVED_WITH_WARNINGS, exit 2 = REJECTED.
  Relatório normalizado em `.meta-harness/reports/`, saída bruta em `.meta-harness/raw/`, estado
  em `.meta-harness/state/current-review.json`.
- SQLite (usado nos testes via `tests/conftest.py`) não enforce FK por padrão — pra testar um
  `IntegrityError` não relacionado à constraint de unicidade esperada, usar colisão de primary key
  (mesmo `id`, profile_id/period diferentes) em vez de violação de FK.
