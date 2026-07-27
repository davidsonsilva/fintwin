# Critérios de aceitação: Design System — Redesign visual do AppShell

> Extraído retroativamente do escopo entregue em `current-slice.md`, já que esta slice não
> teve um `planning/*` formal antes da implementação.

1. **Sem regressão de domínio**: nenhuma mudança em `apps/api/src/domain/`, casos de uso,
   contratos HTTP ou schema de banco (Alembic) — esta slice é exclusivamente front-end.
2. **Sem regressão de testes existentes**: os 34 testes de frontend (Vitest) continuam
   passando; nenhum teste pré-existente foi removido ou tornado `skip` para "passar".
3. **Quality gates limpos além da baseline conhecida**: `npm run lint` não introduz novos
   findings além do baseline documentado (`@typescript-eslint/no-explicit-any` em
   `resourceConfigs.ts`/`ResourceStepForm.tsx`, pré-existente desde VS-07/VS-08);
   `npx tsc --noEmit` não introduz erros além dos 5 já documentados como dívida técnica
   pré-existente (`ProjectionChart.tsx`, `FragilityList.tsx`, `ProfileStep.tsx`,
   `ResourceStepForm.tsx`).
4. **Rotas novas funcionam**: `/dashboard/[profileId]/profile`, `/resources/[resource]`
   (accounts/incomes/obligations/debts/goals/events) e `/review` renderizam sem erro de
   runtime (o bug original de serialização Server→Client de um schema Zod foi corrigido
   movendo a seleção de config para um Client Component).
5. **Acessibilidade do drawer mobile**: o `<aside>` da sidebar não é alcançável via Tab
   quando fechado/fora da tela (`visibility: hidden` sob `max-width: 1024px`), e o foco é
   movido para o primeiro link de navegação quando o drawer abre.
6. **Controles decorativos são inequivocamente não-funcionais**: sino, engrenagem, avatar e
   "Sincronizar dados" no `PageHeader` têm o atributo `disabled` — não simulam
   funcionalidade inexistente nem enganam o usuário sobre o que é clicável.
7. **Tokens não divergem da fonte de verdade**: os valores em `design-system/tokens/*.ts`
   batem com os `--ft-*` correspondentes em `design-system.css` no momento do commit (não
   há verificação automatizada disso ainda — checagem manual).
8. **Migração CVA não quebra visual existente**: o `Button` (`design-system/components/
   Button`) usado em `Sidebar.tsx` reproduz o mesmo resultado visual que a classe `.ft-button
   ft-button--ghost-purple ft-button--full` que substituiu.
