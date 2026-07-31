# Sessão 2026-07-27: Polimento visual do AppShell + migração CSS → tokens/CVA

## Status: CONCLUÍDO (aprovado pelo Meta Harness)

## O que foi feito

### 1. Polimento visual iterativo (Sidebar, Topbar, Onboarding)
- Logo/ícone da marca (public/logo-icon.png, agent-icon.png): recortes do usuário tinham
  fundo opaco não-transparente; corrigido via chroma-key com `sharp` (script node ad-hoc,
  não ficou no repo) antes de salvar em `public/`.
- Sidebar: nova seção de navegação por recurso (Perfil/Contas/Rendas/Obrigações/Dívidas/
  Metas/Eventos/Revisão) com páginas dedicadas em `/dashboard/[profileId]/{profile,
  resources/[resource],review}`, reaproveitando os formulários de `features/onboarding/`
  em vez de deep-link pro wizard (o deep-link original prendia o usuário sem navegação de
  volta ao dashboard — bug relatado e corrigido). Item "Onboarding guiado" separado,
  linkando pro wizard do zero. Card "IA FinTwin" com toggle do AgentPanel (antes sempre
  aberto, ocupando 340px fixos sempre).
- PageHeader (novo componente compartilhado, substitui headers duplicados em 8 páginas):
  hambúrguer funcional (mobile drawer via SidebarContext), sino/engrenagem/avatar/
  "Sincronizar dados" decorativos (`disabled` — sem backend real). Layout posicionado via
  coordenadas absolutas extraídas de `imagens/toolbar.json` (JSON preciso medido do
  screenshot de referência, ±2px) em vez de flexbox auto-centralizado.
- Hierarquia tipográfica normalizada: pesos de fonte fora de escala (650/750/800)
  substituídos por 400/500/600/700 conforme `imagens/FinTwin AI — Design System.md`.

## Lições técnicas (evitar repetir)

1. **Prints pequenos enganam.** Comparar screenshots por leitura visual direta é impreciso
   pra alinhamento fino (px de padding, cor exata). Quando o usuário forneceu um JSON de
   medição precisa (`imagens/toolbar.json`, coordenadas absolutas ±2px), os ajustes finais
   bateram de primeira. Se o usuário reclamar de desalinhamento repetidamente após um
   screenshot, pedir extração JSON/medição em vez de insistir em comparação visual.

2. **Bug real de CSS Grid**: um `<div>` de overlay (`.ft-sidebar-overlay`) só tinha
   `position:fixed` definido *dentro* de um `@media (max-width:1024px)`. Em telas largas,
   ao renderizar condicionalmente (`isMobileOpen && <div>`), esse div virava um item comum
   do CSS Grid pai (`.ft-app`, grid de 3 colunas), embaralhando todo o layout. Lição: se um
   elemento precisa ficar fora do fluxo (fixed/absolute) em qualquer estado condicional,
   a regra de posicionamento não pode estar presa a um media query — declarar a base
   (`position:fixed` sempre, com `display:none` default) fora do media query.

3. **Tailwind v4 `max-[Npx]:` é exclusivo** (`width < Npx`), enquanto CSS `max-width:Npx`
   é inclusivo. Pra bater exatamente com uma media query CSS existente, usar a variante de
   media query arbitrária `[@media(max-width:Npx)]:` em vez de `max-[Npx]:`.

4. **Hidratação sem lint**: para "só renderizar algo depois de montar no cliente" (evitar
   hydration mismatch), usar `useSyncExternalStore(() => () => {}, () => true, () => false)`
   em vez de `useState(false)` + `useEffect(() => setState(true), [])` — este último dispara
   o lint `react-hooks/set-state-in-effect` (pego pelo Meta Harness).

5. **Server→Client boundary com Zod**: passar um objeto de config contendo um schema Zod
   (função/classe) de um Server Component pra um Client Component quebra em runtime
   ("Only plain objects... can be passed"). Resolvido movendo a seleção do config (lookup
   por chave) pra dentro do próprio Client Component, recebendo só a chave (string) do
   servidor.

## Meta Harness — como funciona de fato neste projeto

- Script real é `scripts/validate-step.sh` (bash), **não** `validate-step.ps1` como um doc
  antigo (`docs/features/meta-harness.md`) sugeria — o projeto migrou pra bash.
- Revisa **commits**, não a working tree suja. `scripts/validate-step.sh [ref] [baseline]`
  compara `ref` (default HEAD) com o pai dele. Fluxo: commitar → rodar → se REJECTED/
  APPROVED_WITH_WARNINGS com findings reais, corrigir → novo commit → rodar de novo.
- `.meta-harness/contracts/current-slice.md` precisa refletir o trabalho real sendo
  revisado — se ficar desatualizado (ex: ainda descrevendo a VS anterior), o Codex rejeita
  por "scope creep" mesmo quando o código está correto. Atualizar o contrato é parte do
  ciclo normal, não only-once.
- Não é automático — precisa ser chamado explicitamente. Nesta sessão rodou 5 vezes,
  pegando 2 regressões reais (lint novo + hover perdido nos cards migrados) e 1 achado de
  processo (contrato desatualizado) antes do APPROVED final.

## Migração CSS → tokens/CVA (baseado em `imagens/transformar o css em objetos.md`)

- `apps/web/src/design-system/tokens/*.ts`: espelham os `--ft-*` de `design-system.css`
  como objetos TS tipados (`as const`) — cores, tipografia, espaçamento, radius, sombras,
  motion, layout. `design-system.css` continua sendo a fonte de verdade (globals.css
  registra os mesmos tokens no `@theme` do Tailwind pra virarem utilitários `bg-ft-*` etc).
- `apps/web/src/design-system/components/{Button,Card,IconButton}`: variantes CVA
  (`class-variance-authority`, já estava no package.json). Migrados como consumidores reais:
  Sidebar, PageHeader, todos os cards de `DashboardView.tsx`, os 3 cards de destaque da
  Tela Inicial (`page.tsx`).
- `.ft-button` (base + 4 variantes) e `.ft-card` (base + compact/disabled) foram **removidos
  inteiramente** de `design-system.css` — sem consumidor cru restando em nenhum lugar.
- **Decisão de escopo deliberada**: AgentPanel/PendingActionCard e todo o Onboarding
  (OnboardingWizard, ProfileStep, ResourceStepForm, ReviewStep, ProfileSummary) **não foram
  migrados** — já usam Button/Card/Input do shadcn pra tudo que é componente real; as
  classes `.ft-*` que restam neles são layout de uso único (um consumidor cada: painel do
  chat, bolhas de mensagem, stepper do wizard), que o próprio guia de migração recomenda
  manter como CSS puro em vez de virar abstração artificial. Isso está registrado em
  `.meta-harness/contracts/current-slice.md` pra não ser confundido com trabalho pendente.
- `Card` ganhou prop `as` polimórfica (article/div/etc); todos os usos migrados passam
  `interactive={true}` pra preservar o hover (levantar+sombra+borda) que `.ft-card` aplicava
  incondicionalmente antes — só o brilho diagonal no hover (`::before`) não foi recriado
  (simplificação conhecida e aceita pelo usuário).

## Estado para continuar depois

Se o usuário pedir pra continuar a migração CVA: os próximos candidatos com padrão repetido
(não migrados ainda) seriam `.ft-metric-icon`/`.ft-status-icon` (chip de ícone colorido,
repete 4-6x no dashboard) e `.ft-badge` (pill, repete em vários lugares). AgentPanel e
Onboarding foram avaliados e conscientemente excluídos — não reavaliar sem novo motivo.
