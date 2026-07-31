# Polimento do dashboard FinTwin AI — 2026-07-29/30 — TODOS OS 13 ITENS CONCLUÍDOS E VALIDADOS

Referência visual: `imagens/proposta-de-layout.png`. Perfil de teste: `057943a0-6187-475c-9411-7dc78ef50cf0` (Rafael Martins).

## STATUS FINAL: plano 100% concluído, validado item a item pelo usuário. Sessão encerrada aqui — próximo passo é a skill de validação visual (ainda não iniciada, ver seção final).

## GOTCHA CRÍTICO (vale pra qualquer sessão futura neste projeto)
Containers `web` e `api` do docker-compose NÃO têm bind mount (só `COPY . .`) → SEM hot reload. Toda mudança em `apps/web/` exige `docker compose build web && docker compose up -d web`; idem `api`. Verificar deploy real com `MSYS_NO_PATHCONV=1 docker exec gemeo-financeiro-web-1 grep -n <marcador> /app/src/...` (o prefixo MSYS_NO_PATHCONV=1 é necessário no Git Bash pra não mangular paths tipo /app/...).

## APRENDIZADOS GRANDES desta sessão
1. **Validação visual sem achismo**: comparar 2 JSONs estruturados (referência vs render atual) campo a campo por proporção resolveu em 1 tentativa o que 10 rodadas de ajuste no olho não resolviam (gauge do IncomeCommitmentCard). Recharts é ruim pra controle geométrico fino — o gauge foi refeito em SVG à mão.
2. **Escopo de mudanças em classes CSS compartilhadas**: ao alterar `.ft-card-header` (linha divisória), a mudança se propagou pra lugares indesejados (top bar, card de eventos) e faltou em lugares esquecidos (shadcn genérico em simulation/preventive-plans, onboarding `.ft-form-title`). Lição: mapear TODOS os usos via grep antes de uma mudança de classe compartilhada.
3. **Specs precisas > imagens vagas**: quando o usuário trouxe CSS+HTML+medidas exatas (redesign do Select, redesign do card de eventos), a implementação convergiu de primeira. Quando só havia uma imagem de referência sem números, valeu perguntar/comparar estruturas antes de implementar.

## Resumo completo dos 13 itens (todos CONCLUÍDOS)
1. Campo `name` em FinancialProfile (migration `a3f7d1c9b4e2`) + saudação personalizada no dashboard.
2. AutonomyPanel: listas com bullet (`.ft-evidence-*`), assumptions com tooltip.
3. ExpenseBreakdownChart: donut+legenda lado a lado, responsivo (flex-wrap, scroll só se >8 categorias), footer link+linha.
4. BalanceHistoryChart: AreaChart com grid/degradê/eixo Y "20K", tooltip mês/ano.
5. IncomeCommitmentCard: gauge em SVG à mão (não recharts) — trilha verde + fill âmbar proporcional ao valor, `.ft-analytics-card` (min-height 420px + footer absoluto) alinha os 3 cards de analytics.
6. ProjectionChart: Select com prop `items` (mostra label, não value cru) + backend PT-BR nas assumptions (`_multiplier_phrase`/`_SCENARIO_LABELS_PT` em `domain/projection/engine.py`) + tooltip explicativo.
7. FragilityList: migrado pro design system (`FtCard`/`FtButton`), severidade PT-BR com badge, estado vazio reforçado.
8. Tooltip/InfoTooltip (`components/ui/tooltip.tsx`, wrapper `@base-ui/react/tooltip`, sem seta) espalhado por TODO o sistema: dashboard completo, `PageHeader` (prop `info`) em todas as páginas, `ResourceStepConfig` (campo `info`) nas 6 páginas de recurso.
9. `.ft-card-header` com `border-bottom` sutil — depois estendido pra cards shadcn genéricos (via div separado `mx-(--card-spacing)`, não border direto pra evitar full-bleed) e onboarding (`.ft-form-header`). Exceção: card de eventos (`.ft-indicators-events`) sem linha. Removido de `.ft-header` (topbar) por não ter sido pedido.
10. 3 cards de análise com `.ft-card-footer` link+linha; "Próximos eventos" mantém botão cheio.
11. AutonomyPanel: `formatMoney` trocado pra `Intl.NumberFormat("pt-BR",{style:"currency"})`.
12. Página `/balance-history`: criado `BalanceHistoryTable.tsx` — tabela real (não só gráfico) com período por extenso, saldo, e **variação mês a mês** (valor+% com seta verde/vermelha), calculada client-side a partir do histórico.
13. Select global (`components/ui/select.tsx`) redesenhado: min-width 160px, padding 6px, altura 38px/item, destaque do selecionado sutil (`--ft-primary` 16% opacidade em vez de azul chapado), hover/focus-visible, gap 8px trigger→menu. Vale pra todos os Selects do sistema.

## Correções extras feitas no caminho (pente fino pós-13-itens)
- Card "Próximos eventos financeiros": redesenhado com `grid-template-areas` (date/content/value), `.ft-event-content` (classe nova no wrapper), título com `-webkit-line-clamp:2`, valor com `white-space:nowrap`, breakpoint 720px empilha valor abaixo do conteúdo. Formato de valor trocado de "1800.00 BRL" pra "R$ 1.800,00" (reaproveitado `formatMoney`, removida `formatMoneyPlain` duplicada).
- Tooltips de gráfico (ProjectionChart, BalanceHistoryChart) também estavam com números crus (`.toFixed(2)` ou concat com sufixo BRL) — corrigidos pra `Intl.NumberFormat` currency.
- Onboarding (`resourceConfigs.ts`): 6 `renderSummary` (Contas/Rendas/Obrigações/Dívidas/Metas/Eventos) mostravam "1800.00 BRL" cru na lista de itens já cadastrados — corrigido com helper `formatMoney` local.
- Onboarding (`ResourceStepForm.tsx`): 4 grupos de Select (`liquidityTypeOptions`, `recurrenceOptions`, `incomeStabilityOptions`, `directionOptions`) mostravam o enum em inglês cru como label (ex: "checking_account"). Criado mapa `OPTION_LABELS` (PT-BR) + prop `items` no Select (mesmo fix do item 6). Valor técnico enviado à API continua em inglês (é o que o backend espera) — só o label mudou.
- Campo "Moeda" nos formulários de recurso: usuário questionou se deveria mudar; DECISÃO: manter como está (input editável, valor "BRL" — código ISO correto, necessário pro `Intl.NumberFormat` funcionar). Não mexer.

## PRÓXIMO PASSO (ainda não iniciado): skill de validação visual
Usuário quer construir o pipeline completo descrito em `imagens/proposta-skill.md`: extração JSON de imagem de referência + captura Playwright + Pixelmatch/SSIM + classificação de erros + loop autocorretivo. Usar o card de comprometimento da renda como caso de teste (`imagens/referencia.json`/`imagens/comprometimento-renda-obrigacoes-detalhado.json` já existem como exemplo). Perguntas em aberto que precisam ser respondidas antes de começar: (a) posso instalar Playwright como devDependency em apps/web? (b) como extrair o JSON estruturado da imagem de referência daqui pra frente — eu mesmo via visão, ou um subagente dedicado? claude-in-chrome estava travando nesta sessão (usuário negou acesso) — Playwright é a alternativa natural pra captura automática.

## Task tracker: #1-13 TODOS done e validados. Nenhuma pendência aberta do pente fino do dashboard.
