# Extrair spec de uma imagem de referência

Objetivo: transformar a imagem em `reference-spec.json` conforme
`schemas/visual-spec.schema.json`.

## Regra que vale mais que todas as outras

**Só registre o que você consegue medir. Campo ausente não é comparado; campo chutado
gera finding falso e empurra a correção para o lado errado.**

Na dúvida entre "acho que a fonte é 36px" e omitir `fontSize`, omita. Um spec com 8
propriedades confiáveis é melhor que um com 30 propriedades incertas.

## Passo 1 — dimensões reais da imagem

Antes de estimar qualquer coisa, obtenha as dimensões em pixels:

```bash
node -e "const{PNG}=require('pngjs');const p=PNG.sync.read(require('fs').readFileSync('ref.png'));console.log(p.width,p.height)"
```

Isso ancora todas as medidas seguintes. Sem isso você estima proporções sobre uma escala
desconhecida.

## Passo 2 — por padrão, NÃO registre tamanhos

O objetivo é **layout, cores e tipografia** — não igualar dimensões. A referência e o
render raramente têm a mesma largura, e isso não é defeito.

- **Padrão**: omita `canvas` e omita `bounds`.
- **Exceção**: só registre `bounds` se referência e render estiverem comprovadamente na
  mesma escala e você quiser travar posição.

Registrar dimensões de um mockup em escala diferente gera findings `high` falsos que
afogam os achados reais.

## Passo 3 — o que extrair, em ordem de confiabilidade

| Confiança | O que | Como |
| --- | --- | --- |
| Alta | Textos | Leia literalmente, incluindo acentos e símbolos (`58,2%`, não `58.2%`) |
| Alta | Cores | Identifique o hex; compare com os tokens `--ft-*` do `design-system.css` e prefira o token quando bater |
| Alta | Hierarquia | Ordem e agrupamento dos elementos |
| Média | Font weight | Regular vs semibold vs bold é perceptível; 500 vs 600 não é |
| Média | Proporções | Razão entre tamanhos ("o valor é ~2x o rótulo") |
| Baixa | fontSize exato | Só se houver referência de escala confiável |
| Baixa | Espaçamentos finos | Diferenças de 2-4px não são medíveis a olho |

## Passo 4 — ancorar no DOM

Cada elemento deve ter `match` apontando para uma classe real do componente:

```json
{ "id": "gauge-status", "match": ".ft-gauge-status", "text": "Atenção ao comprometimento" }
```

Descubra as classes disponíveis rodando `capture.js` primeiro e lendo o `actual-spec.json`.
Elementos sem `match` só casam por texto — o que falha em ícones, barras e formas.

## Passo 5 — SVG

Para gauges e gráficos, descreva a **geometria pretendida**, não o pixel:

- ângulo inicial e final do arco;
- espessura do traço e `linecap`;
- cores de cada segmento;
- onde o valor numérico fica em relação ao arco.

O componente deve permanecer dinâmico (arco calculado a partir do valor). Nunca proponha
substituir um gauge funcional por imagem estática.

## Exemplo mínimo

```json
{
  "texts": ["Comprometimento da renda", "58,2%", "do rendimento"],
  "elements": [
    {
      "id": "title",
      "match": ".ft-card-title",
      "text": "Comprometimento da renda",
      "typography": { "fontSize": 16, "fontWeight": 600 },
      "color": "#F7F9FC"
    },
    {
      "id": "gauge-value",
      "match": ".ft-gauge-svg-number",
      "text": "58,2%",
      "typography": { "fontWeight": 700 }
    }
  ]
}
```

Note o que foi omitido: `canvas`, todos os `bounds` e o `fontSize` do valor (não medível
com confiança). Isso é correto, não incompleto — o spec compara layout, cor e tipografia,
não tamanho.
