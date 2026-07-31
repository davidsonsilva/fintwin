# [TEMP] Cards do dashboard: terminar a migração CSS→componentes — 2026-07-31

Status: **StatusCard (etapa 1) implementado e funcionando; NÃO validado visualmente pelo
Davidson; NÃO commitado; Meta Harness ainda não rodado.** Contexto estourou aqui.
Continuação de `mem:planning/responsividade-dashboard_20260730` (superseded) e conclusão de
`mem:planning/design-system-css-para-cva-e-meta-harness_20260727` (parada no meio).

## RETOMAR POR AQUI

1. Medir o dashboard com **outro volume de dados** — perfil demo
   `d5b17141-43c8-4758-91c7-d516532d475a` (era o passo em execução quando o contexto acabou;
   perfil do Davidson é `057943a0-6187-475c-9411-7dc78ef50cf0`).
2. Pedir validação visual ao Davidson.
3. Commit → atualizar `.meta-harness/contracts/current-slice.md` → `scripts/validate-step.sh`.
4. Decidir a questão de altura aberta (abaixo).
5. Seguir para MetricCard → EventsCard → AnalyticsCard → Sidebar.

## A diretriz do Davidson (dita 3x antes de eu escutar)

Cada card vira um componente com partes definidas, dono do próprio espaçamento, altura e
reação à largura. **Responsividade mora no componente, não em media query global.**
SOLID/ISP: contrato por papel, não um `Card` gordo com 20 props opcionais.
Server-Driven UI foi **analogia, não pedido** — não repropor.

## O que FOI FEITO nesta sessão (working tree, não commitado)

**Criado:**
- `design-system/components/IconChip/{iconChipVariants.ts,IconChip.tsx,index.ts}` — CVA com
  `tone` (primary/info/purple/warning) e `size` (sm=38px/md=48px). Glifo acompanha o chip.
- `design-system/components/StatusCard/{StatusCard.tsx,index.ts}` — props: `icon`, `tone`,
  `label`, `hint`, `value`, `loading?`, `action?`. `action` opcional porque só 1 dos 6 tem.

**Alterado:**
- `DashboardView.tsx`: 6 blocos de ~20 linhas de JSX → 6 `<StatusCard/>`. Import de
  `IconChip` e `StatusCard`. O chip do card de eventos também virou `IconChip`.
- `AutonomyPanel.tsx`, `FragilityList.tsx`: `.ft-status-icon` → `<IconChip>`.
- `design-system.css`: **deletados** `.ft-status-card`, `.ft-status-icon`,
  `.ft-status-title`, `.ft-status-description` e o `grid-auto-rows: minmax(0,1fr)` de
  `.ft-grid--indicators`.

**Qualidade:** `tsc --noEmit` sem erros novos (só os 2 arquivos pré-existentes da baseline:
`ProfileStep.tsx`, `ResourceStepForm.tsx`). `eslint` nos 5 arquivos tocados: limpo.
Baseline capturada em `.meta-harness/baselines/statuscard-before.json` — **atenção: `vitest`
já sai com exit code 1 na baseline**, testes de frontend quebrados desde antes.

## Resultado medido (viewport 996×706)

| | antes | depois |
|---|---|---|
| altura dos 6 status | 104 e 124 (divergiam) | **104, todos iguais** |
| aproveitamento horizontal | 27–40% | **80%** |

**A causa real do bug original ficou provada:** `grid-auto-rows: minmax(0, 1fr)` em
`.ft-grid--indicators` fazia **todas as linhas ficarem iguais à mais alta**. Na faixa de 2
colunas o card de eventos entra na mesma grade e levava os 6 status para **416px**. Removida
a regra, os status voltaram a 104px. Isso encerra o mistério de
`mem:global/css-grid-spanning-item-dita-altura-das-linhas` neste caso concreto.

## QUESTÃO ABERTA — critério de altura mal formulado (decisão do Davidson)

Simulando larguras menores (via `grid-template-columns` por JS), as alturas **divergem entre
linhas do grid**: em 4 colunas (card 225px), cards 0–3 = 115px, cards 4–5 = 163px. Causa
legítima: o card 4 tem valor de 2 linhas ("Sem déficit projetado (12 meses…)") e o card 5 tem
o link de ação que os outros não têm.

