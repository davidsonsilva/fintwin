# Slice atual: Dashboard — Linha de 3 gráficos (distribuição, evolução do saldo, comprometimento)

> Plano formal aprovado previamente: `planning/dashboard-3-graficos-linha_20260727` (Serena).
> Fonte de verdade visual: `imagens/proposta-de-layout.png`.

## Contexto

Substitui a seção de analytics do dashboard por uma nova linha de 3 colunas — Distribuição das
despesas (donut), Evolução do saldo líquido (linha) e Comprometimento da renda (gauge
redesenhado) — mantendo `ProjectionChart` e `AutonomyPanel` (reposicionados abaixo da nova
linha, não removidos). Ao contrário da slice anterior (puramente front-end), esta inclui
mudanças reais de domínio/backend: uma nova entidade (`BalanceSnapshot`), uma migração Alembic,
um caso de uso de captura idempotente de snapshot e dois endpoints HTTP novos.

## Escopo entregue

### Backend
- **Agregação de despesas por categoria**: novo endpoint que retorna obrigações mensais
  agrupadas por categoria com percentual sobre o total (`CategoryBreakdownDto`), consumido pelo
  donut do frontend.
- **Entidade `BalanceSnapshot`**: nova tabela `balance_snapshots` (migração Alembic
  `59331c899349_balance_snapshots.py`, aplicada sobre `f1b2c3d4e5a6`), repositório
  `SqlAlchemyBalanceSnapshotRepository`, captura idempotente de snapshot mensal do saldo líquido
  ao carregar o dashboard (`LoadDemoProfileUseCase`/fluxo de summary), e endpoint de histórico
  (`/balance-history?months=N`) que retorna os últimos N snapshots ordenados por período.
- **Seed demo**: `data/demo/balance_snapshots.json` com 6 meses sintéticos (2026-01 a 2026-06,
  saldo líquido evoluindo de 8200.00 a 12100.00 BRL), carregado de forma idempotente por
  `LoadDemoProfileUseCase`.
- **Testes novos**: `test_summary_captures_balance_snapshot_idempotently` (unit),
  `test_balance_history_after_loading_demo_profile` e
  `test_balance_history_missing_profile_returns_404` (integration). Suite completa: 196 testes
  passando.
- Verificação end-to-end via Docker (fora do pytest): perfil demo carregado, `/dashboard` →
  saldo líquido 12500.00, `/obligations/by-category` → 3 categorias somando 100%,
  `/balance-history` → 6 entradas fev–jul terminando em 12500.00; idempotência confirmada
  chamando `/dashboard` duas vezes e comparando o histórico resultante (sem duplicação).

### Frontend (`apps/web/src/features/dashboard/`)
- `ExpenseBreakdownChart.tsx` (novo): donut (`recharts` `PieChart`/`Pie`/`Cell`) consumindo
  `getExpenseBreakdown`, com legenda via `.ft-chart-legend`/`.ft-legend-item`/`.ft-legend-dot`
  já existentes, estados de loading/erro/vazio, link "Ver obrigações".
- `BalanceHistoryChart.tsx` (novo): linha (`LineChart`/`Line`) consumindo
  `getBalanceHistory(profileId, 6)`, tooltip formatado em BRL, estados de loading/erro/vazio.
- `IncomeCommitmentCard.tsx` (novo): gauge (`RadialBarChart`) com 4 níveis de risco
  (`riskTierFor`: Saudável ≤40% / Atenção ≤60% / Elevado ≤75% / Crítico >75%) mapeados para
  badges de cor (`.ft-badge--success/warning/purple/danger`, adicionados a `design-system.css`
  reaproveitando os tokens `--ft-success/warning/purple/danger` existentes), substitui o gauge
  inline antigo do `DashboardView`.
- `types.ts`/`api.ts`: `CategoryBreakdownDto`, `BalanceSnapshotDto`,
  `dashboardApi.getExpenseBreakdown`/`getBalanceHistory`.
- `DashboardView.tsx`: nova seção `ft-grid ft-grid--analytics` com os 3 componentes acima;
  seção seguinte (mesma classe de grid, reaproveitada) mantém `ProjectionChart` +
  `AutonomyPanel` sem alteração de conteúdo, apenas reposicionados abaixo da nova linha.

Nenhuma classe de grid nova foi criada — a linha nova e a linha existente reutilizam
`.ft-grid--analytics` (`1.05fr 1.05fr 1fr`, responsiva a 2 colunas ≤1280px e 1 coluna ≤720px).

## Fora de escopo (não implementado nesta slice)
- Qualquer alteração em `ProjectionChart`, `AutonomyPanel`, Sidebar, Topbar ou Onboarding além
  do reposicionamento descrito acima.
- Cobertura de teste de frontend (Vitest) para os 3 componentes novos — não foram adicionados
  testes automatizados de UI nesta slice (risco residual conhecido).
- Correção do erro de tipo pré-existente do `Tooltip`/`formatter` do recharts em
  `ProjectionChart.tsx` (dívida técnica já documentada, não tocada nesta slice).
