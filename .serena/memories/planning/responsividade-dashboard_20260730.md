# Responsividade do dashboard — diagnóstico feito, correção NÃO fechada (2026-07-30)

> **SUPERSEDED em 2026-07-31.** A causa foi explicada de verdade (etapa de expansão por
> spanning item no track sizing do CSS Grid) e a discussão continua em
> `mem:planning/temp_card-variantes-e-grid-indicadores_20260731`. O mecanismo genérico
> ficou em `mem:global/css-grid-spanning-item-dita-altura-das-linhas`.
> **Não retome por esta memória** — as hipóteses abaixo (`min-height: 0`,
> `grid-auto-rows: min-content`) foram todas refutadas. Leia a temp primeiro.

Status: **em aberto**. Diagnóstico sólido, correção tentada 3x e **não funcionou**.
Retomar por aqui.

## O problema (relato do Davidson)

"Tem card com duas linhas ocupando o espaço de um card de 5 linhas" / "tem um buraco no
dashboard". Os 6 `.ft-status-card` da linha de indicadores são esticados para ~232px cada,
com o conteúdo (ícone + 2 linhas) grudado no topo e o resto vazio.

## Causa raiz identificada

`.ft-grid--indicators` tem 3 colunas de status + o card `.ft-indicators-events` na 4ª
coluna com `grid-row: 1 / span 2`. Quem determina a altura das linhas é o card de eventos,
e não os cards de status — **causalidade invertida em relação à referência**.

Na referência (`imagens/proposta-de-layout.png`): os status são compactos e o card de
eventos (com 1 evento) **absorve a sobra**, deixando um vão entre o evento e o botão.

A altura do card de eventos é função do **dado** (`upcoming_events`, até 5). Ou seja, um
dado do usuário controla o layout de sete cards. Hoje são 3 eventos; quando o `recurrence`
for corrigido serão mais.

## Por que o agente implementou assim

Memória `mem:planning/redistribuicao-projecao-autonomia_20260728` item 3 diz que ele
copiou "igual ao padrão da imagem de referência". Copiou a **geometria** (4ª coluna,
span 2) — que está certa — mas não a **causalidade**, que é invisível numa imagem
estática: "status baixos + eventos alto" e "eventos alto esticando os status" produzem o
mesmo pixel. Ele validou uma vez, com um conjunto de dados. Lição: **validar layout com
mais de um volume de dados**.

## Tentativas que NÃO resolveram (todas verificadas no container, CSS chega correto)

1. Remover `grid-auto-rows: minmax(0, 1fr)` → altura da linha continuou 232px
2. `min-height: 0` em `.ft-indicators-events .ft-event-list` (item de flex nasce com
   `min-height: auto` e não encolhe; o `overflow-y: auto` que já existia nunca rolava)
   → sem efeito
3. `min-height: 0` também em `.ft-indicators-events` (item de **grid** também nasce com
   `min-height: auto`) → sem efeito
4. `grid-auto-rows: min-content` (linha `auto` é dimensionada por max-content, então o
   spanner contribui com a altura cheia da lista) → **ainda 534px de altura total**

Confirmado via `docker exec ... grep` que as regras estão no CSS servido. O CSS aplica; a
altura não muda. **A hipótese sobre track sizing ainda não explica o número.** Próximo
passo: medir a contribuição real via `getComputedStyle`/devtools em vez de continuar
teorizando — ou tirar o card de eventos do grid (grid próprio ao lado), que elimina o
acoplamento por construção em vez de tentar neutralizá-lo.

## Outras mudanças aplicadas na mesma leva (NÃO validadas pelo Davidson)

- Removida a `border-bottom` de `.ft-card-header` (a referência não tem essa linha; o
  código já tinha um override desfazendo-a no card de eventos — sinal de que a regra geral
  estava errada). O override morto foi removido junto.
- Removido o `min-height: 420px` mágico de `.ft-analytics-card` (altura igual passa a vir
  do grid).
- `mt-3` → `mt-auto` no botão "Ver todos os eventos" (`DashboardView.tsx`).

Tudo isso está **não commitado** na cópia de trabalho. `git checkout -- apps/web` volta ao
último estado validado.

## Defeitos de domínio descobertos no caminho (frentes separadas, não iniciadas)

1. **`recurrence` é ignorado** em `dashboard_use_cases.py:107`:
   `sorted(e for e in events if e.date >= today)[:5]`. Evento `YEARLY` cuja data já passou
   **some para sempre** em vez de rolar para a próxima ocorrência. Prova: o perfil de demo
   tem IPTU (10/02/2026) e IPVA (20/01/2026) anuais que sumiram do card. Bomba-relógio: em
   16/11/2026 a manutenção do veículo some do dashboard do Davidson.
2. **O card esconde o ano** (`DashboardView.tsx:352-355` mostra só dia + mês abreviado).
   "20 JAN" não diz se é daqui a 6 ou 18 meses. Foi por isso que o Davidson não conseguiu
   responder olhando a tela.
3. Descrições dos eventos truncam no card ("Manute prev...", "IPVA e licencia").

## Estado do git ao fim da sessão

5 commits criados em `master`, **nada enviado ao remoto** (a pedido dele):
`3cb8660` perfil/nome · `9ea45cb` CORS · `5e136d3` dashboard/design system ·
`9409ded` linguagem acessível · `36c01ff` skill + memórias

`imagens/` e `graphify-out/` (~10MB) ficaram **fora** de propósito: são referência que ele
vai apagar, e arquivo untracked não corre risco em `git checkout`.

Perfil que o Davidson usa: `057943a0-6187-475c-9411-7dc78ef50cf0` ("Rafael", 3 eventos
futuros). O de demo com dados antigos é `d5b17141-43c8-4758-91c7-d516532d475a`.

Contexto: `mem:planning/skill-visual-rebuild_20260730`
