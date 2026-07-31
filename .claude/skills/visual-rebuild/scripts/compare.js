/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

/**
 * Compara o spec da referência com o spec extraído do DOM e produz findings
 * acionáveis. Opcionalmente faz regressão pixel a pixel entre dois renders
 * MEUS (antes/depois) — nunca contra o mockup, cujo recorte e escala não batem.
 *
 * Uso:
 *   node compare.js --reference ref-spec.json --actual .visual/x/actual-spec.json \
 *                   --out .visual/x/report.json
 *   node compare.js ... --baseline .visual/x/prev.png --current .visual/x/actual.png
 */

const fs = require("fs");
const path = require("path");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    if (!argv[i].startsWith("--")) continue;
    args[argv[i].slice(2)] = argv[i + 1];
  }
  return args;
}

const args = parseArgs(process.argv);

const DEFAULT_CRITERIA = {
  maxPositionDiffPx: 2,
  maxDimensionDiffPx: 2,
  maxFontSizeDiffPx: 1,
  maxColorDistance: 8,
  maxDifferentPixelRatio: 0.0025,
};

/** "rgb(49, 230, 174)" | "#31E6AE" -> [r,g,b] */
function toRgb(value) {
  if (!value) return null;
  const s = String(value).trim();
  const hex = s.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    let h = hex[1];
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  }
  const m = s.match(/rgba?\(([^)]+)\)/);
  if (m) return m[1].split(",").slice(0, 3).map((n) => Math.round(parseFloat(n)));
  return null;
}

function colorDistance(a, b) {
  const x = toRgb(a);
  const y = toRgb(b);
  if (!x || !y) return null;
  // distância euclidiana ponderada (aproximação perceptual barata)
  const rMean = (x[0] + y[0]) / 2;
  const dr = x[0] - y[0];
  const dg = x[1] - y[1];
  const db = x[2] - y[2];
  return Math.sqrt(
    (2 + rMean / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rMean) / 256) * db * db
  );
}

function normalizeText(t) {
  return String(t || "").replace(/\s+/g, " ").trim().toLowerCase();
}

/**
 * Casa um elemento da referência com um do DOM.
 * Prioridade: hint explícito (`match`) > texto idêntico > texto normalizado.
 */
function findActual(refEl, actualElements) {
  if (refEl.match) {
    const needle = refEl.match.replace(/^\./, "");
    const byClass = actualElements.find((a) => (a.cls || "").split(/\s+/).includes(needle));
    if (byClass) return { el: byClass, via: "match" };
  }
  if (refEl.text) {
    const target = normalizeText(refEl.text);
    const exact = actualElements.find((a) => normalizeText(a.text) === target);
    if (exact) return { el: exact, via: "text" };
    const partial = actualElements.find(
      (a) => a.text && (normalizeText(a.text).includes(target) || target.includes(normalizeText(a.text)))
    );
    if (partial) return { el: partial, via: "text-partial" };
  }
  return null;
}

function severityFor(delta, tolerance) {
  const abs = Math.abs(delta);
  if (abs <= tolerance) return null;
  if (abs <= tolerance * 3) return "medium";
  return "high";
}

