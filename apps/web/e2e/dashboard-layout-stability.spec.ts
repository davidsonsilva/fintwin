import { expect, test, type Page } from "@playwright/test";

/**
 * Regressão do bug de oscilação da fileira de indicadores (6 cards compactos).
 *
 * O layout antigo escolhia número de colunas e posição do card de eventos
 * pontuando ALTURAS medidas por `ResizeObserver`. Como a altura de um card
 * depende da largura da coluna — e a largura da coluna é justamente o que a
 * decisão altera — o sistema não tinha ponto fixo: media alto em 3 colunas,
 * migrava para 2, media baixo, voltava para 3, indefinidamente.
 *
 * A regra que estes testes fixam: **para a mesma largura de container e o mesmo
 * conjunto de cards, a composição tem que ser sempre idêntica** — não importa
 * quanto tempo passou nem por quais larguras se chegou até ali.
 */

const CARD = "[data-compact-card]";

/** Posição e largura de cada card, indexadas pela chave estável do card. */
async function captureLayout(page: Page) {
  return page.$$eval(CARD, (nodes) =>
    nodes
      .map((node) => {
        const box = node.getBoundingClientRect();
        return `${node.getAttribute("data-compact-card")}:${Math.round(box.x)},${Math.round(
          box.y
        )},${Math.round(box.width)}`;
      })
      .sort()
      .join(" | ")
  );
}

/** Espera o layout parar de mudar (duas leituras iguais em sequência). */
async function waitForStableLayout(page: Page) {
  await expect(page.locator(CARD)).toHaveCount(6);
  let previous = "";
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const current = await captureLayout(page);
    if (current === previous && current !== "") return current;
    previous = current;
    await page.waitForTimeout(250);
  }
  throw new Error("layout não estabilizou em 5s — a fileira de indicadores está oscilando");
}

async function openDashboard(page: Page) {
  await page.goto("/onboarding");
  await page.getByRole("button", { name: "Carregar dados de demonstração" }).click();
  await page.getByRole("button", { name: "Ver dashboard" }).click();
  await page.waitForURL(/\/dashboard\/[^/]+$/);
}

test("a fileira de indicadores não se reorganiza sozinha", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDashboard(page);

  const stable = await waitForStableLayout(page);

  // Sem redimensionar, sem interagir, sem novos dados: nada pode se mover.
  await page.waitForTimeout(5_000);

  expect(await captureLayout(page)).toBe(stable);
});

test("a mesma largura produz sempre a mesma composição", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDashboard(page);
  await waitForStableLayout(page);

  // Chegar à mesma largura descendo e subindo. Um layout que dependa da própria
  // altura renderizada tem histerese: o resultado passa a depender do caminho.
  const widths = [1440, 1280, 1120, 980, 860, 1120, 1280, 1440];
  const seen = new Map<number, string>();

  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    const layout = await waitForStableLayout(page);
    const previous = seen.get(width);
    if (previous !== undefined) {
      expect(layout, `composição divergiu ao voltar para ${width}px`).toBe(previous);
    }
    seen.set(width, layout);
  }
});