**Meu critério "todas as instâncias com altura idêntica" está mal formulado** — ele força
uniformidade artificial. O critério correto é: *a altura de um card não pode ser determinada
por outro card nem pelo volume de dados de outro componente* — e **isso está atendido**.
Perguntar ao Davidson se quer uniformidade forçada mesmo assim.

**NÃO tentar de novo `min-h` em unidades relativas.** Gastei 4 tentativas: `min-h-[2lh]` (o
Tailwind descarta a unidade `lh`, embora o Chrome a suporte — medido: 38.4375px) e
`min-h-[2.75em]` (a regra `.min-h-\[2\.75em\] { min-height: 2.75em }` **é gerada** e o
seletor casa, mas nenhuma regra de min-height chega ao elemento — computa `0px`; não é a
container query, verificado removendo `@min-[320px]:min-h-0` na mão). Ambas removidas do
código. Se for preciso travar a altura, usar px explícito ou outra abordagem — **não repetir
essas duas**.

## Armadilhas de medição descobertas (importantes)

- **Container queries não reavaliam sincronamente** ao mudar `grid-template-columns` via JS:
  `getComputedStyle` devolve valor obsoleto no mesmo turno. Medir em **duas chamadas
  separadas** do `javascript_tool` (mudar numa, medir na outra) — `await rAF` dentro do
  mesmo script faz o CDP dar timeout de 45s.
- `mcp__claude-in-chrome__resize_window` **não redimensiona** (janela maximizada): reportou
  sucesso e o viewport ficou em 996. Para testar larguras, alterar
  `grid-template-columns` direto — testa a container query, mas **não** as media queries.
- O Chrome desta instância está com **zoom ~81%**: janela de 1000px → viewport CSS de 1230px.
  Não dá para resetar (a extensão bloqueia `ctrl+0`). Compensar pelo tamanho da janela.
- `screenshot` da extensão trava; `javascript_tool` funciona. **Medir, não olhar.**

## Decisão de arquitetura (aprovada)

- **Uma caixa só no dashboard**: `design-system/components/Card` (tokens `--ft-*`).
- **Componentes por papel em cima dela** (ISP), cada um dono da própria reação à largura via
  **container query** — `@container` + `@min-[320px]:` funciona (validado: o layout alterna
  entre empilhado e valor-à-direita sozinho).
- **`ui/card` (shadcn) sai do `DashboardView`**, mas **permanece** no onboarding/simulações
  (10 arquivos). Decisão deliberada de 27/07 — **não reabrir**. O que não pode é uma **mesma
  tela** usar os dois. `DashboardView` ainda importa `Card, CardContent` do shadcn: pendente.
- **REGRA DURA**: nenhum componente novo entra sem que a regra global equivalente saia no
  mesmo commit. O ganho vem de **deletar CSS**, não de adicionar abstração.

## Ordem restante

MetricCard → EventsCard → AnalyticsCard → Sidebar (visibilidade + toggle exibir/esconder,
pedido dele). **Não mexer** no breakpoint de 1100px ainda: deve cair sozinho.

## Correções do Davidson nesta sessão

1. "Pare de tentar as coisas" — diagnóstico antes de código.
2. "Aqui sempre montamos o planning primeiro" — plano aprovado antes de editar arquivo.
   Também em `feedback_planning_antes_de_editar` (memória pessoal).
3. "Eu já falei o que eu quero, que parte vc não entendeu" — **escutar a diretriz e
   reafirmá-la, não pedir de novo**.
4. Chrome MCP travava para ele; hoje funcionou parcialmente (JS sim, screenshot/resize não).

## Frente futura (registrada, NÃO agora)

Auditar robustez/segurança do que foi construído por outros modelos, usando o Meta Harness.

## Estado do git

Working tree de `apps/web` **modificado e não commitado** (o trabalho acima). Último commit:
`36c01ff`. A leva antiga (tentativa 5 reprovada + mudanças não validadas de 30/07) está em
**`stash@{0}`** — não descartada.

## Pendências herdadas (frentes separadas)

`recurrence` ignorado em `dashboard_use_cases.py:107` (eventos anuais somem); card esconde o
ano do evento; descrições truncam. Ver `mem:planning/responsividade-dashboard_20260730`.
