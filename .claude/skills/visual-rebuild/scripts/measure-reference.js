/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

/**
 * Mede a imagem de referência em vez de estimá-la a olho.
 *
 * Visão serve para entender o QUE existe; ela é ruim para dizer QUANTO. Este
 * script extrai números reais do PNG: bounds do card, geometria do donut, cores
 * dominantes e linhas de texto. Assim o reference-spec deixa de ser um chute.
 *
 * Uso:
 *   node measure-reference.js --image ref.png [--out medidas.json]
 */

const fs = require("fs");
const path = require("path");

function resolveDep(name) {
  const { createRequire } = require("module");
  const roots = [
    process.cwd(),
    path.resolve(__dirname, "../../../../apps/web"),
    path.resolve(__dirname, "../../../.."),
  ];
  for (const root of roots) {
    try {
      return createRequire(path.join(root, "package.json")).resolve(name);
    } catch {
      /* próximo root */
    }
  }
  throw new Error(`dependência "${name}" não encontrada. Rode a partir de apps/web.`);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    if (!argv[i].startsWith("--")) continue;
    args[argv[i].slice(2)] = argv[i + 1];
  }
  return args;
}

const args = parseArgs(process.argv);
if (!args.image) {
  console.error("erro: --image é obrigatório");
  process.exit(2);
}

const { PNG } = require(resolveDep("pngjs"));
const png = PNG.sync.read(fs.readFileSync(path.resolve(args.image)));
const { width: W, height: H, data } = png;

const at = (x, y) => {
  const i = (W * y + x) << 2;
  return [data[i], data[i + 1], data[i + 2]];
};
const lum = ([r, g, b]) => 0.2126 * r + 0.7152 * g + 0.0722 * b;
const sat = ([r, g, b]) => {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  return max === 0 ? 0 : (max - min) / max;
};
const hex = ([r, g, b]) =>
  "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("").toUpperCase();

// ---- 1. fundo da página vs card ----
const pageBg = at(2, 2);
const centerBg = at(Math.floor(W / 2), Math.floor(H / 2));

/** Bounds do card: primeira/última linha e coluna que diferem do fundo da página. */
function cardBounds() {
  const differs = (p) => Math.abs(lum(p) - lum(pageBg)) > 3;
  let top = 0;
  let bottom = H - 1;
  let left = 0;
  let right = W - 1;
  const midX = Math.floor(W / 2);
  const midY = Math.floor(H / 2);
  while (top < H - 1 && !differs(at(midX, top))) top++;
  while (bottom > 0 && !differs(at(midX, bottom))) bottom--;
  while (left < W - 1 && !differs(at(left, midY))) left++;
  while (right > 0 && !differs(at(right, midY))) right--;
  return { x: left, y: top, w: right - left + 1, h: bottom - top + 1 };
}

const card = cardBounds();

// ---- 2. donut: pixels saturados formam o anel ----
const COLORED = (p) => sat(p) > 0.35 && lum(p) > 40;

let minX = W;
let maxX = -1;
let minY = H;
let maxY = -1;
for (let y = card.y; y < card.y + card.h; y++) {
  for (let x = card.x; x < card.x + card.w; x++) {
    if (!COLORED(at(x, y))) continue;
    // ignora a faixa do rodapé (link roxo) e possíveis dots pequenos da legenda
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
}

/** Refina o donut varrendo apenas a metade esquerda (onde ele está). */
function donutGeometry() {
  const halfX = card.x + Math.floor(card.w * 0.55);
  let dMinX = W;
  let dMaxX = -1;
  let dMinY = H;
  let dMaxY = -1;
  for (let y = card.y; y < card.y + card.h; y++) {
    for (let x = card.x; x < halfX; x++) {
      if (!COLORED(at(x, y))) continue;
      if (x < dMinX) dMinX = x;
      if (x > dMaxX) dMaxX = x;
      if (y < dMinY) dMinY = y;
      if (y > dMaxY) dMaxY = y;
    }
  }
  if (dMaxX < 0) return null;

  const cx = Math.round((dMinX + dMaxX) / 2);
  const cy = Math.round((dMinY + dMaxY) / 2);
  const outer = Math.round((dMaxX - dMinX + 1) / 2);

  // raio interno: do centro para a direita até achar cor saturada
  let inner = 0;
  for (let x = cx; x <= dMaxX; x++) {
    if (COLORED(at(x, cy))) {
      inner = x - cx;
      break;
    }
  }

  return {
    center: { x: cx, y: cy },
    outerRadius: outer,
    innerRadius: inner,
    diameter: dMaxX - dMinX + 1,
    innerRatio: inner && outer ? Number((inner / outer).toFixed(3)) : null,
    strokeWidth: outer - inner,
  };
}

const donut = donutGeometry();

// ---- 3. linhas de texto: agrupa linhas com pixels claros ----
function textRows(x0, x1, minLum = 90) {
  const rows = [];
  let run = null;
  for (let y = card.y; y < card.y + card.h; y++) {
    let count = 0;
    for (let x = x0; x < x1; x++) {
      const p = at(x, y);
      if (lum(p) > minLum && sat(p) < 0.45) count++;
    }
    const hasText = count >= 2;
    if (hasText && !run) run = { start: y, count };
    else if (hasText && run) run.count = Math.max(run.count, count);
    else if (!hasText && run) {
      if (y - run.start >= 4) rows.push({ y: run.start, height: y - run.start, px: run.count });
      run = null;
    }
  }
  return rows;
}

const headerRows = textRows(card.x + 8, card.x + card.w - 8).filter(
  (r) => r.y < (donut ? donut.center.y - donut.outerRadius : card.y + 120)
);

const legendX0 = donut ? donut.center.x + donut.outerRadius + 10 : card.x + Math.floor(card.w / 2);
const legendRows = textRows(legendX0, card.x + card.w - 8);

// ---- 4. cores dominantes do anel ----
function ringColors() {
  if (!donut) return [];
  const counts = new Map();
  const r = Math.round((donut.outerRadius + donut.innerRadius) / 2);
  for (let a = 0; a < 360; a += 2) {
    const rad = (a * Math.PI) / 180;
    const x = Math.round(donut.center.x + r * Math.cos(rad));
    const y = Math.round(donut.center.y + r * Math.sin(rad));
    if (x < 0 || y < 0 || x >= W || y >= H) continue;
    const p = at(x, y);
    if (!COLORED(p)) continue;
    const key = hex([p[0] & 0xf8, p[1] & 0xf8, p[2] & 0xf8]);
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([color, n]) => ({ color, samples: n }));
}

const result = {
  image: { width: W, height: H },
  pageBackground: hex(pageBg),
  cardBackgroundSample: hex(centerBg),
  card,
  donut: donut && {
    ...donut,
    // proporções são o que transfere entre escalas diferentes
    diameterOverCardWidth: Number((donut.diameter / card.w).toFixed(3)),
    centerOffsetXOverCardWidth: Number(((donut.center.x - card.x) / card.w).toFixed(3)),
  },
  ringColors: ringColors(),
  headerTextRows: headerRows,
  legendTextRows: legendRows,
  legendRowSpacing:
    legendRows.length > 1
      ? Number(
          (
            legendRows.slice(1).reduce((s, r, i) => s + (r.y - legendRows[i].y), 0) /
            (legendRows.length - 1)
          ).toFixed(1)
        )
      : null,
};

if (args.out) fs.writeFileSync(args.out, JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
