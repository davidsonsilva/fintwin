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
- `design-system/components/{Button,Card}`: variantes CVA equivalentes a `.ft-button`/
  `.ft-card`. Primeiro consumidor real: `Sidebar.tsx` (botão "Conversar com IA").

## Fora de escopo (não implementado nesta slice)

- Migração completa de todos os usos de `.ft-*` para os novos componentes CVA — só Sidebar
  foi migrado; o restante (PageHeader, DashboardView, cards do dashboard, onboarding,
  AgentPanel) continua usando as classes CSS `.ft-*` existentes.
- Qualquer mudança de domínio financeiro, regra de negócio, endpoint HTTP ou schema.
- Sistema de autenticação/conta de usuário, notificações, configurações ou sincronização de
  dados reais (os controles do header existem só visualmente).
- Cobertura de teste automatizado para as novas rotas/drawer (nenhum teste novo foi
  adicionado para `resources/[resource]`, `profile`, `review`, ou o toggle do drawer mobile).
