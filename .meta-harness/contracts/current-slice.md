# Slice atual: Design system — fechamento da migração CSS→CVA (IconChip, StatusCard, Badge)

> Plano formal aprovado previamente: `planning/design-system-css-para-cva-e-meta-harness_20260727`
> (Serena), que deixou nomeados os candidatos restantes. Consolidação e fechamento registrados
> em `planning/migracao-css-cva-fechada_20260731`.

## Contexto

Slice **puramente front-end e visualmente neutra por construção**. Nenhuma mudança de domínio,
backend, schema, endpoint ou contrato de API.

A migração de classes CSS globais (`design-system.css`) para componentes CVA tipados começou em
27/07 cobrindo a *caixa* (`.ft-card`, `.ft-button`) e parou antes do *conteúdo*, deixando
registrado quais eram os próximos candidatos: o chip de ícone colorido (`.ft-status-icon` /
`.ft-metric-icon`, repetido 9×) e a pill (`.ft-badge`, repetida 6×). Esta slice fecha exatamente
esses dois, mais os cards de status do dashboard que dependiam do chip.

Entregue em **dois commits**:

- `c248ec0` — `IconChip` + `StatusCard`
- `2d920d1` — `.ft-metric-icon` + `.ft-badge`

O critério de aceite aplicado foi: **os componentes reproduzem medida por medida o CSS que
substituem**. A comparação foi feita contra o conteúdo original extraído com
`git show HEAD:<arquivo>` — tanto do CSS quanto do JSX, porque o JSX carregava decisões que o
CSS não mostra (tamanho de glifo, combinação de classes).

## Escopo entregue

### Componentes novos (`apps/web/src/design-system/components/`)

- **`IconChip/`** (`IconChip.tsx`, `iconChipVariants.ts`, `index.ts`) — substitui
  `.ft-status-icon` (38px) e `.ft-metric-icon` (48px) + seus 4 modificadores de cor.
  Variantes CVA: `tone` (primary/info/purple/warning) e `size` (sm=38px/rounded-12,
  md=48px/rounded-15). **A borda mora na variante `md`, não na base**, porque no CSS original
  só `.ft-metric-icon` tinha `border: 1px solid transparent`. Prop `iconSize` opcional porque o
  CSS nunca amarrou glifo a chip: 38px aparecia com glifo de 18px no dashboard e de 22px no
  radar de fragilidade.
- **`StatusCard/`** (`StatusCard.tsx`, `index.ts`) — substitui `.ft-status-card`,
  `.ft-status-title`, `.ft-status-description`. Props: `icon`, `tone`, `label`, `hint`,
  `value`, `loading?`, `action?`. `action` é opcional porque só 1 dos 6 indicadores tem link
  de detalhe (ISP — o contrato não obriga quem não usa). Os 6 blocos de ~20 linhas de JSX
  repetidas viraram 6 chamadas declarativas.
- **`Badge/`** (`Badge.tsx`, `badgeVariants.ts`, `index.ts`) — substitui `.ft-badge` e os
  modificadores `--success/--warning/--purple/--danger/--link`. Renderiza `<span>`; quando o
  badge precisa ser outro elemento (o `<Link>` do `StatusCard`), usa-se `badgeVariants()`
  direto no `className`, mesmo padrão já adotado com `buttonVariants`.

### Consumidores migrados

`DashboardView.tsx` (6 StatusCard + 4 IconChip md + 1 IconChip sm), `page.tsx` (3 IconChip md),
`AutonomyPanel.tsx`, `FragilityList.tsx` (IconChip + 4 Badge por severidade),
`PlanCard.tsx` (1 Badge).

Duas trocas de string mágica por tipo: `FragilityList` guardava `badge: "ft-badge--danger"`
(nome de classe CSS) e passou a guardar `tone: BadgeTone`; `page.tsx` montava a variante por
template string (`ft-metric-icon--${variant}`) e passa `tone={variant}` verificado em
compilação.

### CSS removido no mesmo passo (regra dura do projeto)

Componente novo só entra se a regra global equivalente sair no mesmo commit — o ganho vem de
deletar CSS, não de somar abstração. Removidos de `design-system.css` (~100 linhas):
`.ft-status-card`, `.ft-status-icon`, `.ft-status-title`, `.ft-status-description`,
`.ft-metric-icon` + 4 modificadores, `.ft-badge` + 5 modificadores (incluindo `--link` e seu
`:hover`). Verificado: zero ocorrências dessas classes no código.

### Única mudança visual intencional

Removido `grid-auto-rows: minmax(0, 1fr)` de `.ft-grid--indicators`. Essa regra fazia **todas
as linhas do grid ficarem iguais à mais alta**, então o card de eventos — cuja altura é função
de quantos eventos o perfil tem — esticava os seis cards de status junto, chegando a 416px na
faixa de duas colunas. É a correção do bug que originou o trabalho. Medido antes/depois em
viewport 996×706: alturas 104/124 divergentes → 104 uniformes; aproveitamento horizontal
27–40% → 80%. Validada visualmente pelo usuário.

## Fora de escopo (não implementado nesta slice)

- **Arquitetura de cards por papel** (`MetricCard`, `EventsCard`, `AnalyticsCard`, Sidebar) —
  decisão explícita do usuário de parar a frente de layout até a migração fechar. As classes
  `.ft-metric-card`, `.ft-analytics-card`, `.ft-card-header/title/subtitle/footer` e
  `.ft-grid--*` **permanecem intactas de propósito**.
- **`ui/card` (shadcn) no onboarding, simulações e planos preventivos** — exclusão deliberada
  de 27/07, registrada para não ser reaberta. `DashboardView` ainda importa `Card/CardContent`
  do shadcn, mas apenas nos blocos de erro e perfil-não-encontrado.
- **`margin-top: 10px` embutido no `.ft-badge`** — reproduzido no componente em vez de
  removido. Tirar é decisão de layout e mudaria o visual, o que esta slice não faz.
- **Testes de frontend (Vitest)** para os componentes novos — não adicionados. Risco residual
  conhecido; a suíte de frontend já falha desde antes desta slice (ver baseline).

## Verificação executada

- `tsc --noEmit`: 3 erros, **todos pré-existentes** e nos mesmos 2 arquivos da baseline
  (`ProfileStep.tsx`, `ResourceStepForm.tsx` — incompatibilidade Zod/react-hook-form). Nenhum
  erro novo.
- `eslint` nos arquivos tocados: limpo.
- `docker compose build web && up -d web` antes de cada verificação visual (o serviço `web` não
  tem volume montado, então edição no host não reflete sem rebuild).
- Validação visual pelo usuário nas 4 telas afetadas (tela inicial, dashboard, radar de
  fragilidade, planos preventivos) antes de cada commit.

**Baseline**: `.meta-harness/baselines/statuscard-before.json`. Atenção: `vitest` já sai com
exit code 1 na baseline — testes de frontend quebrados desde antes desta slice.
