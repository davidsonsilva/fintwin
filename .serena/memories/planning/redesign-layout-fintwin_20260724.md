# Plano: Redesign do layout do FinTwin AI (AppShell + design system --ft-*)

## 📅 Criado em: 2026-07-24

## 🎯 Status: ✅ IMPLEMENTADO (verificação funcional completa; verificação visual manual delegada ao usuário)

---

## 📋 Resumo Executivo

Adotado o design system `--ft-*` (fornecido pelo usuário via `imagens/proposta-de-layout.png` + `imagens/proposta-layout-css.md`) como base visual definitiva do painel interno do FinTwin AI, substituindo a diretriz de Material Design 3 (exceção registrada em `~/.claude/rules/common/design-hallmark-vs-md3.md`). Construído um AppShell (sidebar + conteúdo) para todas as rotas `/dashboard/[profileId]/*`, dashboard reconstruído com KPIs/indicadores/gráficos usando dados reais (VS-04/05/06), e paleta aplicada globalmente via remapeamento dos tokens shadcn existentes — o que fez a maior parte das páginas de fragilidades/simulações/planos herdar o novo visual automaticamente, sem reescrita.

---

## ✅ Decisões Tomadas (todas mantidas sem correção do usuário)

1. **`--ft-*` substitui MD3 para este projeto** — registrado como exceção explícita na regra global, com o resto do MD3 preservado para outros projetos.
2. **Escopo = AppShell + todas as páginas existentes** — dashboard, fragilidades, simulações, planos, onboarding, landing.
3. **Dados reais onde já existem** — autonomia (VS-05), fragilidades (VS-06), déficit projetado (VS-04) usam a API real; só o banner de IA (VS-09) é placeholder.
4. **Nav restrita ao que existe hoje** — Início/Radar de fragilidade/Simulações/Planos preventivos; CRUD pós-onboarding (Perfil/Contas/Rendas/etc.) fica fora, é slice futura.

## 🏗️ Implementação (como ficou de fato)

- **`apps/web/src/app/design-system.css`** (novo): tokens `--ft-*` + todas as classes de componente do design system (sidebar, cards, métricas, botões, formulários, AI insight, responsivo) copiadas do `proposta-layout-css.md`, com o bloco de RESET original simplificado (removido `box-sizing`/font-family manuais que colidiriam com o preflight do Tailwind e com `next/font`; mantido só `html{color-scheme:dark}` e o gradiente de fundo do body).
- **`apps/web/src/app/globals.css`**: `:root` remapeado para os valores `--ft-*` (background→ft-bg-page, card→ft-bg-surface, primary→ft-primary, sidebar→ft-bg-sidebar etc.); removido o bloco `.dark` e o `@custom-variant dark` — app agora é **dark-only**, sem alternância clara/escura (decisão implícita: o mockup não define tema claro).
- **`apps/web/src/components/shell/Sidebar.tsx`** (novo, client component): logo, nav (Início/Radar de fragilidade/Simulações/Planos preventivos, ativo via `usePathname`), painel de IA como placeholder desabilitado (`ft-sidebar-panel--ai`). **Painel de "upgrade/Pro" do mockup foi deliberadamente omitido** — não existe tier pago no produto (Spec não define), incluir seria enganoso.
- **`apps/web/src/app/dashboard/[profileId]/layout.tsx`** (novo): AppShell (`ft-app` grid) envolvendo Sidebar + `{children}` em `ft-main`/`ft-content`. Server Component, `await params`.
- Páginas filhas (`page.tsx` de dashboard/fragilities/simulations/simulations/[id]/plans) perderam o header duplicado "Voltar ao dashboard" (redundante com a sidebar) e ganharam headers locais com classes `ft-header`/`ft-page-title`/`ft-page-description`.
- **`DashboardView.tsx`** reconstruído: grid de 4 KPI cards reais (saldo, obrigações, comprometimento, meta), grid de 3 indicadores reais (autonomia básica, próximo déficit, fragilidades — clicável para o radar), `ProjectionChart`/`AutonomyPanel` mantidos (herdam o novo visual via token remap, sem reescrita), gauge de comprometimento da renda novo (recharts `RadialBarChart`, dado real), lista de eventos restilizada (`ft-event-item`), banner de IA estático (`ft-ai-insight`, botão desabilitado).
- **Doação do donut de despesas por categoria**: **não implementado** — exigiria conversão de frequência→valor mensal por categoria no frontend, o que duplicaria lógica de domínio (`monthly_equivalent`) já proibida pelo próprio padrão do projeto ("regras de negócio financeiras não devem ser reimplementadas no frontend"). Documentado aqui como limitação consciente, mesmo espírito da omissão do custo de oportunidade na VS-07.
- `FragilityList`/`PlanCard`: badges manuais (`rounded bg-muted...`) trocados por `.ft-badge`. Resto do visual (Card, Button, Select) herdado automaticamente do remap de tokens — não precisou reescrever `SimulationHistory`/`DecisionForm`/`SimulationComparison`/`PreventivePlanList`.
- `app/page.tsx` (landing) reescrito sem classes `dark:` (que dependiam do `.dark` class-toggle removido) — agora usa `bg-background`/`text-foreground`/`text-muted-foreground` direto.
- Onboarding: nenhuma mudança de código necessária — já usava só tokens (`bg-background` etc.), herdou a paleta nova automaticamente.

