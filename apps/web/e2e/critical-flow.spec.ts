import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * Fluxo crítico do MVP (Spec seção "VS-10" e critérios de aceite #13/#14/#15/#16):
 * onboarding (via seed de demonstração) → dashboard → simular decisão →
 * comparar antes/depois → detectar fragilidades → gerar e aprovar um plano
 * preventivo.
 *
 * Não passa pelo agente conversacional de propósito: evita depender de uma
 * chamada real e não-determinística à API da Anthropic num teste automatizado.
 */

async function expectNoSeriousA11yViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter((v) => v.impact === "critical" || v.impact === "serious");
  expect(serious).toEqual([]);
}

test("onboarding via demo até aprovar um plano preventivo", async ({ page }) => {
  await page.goto("/onboarding");
  await page.getByRole("button", { name: "Carregar dados de demonstração" }).click();

  await page.getByRole("button", { name: "Ver dashboard" }).click();
  await page.waitForURL(/\/dashboard\/[^/]+$/);
  await expectNoSeriousA11yViolations(page);

  await page.getByRole("link", { name: "Simulações" }).click();
  await expect(page).toHaveURL(/\/simulations$/);

  await page.getByLabel("Descrição").fill("Compra de teste E2E");
  await page.locator("#amount").fill("150");
  await page.getByRole("button", { name: "Simular decisão" }).click();

  await expect(page).toHaveURL(/\/simulations\/[^/]+$/);
  await expect(page.getByRole("heading", { name: "Cenário-base" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Cenário simulado/ })).toBeVisible();
  await expectNoSeriousA11yViolations(page);

  await page.getByRole("link", { name: "Radar de fragilidade" }).click();
  await expect(page).toHaveURL(/\/fragilities$/);
  await page.getByRole("button", { name: "Detectar fragilidades" }).click();
  await expect(page.locator("details summary").first()).toBeVisible();
  await expectNoSeriousA11yViolations(page);

  await page.getByRole("link", { name: "Planos preventivos" }).click();
  await expect(page).toHaveURL(/\/plans$/);

  await page.getByRole("button", { name: "Gerar planos" }).click();
  const firstApproveButton = page.getByRole("button", { name: "Aprovar" }).first();
  await expect(firstApproveButton).toBeVisible();
  await firstApproveButton.click();

  await expect(page.getByText("Aprovado").first()).toBeVisible();
  await expectNoSeriousA11yViolations(page);
});
