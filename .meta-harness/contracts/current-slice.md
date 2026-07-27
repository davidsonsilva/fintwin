# Slice atual: Design System — Redesign visual do AppShell (pós-VS-10)

> Trabalho interativo de polimento visual pedido diretamente pelo usuário (sem planning/*
> formal prévio), consolidado retroativamente neste contrato para permitir revisão do Meta
> Harness. Fonte de verdade visual: `imagens/proposta-de-layout.png`, `imagens/toolbar.json`,
> `imagens/FinTwin AI — Design System.md`.

## Contexto

Após a VS-10 (MVP consolidado), o usuário pediu alinhamento visual do painel interno
(Onboarding, Tela Inicial, Dashboard, Sidebar, Topbar) ao design system `--ft-*` de
referência, e o início da migração desse CSS autoral para tokens TypeScript + variantes
CVA (`class-variance-authority`), preservando o Tailwind gerado e o CSS de terceiros
intocados.

Não é uma Vertical Slice do domínio financeiro — não adiciona nem altera regra de negócio,
caso de uso, contrato HTTP ou schema de banco. É puramente front-end (`apps/web/`).

## Escopo entregue

### Sidebar / navegação
- Logo/ícone com fundo tratado (transparente), nova seção de navegação por recurso
  (Perfil/Contas/Rendas/Obrigações/Dívidas/Metas/Eventos/Revisão) com páginas dedicadas em
  `/dashboard/[profileId]/{profile,resources/[resource],review}` — reaproveitando os
  formulários já existentes de `features/onboarding/`, sem duplicar lógica de negócio.
- Item "Onboarding guiado" separado, linkando para `/onboarding` (fluxo de criação de
  perfil do zero), desacoplado da navegação de dados de um perfil existente.
- Card "IA FinTwin" com toggle do `AgentPanel` (antes sempre aberto, ocupando 340px fixos).
- Drawer mobile funcional (`SidebarContext`, overlay, `visibility`+`inert` de foco).

### Topbar (`PageHeader`, novo componente compartilhado)
- Substitui headers duplicados em 8 páginas por um único componente.
- Hambúrguer funcional; sino/engrenagem/avatar/"Sincronizar dados" são decorativos
  (`disabled`) — não há backend de notificações, configurações ou sincronização.
- Layout posicionado via coordenadas absolutas extraídas de `imagens/toolbar.json`.

### Design system
- `design-system.css`: hierarquia tipográfica normalizada (pesos fora de escala 650/750/800
  removidos), espaçamento de seção corrigido, botão primário/nav/badge alinhados ao doc de
  referência.
- `design-system/tokens/*.ts`: espelham os valores `--ft-*` de `design-system.css` como
  objetos TypeScript tipados (`as const`), sem duplicar a fonte de verdade (globals.css
  registra os mesmos tokens no `@theme` do Tailwind).
- `design-system/components/{Button,Card,IconButton}`: variantes CVA equivalentes a
  `.ft-button`/`.ft-card`/`.ft-icon-button`/`.ft-header-avatar`. Consumidores migrados:
  `Sidebar.tsx` (botão "Conversar com IA"), `PageHeader.tsx` (hambúrguer, sino, engrenagem,
  avatar, "Sincronizar dados"), `DashboardView.tsx` (4 cards de métrica, 2 cards de status +
  1 link de status, card do gráfico de comprometimento, card de eventos futuros), `page.tsx`
  Tela Inicial (3 cards de destaque). `Card` ganhou prop `as` (article/div/etc) e todos os
  usos migrados passam `interactive` para preservar o hover (levantar + sombra + borda) que
  `.ft-card` aplicava incondicionalmente — só o brilho diagonal (`::before`) não foi
  recriado (simplificação conhecida e aceita).
- `.ft-button`, `.ft-menu-button`, `.ft-icon-button`, `.ft-notification-dot`,
  `.ft-header-avatar`, `.ft-header-chevron`, `.ft-header-sync`, `.ft-header-profile`,
  `.ft-card`, `.ft-card--compact`, `.ft-card--disabled` removidos de `design-system.css`
  (órfãos após a migração; `.ft-button:disabled` mantido — ainda usado no card de IA insight
  do dashboard, que não foi migrado nesta rodada).

## Fora de escopo (não implementado nesta slice)

- `AgentPanel`, `OnboardingWizard`/formulários de recurso e o card de IA insight do
  dashboard (botão "Em breve") continuam usando classes CSS `.ft-*` existentes — não
  migrados para CVA nesta rodada.
- Qualquer mudança de domínio financeiro, regra de negócio, endpoint HTTP ou schema.
- Sistema de autenticação/conta de usuário, notificações, configurações ou sincronização de
  dados reais (os controles do header existem só visualmente).
- Cobertura de teste automatizado para as novas rotas/drawer (nenhum teste novo foi
  adicionado para `resources/[resource]`, `profile`, `review`, ou o toggle do drawer mobile).