function compareSpecs(reference, actual, criteria) {
  const findings = [];
  const actualElements = actual.elements || [];

  // ---- semântico: textos presentes/ausentes ----
  const refTexts = (reference.texts || reference.elements?.filter((e) => e.text).map((e) => e.text) || [])
    .map(normalizeText)
    .filter(Boolean);
  const actTexts = (actual.texts || []).map(normalizeText).filter(Boolean);

  const missingTexts = refTexts.filter((t) => !actTexts.some((a) => a === t || a.includes(t)));
  for (const t of missingTexts) {
    findings.push({
      type: "content",
      severity: "high",
      element: t,
      message: `Texto da referência não encontrado no render: "${t}"`,
    });
  }

  // ---- truncamento: independe da referência, é sempre defeito ----
  for (const t of actual.truncated || []) {
    findings.push({
      type: "layout",
      severity: "high",
      element: t.cls || t.text,
      message: `Texto cortado por falta de espaço: "${t.text}" (precisa de ${t.scrollWidth}px, tem ${t.clientWidth}px)`,
      expected: t.scrollWidth,
      actual: t.clientWidth,
      delta: t.clientWidth - t.scrollWidth,
    });
  }

  // ---- canvas ----
  if (reference.canvas && actual.canvas) {
    for (const dim of ["width", "height"]) {
      // Referência pode omitir uma dimensão de propósito (escala diferente).
      if (typeof reference.canvas[dim] !== "number") continue;
      const d = actual.canvas[dim] - reference.canvas[dim];
      const sev = severityFor(d, criteria.maxDimensionDiffPx);
      if (sev) {
        findings.push({
          type: "dimensions",
          severity: sev,
          element: "canvas",
          message: `Canvas ${dim}: esperado ${reference.canvas[dim]}px, atual ${actual.canvas[dim]}px`,
          expected: reference.canvas[dim],
          actual: actual.canvas[dim],
          delta: d,
        });
      }
    }
  }

  // ---- estrutural: elemento a elemento ----
  let matched = 0;
  for (const refEl of reference.elements || []) {
    const hit = findActual(refEl, actualElements);
    if (!hit) {
      findings.push({
        type: "content",
        severity: "high",
        element: refEl.id || refEl.text || refEl.match || "?",
        message: `Elemento da referência não localizado no DOM`,
      });
      continue;
    }
    matched++;
    const a = hit.el;
    const id = refEl.id || refEl.text || refEl.match;

    if (refEl.bounds && a.bounds) {
      for (const [key, type, tol] of [
        ["x", "position", criteria.maxPositionDiffPx],
        ["y", "position", criteria.maxPositionDiffPx],
        ["w", "dimensions", criteria.maxDimensionDiffPx],
        ["h", "dimensions", criteria.maxDimensionDiffPx],
      ]) {
        if (refEl.bounds[key] === undefined) continue;
        const d = a.bounds[key] - refEl.bounds[key];
        const sev = severityFor(d, tol);
        if (sev) {
          findings.push({
            type,
            severity: sev,
            element: id,
            message: `${key}: esperado ${refEl.bounds[key]}px, atual ${a.bounds[key]}px (${d > 0 ? "+" : ""}${d.toFixed(1)}px)`,
            expected: refEl.bounds[key],
            actual: a.bounds[key],
            delta: Number(d.toFixed(2)),
          });
        }
      }
    }

    if (refEl.typography && a.typography) {
      const rt = refEl.typography;
      const at = a.typography;
      if (rt.fontSize !== undefined) {
        const d = at.fontSize - rt.fontSize;
        const sev = severityFor(d, criteria.maxFontSizeDiffPx);
        if (sev) {
          findings.push({
            type: "typography",
            severity: sev,
            element: id,
            message: `fontSize: esperado ${rt.fontSize}px, atual ${at.fontSize}px`,
            expected: rt.fontSize,
            actual: at.fontSize,
            delta: Number(d.toFixed(2)),
          });
        }
      }
      if (rt.fontWeight !== undefined && Number(rt.fontWeight) !== Number(at.fontWeight)) {
        findings.push({
          type: "typography",
          severity: "medium",
          element: id,
          message: `fontWeight: esperado ${rt.fontWeight}, atual ${at.fontWeight}`,
          expected: rt.fontWeight,
          actual: at.fontWeight,
        });
      }
      if (rt.fontFamily && at.fontFamily && rt.fontFamily !== at.fontFamily) {
        findings.push({
          type: "typography",
          severity: "medium",
          element: id,
          message: `fontFamily: esperado ${rt.fontFamily}, atual ${at.fontFamily}`,
          expected: rt.fontFamily,
          actual: at.fontFamily,
        });
      }
    }

    if (refEl.color && a.color) {
      const dist = colorDistance(refEl.color, a.color);
      if (dist !== null && dist > criteria.maxColorDistance) {
        findings.push({
          type: "color",
          severity: dist > criteria.maxColorDistance * 4 ? "high" : "medium",
          element: id,
          message: `color: esperado ${refEl.color}, atual ${a.color} (distância ${dist.toFixed(1)})`,
          expected: refEl.color,
          actual: a.color,
          delta: Number(dist.toFixed(1)),
        });
      }
    }
  }

  return { findings, matched, refElementCount: (reference.elements || []).length };
}

