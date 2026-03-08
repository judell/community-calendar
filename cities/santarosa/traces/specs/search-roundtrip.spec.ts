import { test, expect } from '@playwright/test';
import { captureTrace } from './trace-capture';

test('search-roundtrip', async ({ page }) => {
  test.setTimeout(30000);

  try {
    // Start at root, pick Santa Rosa
    await page.goto('./');
    const santaRosaBtn = page.getByText('Santa Rosa', { exact: true });
    await expect(santaRosaBtn).toBeVisible({ timeout: 10000 });
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/events') && !r.url().includes('event_enrichments')),
      santaRosaBtn.click(),
    ]);

    // Wait for the search box to appear
    const searchBox = page.getByPlaceholder('Search events...');
    await expect(searchBox).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(1000);

    // Type a search term
    await searchBox.fill('jazz');
    await page.waitForTimeout(1000);

    // Clear the search
    await searchBox.fill('');
    await page.waitForTimeout(500);

  } finally {
    await captureTrace(page);
  }
});
