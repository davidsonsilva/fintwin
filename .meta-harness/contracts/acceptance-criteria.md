# Critérios de aceitação: Design system — fechamento da migração CSS→CVA

> Derivado de `planning/design-system-css-para-cva-e-meta-harness_20260727` (que deixou os
> candidatos nomeados) e consolidado em `planning/migracao-css-cva-fechada_20260731` (Serena).
> Slice puramente front-end: sem domínio, backend, schema, endpoint ou contrato de API.

1. **Neutralidade visual**: cada componente reproduz medida por medida a regra CSS que
   substitui — dimensões, raio, cor, borda, tipografia, espaçamento e **curva/duração de
   transição**. Divergência em qualquer uma delas é regressão, não melhoria. A comparação é
   feita contra o original extraído com `git show <base>:<arquivo>`, do **CSS e do JSX**,
   porque o JSX carrega decisões que o CSS não mostra (tamanho de glifo, classes combinadas).
   Única exceção declarada: a remoção de `grid-auto-rows: minmax(0,1fr)` de
   `.ft-grid--indicators`, correção intencional do bug que originou o trabalho.

2. **Regra global sai no mesmo commit**: nenhum componente novo entra sem que a classe `.ft-*`
   equivalente seja removida de `design-system.css` no mesmo commit. O ganho vem de deletar
   CSS, não de somar abstração. Verificável: zero ocorrências de `.ft-status-card`,
   `.ft-status-icon`, `.ft-status-title`, `.ft-status-description`, `.ft-metric-icon` e
   `.ft-badge` (e modificadores) em todo `apps/web/src`.

3. **Sem regressão de testes existentes**: nenhum teste pré-existente removido ou marcado
   `skip`. A suíte de backend não é afetada por esta slice (nenhum arquivo de `apps/api`
   tocado). **A suíte de frontend (Vitest) já falha na baseline** — ver
   `.meta-harness/baselines/statuscard-before.json`; falha dela não conta como regressão desta
   slice, mas também não pode piorar.

4. **Quality gates limpos além da baseline conhecida**: `npx tsc --noEmit` não introduz erros
   novos além dos 3 pré-existentes em `ProfileStep.tsx` e `ResourceStepForm.tsx`
   (incompatibilidade Zod/react-hook-form); `eslint` limpo nos arquivos tocados; nenhum import
   órfão deixado para trás após a troca de classe por componente.

5. **Tipo no lugar de string mágica**: onde a variante era escolhida por nome de classe CSS
   (`badge: "ft-badge--danger"`) ou montada por template string
   (`ft-metric-icon--${variant}`), passa a ser um tipo do design system (`BadgeTone`,
   `IconChipTone`). Critério: valor inválido deve falhar em compilação, não silenciosamente em
   runtime.

6. **Contrato mínimo por papel (ISP)**: props que só alguns consumidores usam são opcionais —
   `action` no `StatusCard` (1 de 6 indicadores tem link de detalhe), `iconSize` no `IconChip`
   (o CSS nunca amarrou glifo a chip: 38px aparece com glifo de 18px e de 22px). Nenhum
   componente vira um `Card` gordo com props opcionais que ninguém usa.

7. **Diferenças reais do CSS preservadas nas variantes, não na base**: a borda existe só no
   chip de 48px (`.ft-metric-icon`), nunca no de 38px (`.ft-status-icon`) — logo mora na
   variante `size`, não na base do CVA. Vale para qualquer diferença entre modificadores que a
   base tentaria unificar.

8. **Polimorfismo sem inchar o componente**: quando o elemento precisa ser outro (o `<Link>` do
   `StatusCard`), usa-se a função de variantes direto no `className`
   (`badgeVariants({ tone: "link" })`), mesmo padrão já adotado com `buttonVariants` — em vez
   de adicionar prop `as`/`render` ao componente.

9. **Escopo respeitado**: nada da frente de layout é tocado. `.ft-metric-card`,
   `.ft-analytics-card`, `.ft-card-header/title/subtitle/footer` e `.ft-grid--*` permanecem
   intactos; `ui/card` (shadcn) permanece no onboarding, simulações e planos preventivos
   (exclusão deliberada de 27/07). Espaçamento externo embutido no CSS original — o
   `margin-top: 10px` do `.ft-badge` — é reproduzido, não corrigido: removê-lo é decisão de
   layout.

10. **Verificação visual antes do commit**: toda tela afetada é conferida pelo usuário antes do
    commit, não só a que motivou a mudança. Nesta slice foram quatro: tela inicial, dashboard,
    radar de fragilidade e planos preventivos. O rebuild do container `web`
    (`docker compose build web && up -d web`) é obrigatório antes de qualquer conferência — o
    serviço não tem volume montado e serve build congelado.