/**
 * Este script roda de fora de apps/web, onde as dependências estão instaladas.
 * `require` normal não as acha, e `import()` de ESM ignora NODE_PATH — então
 * resolvemos o caminho explicitamente a partir de roots conhecidos.
 */
const DEP_ROOTS = [
  process.cwd(),
  path.resolve(__dirname, "../../../../apps/web"),
  path.resolve(__dirname, "../../../.."),
];

function resolveDep(name) {
  const { createRequire } = require("module");
  for (const root of DEP_ROOTS) {
    try {
      return createRequire(path.join(root, "package.json")).resolve(name);
    } catch {
      /* tenta o próximo root */
    }
  }
  throw new Error(
    `dependência "${name}" não encontrada. Instale em apps/web: npm install -D pixelmatch pngjs`
  );
}

async function pixelRegression(baselinePath, currentPath, diffPath, criteria) {
  const { pathToFileURL } = require("url");
  const { PNG } = require(resolveDep("pngjs"));
  const mod = await import(pathToFileURL(resolveDep("pixelmatch")).href);
  const pixelmatch = mod.default || mod;

  const a = PNG.sync.read(fs.readFileSync(baselinePath));
  const b = PNG.sync.read(fs.readFileSync(currentPath));

  if (a.width !== b.width || a.height !== b.height) {
    return {
      comparable: false,
      reason: `dimensões diferentes: ${a.width}x${a.height} vs ${b.width}x${b.height}`,
    };
  }

  const diff = new PNG({ width: a.width, height: a.height });
  const differentPixels = pixelmatch(a.data, b.data, diff.data, a.width, a.height, {
    threshold: 0.1,
    includeAA: false,
  });
  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const total = a.width * a.height;
  const ratio = differentPixels / total;
  return {
    comparable: true,
    differentPixels,
    totalPixels: total,
    differentPixelRatio: Number(ratio.toFixed(6)),
    withinTolerance: ratio <= criteria.maxDifferentPixelRatio,
    diffImage: diffPath,
  };
}

(async () => {
  const criteria = { ...DEFAULT_CRITERIA };
  if (args.criteria && fs.existsSync(args.criteria)) {
    Object.assign(criteria, JSON.parse(fs.readFileSync(args.criteria, "utf8")));
  }

  const report = { criteria, generatedAt: new Date().toISOString() };

  if (args.reference && args.actual) {
    const reference = JSON.parse(fs.readFileSync(args.reference, "utf8"));
    const actual = JSON.parse(fs.readFileSync(args.actual, "utf8"));
    const { findings, matched, refElementCount } = compareSpecs(reference, actual, criteria);

    report.structural = {
      refElementCount,
      matched,
      matchRate: refElementCount ? Number((matched / refElementCount).toFixed(3)) : null,
    };
    report.findings = findings.sort((a, b) => {
      const order = { high: 0, medium: 1, low: 2 };
      return order[a.severity] - order[b.severity];
    });
  }

  if (args.baseline && args.current) {
    const diffPath = args.diff || path.join(path.dirname(args.current), "diff.png");
    report.pixelRegression = await pixelRegression(args.baseline, args.current, diffPath, criteria);
  }

  const findings = report.findings || [];
  const high = findings.filter((f) => f.severity === "high").length;
  const medium = findings.filter((f) => f.severity === "medium").length;

  report.summary = {
    high,
    medium,
    total: findings.length,
    status: high === 0 && medium === 0 ? "approved" : high === 0 ? "close" : "needs-work",
  };

  if (args.out) {
    fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
    fs.writeFileSync(args.out, JSON.stringify(report, null, 2));
  }

  console.log(JSON.stringify(report, null, 2));
  process.exit(report.summary.status === "needs-work" ? 1 : 0);
})().catch((e) => {
  console.error("FALHOU:", e.message);
  process.exit(2);
});
