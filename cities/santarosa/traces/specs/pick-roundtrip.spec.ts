import { test, expect } from '@playwright/test';
import { captureTrace } from './trace-capture';

test('pick-roundtrip', async ({ page }) => {
  test.setTimeout(45000);

  try {
    // Start at root, wait for page to load, then pick Santa Rosa
    await page.goto('./');
    const santaRosaBtn = page.getByText('Santa Rosa', { exact: true });
    await expect(santaRosaBtn).toBeVisible({ timeout: 10000 });
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/events') && !r.url().includes('event_enrichments')),
      santaRosaBtn.click(),
    ]);

    // Wait for the event list to render
    await expect(page.getByPlaceholder('Search events...')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(1000);

    // Click the bookmark icon to open the PickEditor dialog
    const firstBookmark = page.getByRole('button', { name: 'Add to my picks' }).first();
    await expect(firstBookmark).toBeVisible({ timeout: 5000 });
    await firstBookmark.click();
    await page.waitForTimeout(1000);

    // Submit the PickEditor dialog and wait for the POST to complete
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/picks') && r.request().method() === 'POST'),
      page.locator('button[type="submit"]').click(),
    ]);

    // After success, PickEditor shows "Done" button — click to close
    await expect(page.getByRole('button', { name: 'Done' })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Done' }).click();
    await page.waitForTimeout(1000);

    // Switch to "my picks" view via the radio button
    await page.getByRole('radio', { name: 'my picks' }).click();
    await page.waitForTimeout(1000);

    // Verify at least one pick is showing
    const pickCount = page.locator('text=/\\d+ events/');
    await expect(pickCount).toBeVisible({ timeout: 5000 });

    // Switch back to list view
    await page.getByRole('radio', { name: 'list' }).click();
    await page.waitForTimeout(500);

    // Unpick the same event (unpicking is one-click, no dialog)
    const removeBookmark = page.getByRole('button', { name: 'Remove from my picks' }).first();
    await removeBookmark.click();
    await page.waitForTimeout(1000);

  } finally {
    await captureTrace(page);
  }
});
