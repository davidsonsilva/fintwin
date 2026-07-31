---
name: visual-rebuild
description: Reconstrói ou valida um componente da UI contra uma imagem de referência, usando captura determinística via Playwright, extração de spec pelo DOM e comparação numérica com findings acionáveis. Use quando houver um mockup/screenshot de referência e for preciso aproximar a implementação dele, ou para validar que uma tela não regrediu visualmente.
---

# visual-rebuild

Sistema de visual regression autocorretivo para o FinTwin AI.

## O objetivo NÃO é igualar tamanhos

A referência quase nunca tem a mesma largura do componente renderizado, e não precisa
ter. O que se compara é **layout (estrutura e ordem), cores e tipografia**.

Portanto, por padrão:

- **omita `canvas`** no `reference-spec.json`;
- **omita `bounds`** dos elementos;
- compare `typography`, `color`, presença/ausência de elementos e truncamento.

Só registre `bounds` quando referência e render estiverem comprovadamente na mesma
escala e você quiser travar posição — o que é exceção, não regra. Dimensão divergente
vira finding `high` e afoga os achados que importam.

## Princípio central: a comparação é assimétrica

Não use visão para avaliar o que foi renderizado. O DOM já contém a verdade exata
(geometria, tipografia, cores). Visão só é necessária para ler a **imagem de referência**,
que é o único lado onde não há dados estruturados.

```
imagem de referência ──[visão]──> reference-spec.json  ┐
                                                        ├─> diff numérico ─> findings
app rodando ─────────[DOM/Playwright]──> actual-spec.json ┘
```

Tentar "olhar o screenshot e adivinhar o que está errado" foi o que causou ~10 iterações
falhas no gauge de comprometimento da renda. Medir resolve em 1.

## Pré-requisitos

O loop de correção precisa de HMR. O container `web` **não tem bind mount** (só `COPY` no
build), então mudanças no host não chegam nele. Rode o dev server no host:

```bash
cd apps/web && PORT=3001 npm run dev
```

A API continua no Docker (`localhost:8000`). Use o Docker apenas para a validação final.

Para obter um `profileId` determinístico, use o seed de demonstração
(`/onboarding` → "Carregar dados de demonstração") ou reaproveite um perfil existente.

## Fluxo

### 1. Extrair o spec da referência

Analise a imagem e produza um `reference-spec.json` seguindo
`schemas/visual-spec.schema.json`. Siga `prompts/extract-reference.md` — ele define como
medir e o que NÃO inventar.

Só inclua propriedades que você consegue medir com confiança na imagem. Um campo ausente
não é comparado; um campo chutado gera finding falso e manda a correção para o lado errado.

Use `match` para ancorar cada elemento a uma classe do DOM (`"match": ".ft-gauge-status"`).
Sem isso, o casamento cai para o texto, que falha em elementos sem texto.

### 2. Capturar o render atual

Rode **a partir de `apps/web`** (é onde as dependências estão) e com
`MSYS_NO_PATHCONV=1` (no Git Bash do Windows, sem isso o `/dashboard/...` vira
um caminho `C:/Program Files/Git/dashboard/...` e a navegação falha):

```bash
cd apps/web
MSYS_NO_PATHCONV=1 node ../../.claude/skills/visual-rebuild/scripts/capture.js \
  --route "/dashboard/<profileId>" \
  --selector ".ft-analytics-card:has(.ft-gauge-stack)" \
  --out ../../.visual/gauge \
  --label actual
```

Gera `actual.png` e `actual-spec.json`. A captura fixa viewport, `deviceScaleFactor: 1`,
locale pt-BR, `colorScheme: dark` e desliga animações/transições — sem isso a mesma tela
produz imagens diferentes entre execuções.

`--selector` aceita qualquer seletor CSS do Playwright, inclusive `:has()`.

### 3. Comparar

```bash
cd apps/web
MSYS_NO_PATHCONV=1 node ../../.claude/skills/visual-rebuild/scripts/compare.js \
  --reference ../../.visual/gauge/reference-spec.json \
  --actual ../../.visual/gauge/actual-spec.json \
  --out ../../.visual/gauge/report.json
```

Saída: findings ordenados por severidade, com `expected`, `actual` e `delta` numérico.
Exit code 1 quando há finding `high`.

Categorias: `layout`, `position`, `dimensions`, `typography`, `color`, `content`.

`layout` inclui **truncamento**: texto cortado por falta de espaço (`scrollWidth >
clientWidth`). É detectado sempre, independente da referência — um card pode passar em
toda a comparação estrutural e ainda assim mostrar "Ali..." no lugar de "Alimentação".

**Valide em mais de um viewport.** A largura do card muda com a grade do dashboard
(1920 → 530px; 1440 → 368px), e um layout que cabe num não cabe no outro. Prefira
container queries a media queries: o que manda é a largura do card, não a da tela.

### 4. Corrigir

Aplique **apenas** as propriedades apontadas pelos findings. Cada finding traz o delta
exato — não é preciso estimar. Um finding de `y: +8px` vira uma mudança de 8px, não uma
tentativa.

Prefira ajustar o token/classe no `design-system.css` a inserir estilo inline: a mudança
precisa valer para todas as instâncias do componente.

### 5. Iterar

Repita 2→4. Pare quando o status for `approved`, ou após 6 iterações.

Se duas iterações seguidas produzirem o mesmo finding com o mesmo delta, **pare**: a
propriedade que você está mudando não é a que controla aquele valor. Investigue o CSS
computado antes de tentar de novo.

### 6. Regressão pixel a pixel (opcional)

Só entre renders seus — nunca contra o mockup, cujo recorte e escala não batem:

```bash
cd apps/web
MSYS_NO_PATHCONV=1 node ../../.claude/skills/visual-rebuild/scripts/compare.js \
  --baseline ../../.visual/gauge/before.png \
  --current ../../.visual/gauge/actual.png \
  --diff ../../.visual/gauge/diff.png
```

Útil para confirmar que uma correção não alterou nada além do pretendido.

Duas capturas seguidas sem mudança de código devem dar `differentPixels: 0`. Se derem
qualquer outro valor, há algo não determinístico na tela (animação, dado que varia,
fonte carregando tarde) — resolva isso **antes** de confiar em qualquer diff.

## Critérios de aprovação

Padrão (sobrescreva com `--criteria arquivo.json`):

```json
{
  "maxPositionDiffPx": 2,
  "maxDimensionDiffPx": 2,
  "maxFontSizeDiffPx": 1,
  "maxColorDistance": 8,
  "maxDifferentPixelRatio": 0.0025
}
```

Afrouxe tolerâncias quando a referência for um mockup em escala diferente — nesse caso
posições absolutas têm pouco valor e o que importa são proporções, tipografia e cores.

## Limitações

- Comparação contra mockup é confiável em **tipografia, cores e proporções**; posições
  absolutas dependem de a referência estar na mesma escala do render.
- Antialiasing de sombras e gradientes gera milhares de pixels diferentes sem erro visual
  real. Por isso o pixel a pixel é regressão, não critério de aceite contra referência.
- O render do host pode diferir levemente do container (fontes do SO). Valide o resultado
  final no Docker.
