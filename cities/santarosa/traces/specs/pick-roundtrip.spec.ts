import { test, expect } from '@playwright/test';
import { captureTrace } from './trace-capture';

test('pick-roundtrip', async ({ page }) => {
  test.setTimeout(45000);

  try {
    // Start at root and pick Santa Rosa
    await page.goto('./');
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/events')),
      page.getByText('Santa Rosa', { exact: true }).click(),
    ]);

    // Wait for the event list to render
    await expect(page.getByPlaceholder('Search events...')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(1000);

    // The bookmark icon is only visible when authenticated.
    // Pick the first event by clicking its bookmark icon.
    const firstBookmark = page.locator('[data-icon="l-bookmark"]').first();
    await expect(firstBookmark).toBeVisible({ timeout: 5000 });
    await firstBookmark.click();
    await page.waitForTimeout(1000);

    // Switch to "my picks" tab
    await page.getByText('my picks').click();
    await page.waitForTimeout(1000);

    // Verify at least one pick is showing
    const pickCount = page.locator('text=/\\d+ events/');
    await expect(pickCount).toBeVisible({ timeout: 5000 });

    // Switch back to list view
    await page.getByText('list', { exact: true }).click();
    await page.waitForTimeout(500);

    // Unpick the same event
    await firstBookmark.click();
    await page.waitForTimeout(1000);

  } finally {
    await captureTrace(page);
  }
});
