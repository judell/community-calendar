import { test, expect } from '@playwright/test';
import { captureTrace } from './trace-capture';

test('search-roundtrip', async ({ page }) => {
  test.setTimeout(30000);

  try {
    // Start at root and pick Santa Rosa
    await page.goto('./');
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/events')),
      page.getByText('Santa Rosa', { exact: true }).click(),
    ]);

    // Wait for the event list to render
    await expect(page.getByPlaceholder('Search events...')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(500);

    // Type a search term
    await test.step('search for jazz', async () => {
      await page.getByPlaceholder('Search events...').fill('jazz');
      await page.waitForTimeout(500);
    });

    // Clear the search — the close Icon now has role="button" aria-label="close"
    await test.step('clear search', async () => {
      await page.getByRole('button', { name: 'close', exact: true }).click();
      await page.waitForTimeout(500);
    });
  } finally {
    await captureTrace(page);
  }
});
