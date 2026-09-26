// @ts-check
const { test, expect } = require('@playwright/test');

// The /optimize endpoint runs Selenium + network scraping — allow up to 90s.
const OPTIMIZE_TIMEOUT = 90_000;

test('fluxo completo: home → otimizar (BIO+GEO) → resultados', async ({ page }) => {
  let capturedPayload = null;

  await page.route('**/optimize', async (route) => {
    capturedPayload = JSON.parse(route.request().postData() || '{}');
    await route.continue();
  });

  await page.goto('/');
  await expect(page.getByRole('heading', { name: /otimizador de acertos/i })).toBeVisible();

  const filters = page.locator('.filters select');
  await expect(filters.nth(0)).toBeEnabled();
  await filters.nth(0).selectOption('2025');
  await expect(filters.nth(1)).toBeEnabled({ timeout: OPTIMIZE_TIMEOUT });
  await filters.nth(1).selectOption({ label: 'Ciência da Computação - Bacharelado' });
  await filters.nth(2).selectOption('Inglês');
  await filters.nth(3).selectOption('LI_EP');

  // Select two subjects to minimize
  await page.locator('#BIO').check();
  await page.locator('#GEO').check();

  await page.getByRole('button', { name: /otimizar/i }).click();
  await page.waitForURL('**/resultados', { timeout: OPTIMIZE_TIMEOUT });

  // --- Payload assertions ---
  expect(capturedPayload).toMatchObject({
    course: 'Ciência da Computação - Bacharelado',
    foreign_language: 'Inglês',
    reference_year: '2025',
    entry_method: 'LI_EP',
  });
  expect(Object.keys(capturedPayload.constraints)).toHaveLength(9);
  expect(capturedPayload.min_subjects).toEqual(expect.arrayContaining(['BIO', 'GEO']));
  expect(capturedPayload.min_subjects).toHaveLength(2);

  // --- Results page assertions ---
  await expect(page.getByRole('heading', { name: /otimizador de acertos/i })).toBeVisible();
  const rows = page.locator('table.results-table tbody tr');
  await expect(rows).toHaveCount(8);
  await expect(rows.first()).toContainText('Biologia');
  // Bar chart only renders when historicalData from real API is non-empty
  await expect(page.locator('.historical-data-graph')).toBeVisible();
});