## ❌ Lições / Achados

- **`dark:` no Tailwind v4 sem `@custom-variant dark (&:is(.dark *))` volta a ser media-query-based** (`prefers-color-scheme`), não class-based. Ao remover esse `@custom-variant` (decisão consciente de ir dark-only), qualquer `dark:` residual em código próprio (não em componentes shadcn gerados) precisa ser removido/revisado — só a landing page (`app/page.tsx`) tinha isso hardcoded; os componentes `ui/*.tsx` gerados pelo shadcn têm `dark:` residual mas são inofensivos (a paleta já é dark por padrão via token remap, então o "extra" do `dark:` nunca muda nada visualmente incorreto).
- **Mistura de classes `.ft-button` (CSS puro) com o componente shadcn `Button` (cva) causa dupla-estilização** — decisão: usar SEMPRE o componente shadcn `Button` (que já herda a paleta via tokens) para ações que já usam esse componente, e reservar `.ft-button`/`.ft-*` cru só para markup que não passa pelo `Button` (ex: dentro de `Sidebar.tsx`, banner de IA).
- **Verificação visual via browser automation (Claude in Chrome) travou** nesta sessão — screenshot/get_page_text deram timeout repetido em duas abas diferentes, mesmo com a página funcionalmente OK (todas as chamadas de API retornaram 200, confirmado via `read_network_requests`). Suspeita: uma requisição pendente para `http://fonts.googleapis.com` (protocolo inseguro, sem `s`) parece vir de uma extensão do Chrome no perfil usado, não do app. Usuário optou por conferir manualmente no navegador em vez de insistir na automação.

## 🔧 Verificação Realizada

- ✅ `pytest` (backend, 168 testes) — sem regressão, redesign é só frontend.
- ✅ `npm test` (frontend, 30 testes, 10 arquivos) — 2 ajustes de seletor necessários (`formatMoney` mudou de `"12500.00 BRL"` para `Intl.NumberFormat` `"R$ 12.500,00"`; duplicação de "50.0%"/"1.8 meses" entre KPI card e gauge/AutonomyPanel exigiu `getAllByText` em vez de `getByText`) — nenhuma mudança de comportamento, só de apresentação.
- ✅ `npx tsc --noEmit` — exatamente os mesmos 5 erros da baseline pré-existente (ProjectionChart/FragilityList/ProfileStep×2/ResourceStepForm), nenhum novo.
- ✅ `npm run lint` — exatamente os mesmos 24 erros + 1 warning da baseline (resourceConfigs.ts/ResourceStepForm.tsx `any`, `waitFor` não usado), nenhum novo.
- ⏳ Verificação visual manual: delegada ao usuário (bloqueio da automação de browser, não do app).

## 📚 Contexto e Referências

- Mockup: `D:\IA Projects\gemeo-financeiro\imagens\proposta-de-layout.png`
- Design system fonte: `D:\IA Projects\gemeo-financeiro\imagens\proposta-layout-css.md`
- Regra global atualizada: `C:\Users\david\.claude\rules\common\design-hallmark-vs-md3.md` (seção "Exceção: FinTwin AI")
- Arquivos novos: `apps/web/src/app/design-system.css`, `apps/web/src/components/shell/Sidebar.tsx`, `apps/web/src/app/dashboard/[profileId]/layout.tsx`

## 🚦 Próximo Passo

Aguardando o usuário confirmar visualmente que o dashboard (`http://localhost:3000/dashboard/{profileId}`) e demais páginas estão corretas. Depois disso: commitar as mudanças e retomar o planejamento da VS-09 (Agente conversacional).
