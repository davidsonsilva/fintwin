# Migração CSS→CVA do design system — FECHADA (2026-07-31)

## ESTADO ATUAL / PRÓXIMO PASSO

**CONCLUÍDA e commitada.** Encerra `mem:planning/design-system-css-para-cva-e-meta-harness_20260727`,
que havia parado no meio deixando dois candidatos nomeados.

Commits: `c248ec0` (IconChip + StatusCard) e `2d920d1` (`.ft-metric-icon` + `.ft-badge`).
Ambos validados visualmente pelo Davidson antes de entrar.

**Próximo passo (frente separada, NÃO iniciada)**: arquitetura de cards por papel —
MetricCard, EventsCard, AnalyticsCard, Sidebar. É layout, e o Davidson mandou parar:
*"Tem que parar com estes ajustes de card. Temos que migrar tudo antes."* A migração
acabou; a decisão de retomar layout é dele.

**Meta Harness: RODADO E APROVADO.** Sequência final:

| commit | veredito | findings |
|---|---|---|
| `c248ec0` IconChip + StatusCard | APPROVED | 0 |
| `2d920d1` metric-icon + badge | APPROVED_WITH_WARNINGS | 1 (real, corrigido) |
| `97d7a34` fix da curva de transição | APPROVED_WITH_WARNINGS | 1 (contrato, corrigido) |
| `f307492` sincroniza acceptance-criteria | APPROVED_WITH_WARNINGS | 2 (contrato, corrigidos) |
| `4c37d9e` critérios 2 e 9 verificáveis | **APPROVED** | **0** |

**O finding real que ele pegou** e eu não: `.ft-badge--link` usava
`transition: color 0.15s ease` e o componente saiu com `ease-in-out`. Curva diferente = hover
visivelmente diferente, ou seja, a migração não era neutra como o contrato afirmava. O Codex
verificou o CSS gerado depois da correção (`transition-timing-function: ease`). **Tailwind não
tem utilitário para a curva `ease` pura** (só `ease-in`/`ease-out`/`ease-in-out`) — usar
`ease-[ease]`. Lição: neutralidade visual inclui **curva e duração de transição**, não só
medida e cor.

**Os outros 3 findings foram todos no contrato, não no código** — e o padrão vale a pena:
o harness pega inconsistência entre documentos com a mesma eficácia que pega bug. Ele rejeitou
porque (a) `acceptance-criteria.md` ainda descrevia a slice de 27/07 enquanto
`current-slice.md` já descrevia esta, (b) o critério exigia "zero ocorrências" de seletores
que os próprios comentários citam, (c) o critério 9 dizia que toda `.ft-grid--*` fica intacta
enquanto o critério 1 autorizava mexer em `.ft-grid--indicators`.

**REGRA**: `current-slice.md` e `acceptance-criteria.md` são atualizados **juntos**. Contrato
desatualizado faz o Codex rejeitar código correto.

**LIMITAÇÃO REAL DO HARNESS neste ambiente** (aparece como NOT_VERIFIED em toda rodada, não é
falha desta slice): o Codex roda em sandbox e **não consegue executar teste nenhum** —
`pytest` falha porque o launcher da `.venv` aponta para um Python 3.12 ausente; `vitest` falha
com EPERM ao criar diretório temporário; `next build` falha com EPERM ao gravar
`.next/trace-build`. Na prática o harness valida diff, lint e tipos, **não a suíte**. Vale
consertar a venv se quiser cobertura de verdade.
`.serena/memories/_index.md` ainda não existe neste projeto — o `audit-projeto.ps1` do
`ai-dev-template` já cobra (ver `mem:planning/temp_20260731_115424`).

## O que ficou pronto

| componente | substitui | usos |
|---|---|---|
| `IconChip` | `.ft-status-icon` (38px), `.ft-metric-icon` (48px) + 4 modificadores | 9 |
| `StatusCard` | `.ft-status-card`, `.ft-status-title`, `.ft-status-description` | 6 |
| `Badge` | `.ft-badge` + `--success/--warning/--purple/--danger/--link` | 6 |

`design-system.css` perdeu ~100 linhas. Zero ocorrências de `.ft-status-*`,
`.ft-metric-icon`, `.ft-badge` no código.

