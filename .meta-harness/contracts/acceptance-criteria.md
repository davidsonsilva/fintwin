# Critérios de aceitação: Dashboard — Linha de 3 gráficos

> Derivado do plano `planning/dashboard-3-graficos-linha_20260727` (Serena).

1. **Domínio correto**: `BalanceSnapshot`, o caso de uso de captura idempotente e o endpoint de
   agregação por categoria vivem em `apps/api/src/domain/` e `apps/api/src/application/`; o
   frontend não reimplementa nenhuma regra de cálculo (percentual de categoria, comprometimento
   de renda) — apenas consome os DTOs já calculados pela API.
2. **Idempotência do snapshot**: capturar o dashboard múltiplas vezes no mesmo período não gera
   snapshots duplicados em `balance_snapshots` (coberto por
   `test_summary_captures_balance_snapshot_idempotently` e verificado ao vivo via Docker).
3. **Sem regressão de testes existentes**: a suíte de backend (`pytest`) continua passando na
   íntegra (196 testes) após as mudanças; nenhum teste pré-existente foi removido ou marcado
   `skip`.
4. **Quality gates limpos além da baseline conhecida**: `npx tsc --noEmit` no frontend não
   introduz erros novos além dos já documentados como dívida técnica pré-existente (incluindo o
   erro de tipo do `Tooltip`/`formatter` do recharts em `ProjectionChart.tsx`, que não foi
   tocado nesta slice); `npm run lint` não introduz novos findings.
5. **Endpoints novos funcionam**: `/obligations/by-category` retorna categorias cujos
   percentuais somam ~100%; `/balance-history?months=N` retorna os últimos N snapshots
   ordenados por período (`periods == sorted(periods)`) e responde 404 para perfil inexistente.
6. **Estados de UI cobertos**: `ExpenseBreakdownChart`, `BalanceHistoryChart` e
   `IncomeCommitmentCard` tratam explicitamente loading, erro e vazio (sem dado) — nenhum
   componente assume que a query sempre retorna dados.
7. **Sem dado hardcoded ou fake no frontend**: os 3 componentes novos consomem dados reais via
   `dashboardApi`/React Query; nenhum valor de gráfico é mockado ou calculado no cliente.
8. **Reaproveitamento de design system**: a nova linha de 3 colunas reutiliza a classe de grid
   `.ft-grid--analytics` existente (nenhuma classe de grid nova foi criada); as 4 variantes de
   badge de risco (`.ft-badge--success/warning/purple/danger`) usam os tokens de cor `--ft-*`
   já existentes, sem cores hardcoded fora do design system.
9. **`ProjectionChart` e `AutonomyPanel` preservados**: ambos continuam renderizando e
   funcionando sem alteração de comportamento, apenas reposicionados abaixo da nova linha de
   gráficos.
