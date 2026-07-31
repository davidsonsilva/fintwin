# Plano: Redistribuição dos cards Projeção de fluxo de caixa + Autonomia financeira

## Status: CONCLUÍDO (2ª rodada) — validado visualmente pelo usuário em 2026-07-29

## 1ª rodada (2026-07-28)
- `DashboardView.tsx`: inverteu span da grid `ft-grid--analytics` (Projection 2 col / Autonomy 1 col).
- `AutonomyPanel.tsx`: migrado para `FtCard`, números em grid 2x2 (`ft-autonomy-stats`).
- Usuário pediu mais ajustes no dia seguinte, comparando com `imagens/proposta-de-layout.png`.

## 2ª rodada (2026-07-29) — itens do usuário, todos aplicados
1. **Projeção de fluxo de caixa full-width**: `ProjectionChart.tsx` saiu do grid, virou seção própria full-width.
   Migrado de `Card`/`CardHeader` (shadcn) para `FtCard` + `ft-card-header`/`ft-chart-container`; cores hardcoded
   (#16a34a/#dc2626/#2563eb) trocadas por tokens (`--ft-success`/`--ft-danger`/`--ft-info`) — resolve pendência
   antiga registrada na 1ª rodada.
2. **Autonomia financeira**: os 4 números (básica/provável/adversa/perda de renda) saíram do `AutonomyPanel` e
   viraram 4 `ft-status-card` dentro da grid de indicadores (`ft-grid--indicators`, agora 4 colunas). `AutonomyPanel`
   ficou só com o bloco de evidências/premissas (ativos elegíveis, obrigações essenciais, `<details>`, disclaimer),
   como card próprio abaixo da grid de indicadores — decisão do usuário via AskUserQuestion (rejeitou remover as
   evidências do dashboard).
3. **Próximos eventos financeiros**: saiu de card full-width solto e virou a 4ª coluna da grid de indicadores,
   compacto, `grid-row: 1 / span 2` (classe nova `.ft-indicators-events`), igual ao padrão da imagem de referência.
   Grid de indicadores agora tem 6 status cards (autonomia x4 + déficit + fragilidades) em 3 cols x 2 rows + a
   coluna de eventos — bateu certo com o layout de referência sem precisar inventar conteúdo novo.
4. **Botão fixo no bottom do card**: `IncomeCommitmentCard.tsx` e `ExpenseBreakdownChart.tsx` trocaram `mt-3` por
   `mt-auto` no link de rodapé (ambos já eram `flex flex-col` dentro de um grid item stretched — só faltava o
   `mt-auto` empurrar pro fim).
5. **Tooltip customizado nos gráficos**: criado `ChartTooltip.tsx` (componente compartilhado, balão com
   `ft-chart-tooltip*` no `design-system.css`, usa tokens `--ft-bg-elevated`/`--ft-border`/`--ft-shadow-sm`) e
   aplicado via `content={<ChartTooltip .../>}` em `BalanceHistoryChart`, `ExpenseBreakdownChart` (Pie não tinha
   tooltip nenhum antes) e `ProjectionChart`.

## Pendente — NÃO mexer ainda (item 5 do usuário, 2026-07-29)
Usuário considera redundante ter dois pontos de entrada pro chat da IA: o card "Insight do seu Gêmeo Financeiro"
(hoje só abre o AgentPanel via `openAgent`) e o "IA FinTwin" (mesma coisa). Ele quer que "Insight" mostre
recomendações diretamente (sem abrir chat) em vez de duplicar a entrada pro agente conversacional. Usuário disse
"vou pensar em algo e depois te falo" — **não implementar nada disso até ele trazer uma proposta concreta**.

## Build/validação
Rebuild obrigatório (`docker compose build web && docker compose up -d web`, ver `mem:gotcha/docker-web-sem-hot-reload`)
+ `npx tsc --noEmit` (só erros pré-existentes em `FragilityList.tsx`/`ProfileStep.tsx`/`ResourceStepForm.tsx`,
não relacionados a esta mudança). Usuário validou visualmente e confirmou: "já validei eu mesmo, ficou muito melhor".