## A LIÇÃO CENTRAL DESTA SESSÃO

**Migração é troca de estrutura com ZERO mudança visual.**

A primeira versão do `StatusCard` embutiu uma container query que mandava o valor para a
direita do rótulo quando havia espaço. Isso **não existia** no `.ft-status-card`, que sempre
empilhou. Com valores longos ("Sem déficit projetado (12 meses, cenário provável)") o card
ficou visivelmente quebrado, e o Davidson pegou de imediato:

> "O que eu vejo aqui agora é um card totalmente quebrado (...) Está tudo na mesma linha,
> ficou horrível. Tem que parar com estes ajustes de card. Temos que migrar tudo antes."

Eu não tinha feito uma migração — tinha feito **migração + um redesign que ninguém pediu**,
e os dois misturados num commit só. Refazer como cópia fiel expôs mais **duas infidelidades**
que ninguém tinha visto:

1. **Borda no chip errado.** `.ft-status-icon` (38px) não tem borda; só `.ft-metric-icon`
   (48px) tem `border: 1px solid transparent`. Eu tinha posto na base do CVA, então o chip
   de 38px ganhou um anel que não existia. **A borda mora na variante `md`, não na base.**
2. **Glifo encolhido.** O CSS nunca amarrou glifo a chip: 38px aparece com glifo de 18px no
   dashboard e de **22px** no radar de fragilidade. Eu tinha fixado 18 para todo `sm`. Daí o
   prop `iconSize` opcional em `IconChip` — o default cobre o caso comum.

**Método que funcionou** (usar sempre em migração):
`rtk proxy "git show HEAD:<arquivo>"` para extrair o CSS *e* o JSX originais e comparar
propriedade por propriedade antes de escrever o componente. Ler só o CSS não basta — o JSX
carrega decisões (tamanho de glifo, classes combinadas) que o CSS não mostra.

## Decisões registradas

- **`margin-top: 10px` do `.ft-badge` foi mantido** no componente. É espaçamento externo
  embutido no badge, discutível, mas tirar seria mudança visual. Fica para a frente de layout.
- **`grid-auto-rows: minmax(0,1fr)` removido de `.ft-grid--indicators`** — única mudança
  visual intencional dos dois commits. Era a causa do bug original: fazia todas as linhas
  ficarem iguais à mais alta, então o card de eventos (altura em função de quantos eventos o
  usuário tem) esticava os 6 cards de status para 416px na faixa de 2 colunas. Validado pelo
  Davidson.
- **Tipagem substituindo string mágica**: `FragilityList` guardava `badge: "ft-badge--danger"`
  (nome de classe); passou a guardar `tone: BadgeTone`. Classe errada era silêncio; tom errado
  não compila. Mesma coisa em `page.tsx`, onde a variante vinha por template string.
- **`badgeVariants()` direto no `className`** quando o badge precisa ser outro elemento (o
  `<Link>` do StatusCard) — mesmo padrão que `buttonVariants` já usava. `Badge` renderiza
  `<span>` e só.
- **REGRA DURA mantida**: componente novo só entra se a regra CSS equivalente sair no mesmo
  commit. O ganho vem de deletar CSS, não de somar abstração.
- **`ui/card` (shadcn) permanece** no onboarding/simulações/planos. Decisão deliberada de
  27/07 — **não reabrir**.

## NÃO repetir

- `min-h-[2lh]` — Tailwind descarta a unidade `lh` (Chrome suporta; medido 38.4375px)
- `min-h-[2.75em]` — a regra é gerada e o seletor casa, mas computa `0px`. Inexplicado após
  4 tentativas. Se precisar travar altura, usar px explícito.
- Não misturar melhoria visual com migração no mesmo passo. Foi a causa raiz do retrabalho.

## Gotchas de ambiente

- `web` do docker-compose **não tem hot reload**: `docker compose build web && docker compose
  up -d web` antes de qualquer verificação visual (`mem:gotcha/docker-web-sem-hot-reload`).
- `git diff | grep` é filtrado pelo rtk e devolve "--- Changes ---". Usar
  `rtk proxy "git show ..."` para conteúdo bruto.
