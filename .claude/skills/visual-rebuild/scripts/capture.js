/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

/**
 * Captura determinística de um componente + extração do spec visual via DOM.
 *
 * O DOM é a fonte de verdade do que foi renderizado: geometria, tipografia e
 * cores saem exatas, sem interpretação visual. Visão só é usada do outro lado
 * da comparação, para ler a imagem de referência.
 *
 * Uso:
 *   node capture.js --selector ".ft-analytics-card:has(.ft-gauge-stack)" \
 *                   --route "/dashboard/<id>" --out .visual/gauge
 */

const fs = require("fs");
const path = require("path");

/**
 * O script roda de fora de apps/web, onde as dependências estão instaladas,
 * então `require` normal não as encontra. Resolvemos a partir de roots conhecidos.
 */
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
      /* tenta o próximo root */
    }
  }
  throw new Error(`dependência "${name}" não encontrada. Rode a partir de apps/web.`);
}

const { chromium } = require(resolveDep("@playwright/test"));

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    if (!argv[i].startsWith("--")) continue;
    args[argv[i].slice(2)] = argv[i + 1];
  }
  return args;
}

const args = parseArgs(process.argv);
const BASE = args.base || process.env.VISUAL_BASE_URL || "http://localhost:3001";
const ROUTE = args.route;
const SELECTOR = args.selector;
const OUT = path.resolve(args.out || ".visual/capture");
const WIDTH = Number(args.width || 1440);
const HEIGHT = Number(args.height || 900);
const LABEL = args.label || "actual";

if (!ROUTE || !SELECTOR) {
  console.error("erro: --route e --selector são obrigatórios");
  process.exit(2);
}

/** Executado dentro da página. Extrai o spec do elemento alvo. */
function extractSpec(sel) {
  const target = document.querySelector(sel);
  if (!target) return null;

  const base = target.getBoundingClientRect();
  const px = (v) => Math.round(parseFloat(v) * 100) / 100;

  const describe = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    const leaf = el.children.length === 0;
    const node = {
      tag: el.tagName.toLowerCase(),
      cls: typeof el.className === "string" ? el.className.trim() || undefined : undefined,
      bounds: {
        x: px(r.left - base.left),
        y: px(r.top - base.top),
        w: px(r.width),
        h: px(r.height),
      },
      typography: {
        fontFamily: s.fontFamily.split(",")[0].replace(/["']/g, ""),
        fontSize: px(s.fontSize),
        fontWeight: Number(s.fontWeight),
        lineHeight: s.lineHeight === "normal" ? "normal" : px(s.lineHeight),
      },
      color: s.color,
    };
    if (leaf) {
      const t = el.textContent.trim();
      if (t) node.text = t;
      // Texto cortado por ellipsis/overflow: o layout "passa" na comparação
      // estrutural mas fica ilegível. Precisa virar finding.
      if (t && el.scrollWidth > el.clientWidth + 1) {
        node.truncated = { scrollWidth: el.scrollWidth, clientWidth: el.clientWidth };
      }
    }
    if (s.backgroundColor !== "rgba(0, 0, 0, 0)") node.background = s.backgroundColor;
    if (s.borderRadius !== "0px") node.borderRadius = s.borderRadius;
    if (s.borderTopWidth !== "0px" || s.borderBottomWidth !== "0px") {
      node.border = `${s.borderTopWidth} ${s.borderTopStyle} ${s.borderTopColor}`;
      node.borderBottom = `${s.borderBottomWidth} ${s.borderBottomStyle} ${s.borderBottomColor}`;
    }
    if (s.boxShadow !== "none") node.boxShadow = s.boxShadow;
    return node;
  };

  const elements = [...target.querySelectorAll("*")]
    .filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0.5 && r.height > 0.5;
    })
    .map(describe);

  const svgs = [...target.querySelectorAll("svg")].map((svg) => {
    const r = svg.getBoundingClientRect();
    return {
      viewBox: svg.getAttribute("viewBox"),
      bounds: { x: px(r.left - base.left), y: px(r.top - base.top), w: px(r.width), h: px(r.height) },
      shapes: [...svg.querySelectorAll("path,circle,rect,line,text")].map((el) => {
        const s = getComputedStyle(el);
        const shape = { tag: el.tagName };
        const d = el.getAttribute("d");
        if (d) shape.d = d;
        if (el.tagName === "text") shape.text = el.textContent.trim();
        for (const attr of ["cx", "cy", "r", "x", "y", "x1", "y1", "x2", "y2"]) {
          const v = el.getAttribute(attr);
          if (v !== null) shape[attr] = v;
        }
        if (s.stroke !== "none") {
          shape.stroke = s.stroke;
          shape.strokeWidth = s.strokeWidth;
          shape.strokeLinecap = s.strokeLinecap;
        }
        if (s.fill !== "none") shape.fill = s.fill;
        return shape;
      }),
    };
  });

  const texts = elements.filter((e) => e.text).map((e) => e.text);
  const truncated = elements
    .filter((e) => e.truncated)
    .map((e) => ({ cls: e.cls, text: e.text, ...e.truncated }));

  return {
    canvas: { width: Math.round(base.width), height: Math.round(base.height) },
    texts,
    truncated,
    elements,
    svgs,
  };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    deviceScaleFactor: 1,
    locale: "pt-BR",
    colorScheme: "dark",
    reducedMotion: "reduce",
  });
  const page = await context.newPage();

  await page.goto(`${BASE}${ROUTE}`, { waitUntil: "domcontentloaded", timeout: 120000 });

  // Congela animações e transições: sem isso a captura varia entre execuções.
  await page.addStyleTag({
    content: `*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}`,
  });

  await page.waitForLoadState("networkidle", { timeout: 120000 });

  const target = page.locator(SELECTOR).first();
  await target.waitFor({ state: "visible", timeout: 60000 });
  await target.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);

  const pngPath = path.join(OUT, `${LABEL}.png`);
  await target.screenshot({ path: pngPath });

  const spec = await page.evaluate(extractSpec, SELECTOR);
  if (!spec) {
    console.error(`erro: seletor não encontrado no DOM: ${SELECTOR}`);
    await browser.close();
    process.exit(1);
  }

  spec.meta = {
    label: LABEL,
    route: ROUTE,
    selector: SELECTOR,
    viewport: { width: WIDTH, height: HEIGHT },
    capturedAt: new Date().toISOString(),
  };

  const specPath = path.join(OUT, `${LABEL}-spec.json`);
  fs.writeFileSync(specPath, JSON.stringify(spec, null, 2));

  console.log(JSON.stringify({
    ok: true,
    png: pngPath,
    spec: specPath,
    canvas: spec.canvas,
    elements: spec.elements.length,
    svgs: spec.svgs.length,
    texts: spec.texts.length,
  }, null, 2));

  await browser.close();
})().catch((e) => {
  console.error("FALHOU:", e.message);
  process.exit(1);
});
