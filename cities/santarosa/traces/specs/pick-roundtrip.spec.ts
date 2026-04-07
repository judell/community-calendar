import { test, expect } from '@playwright/test';
import { captureTrace } from './trace-capture';

test('pick-roundtrip', async ({ page }) => {
  test.setTimeout(120000);

  try {
    // Start at root, wait for page to load, then pick Santa Rosa
    await page.goto('./');
    const santaRosaBtn = page.getByText('Santa Rosa Now', { exact: true });
    await expect(santaRosaBtn).toBeVisible({ timeout: 10000 });
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/events') && !r.url().includes('event_enrichments')),
      santaRosaBtn.click(),
    ]);

    // Wait for the event list to render
    await expect(page.getByPlaceholder('Search events...')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(1000);

    // Click "Add to my picks" on the first event (title varies, use .first())
    const addPickBtn = page.getByRole('button', { name: /Add to my picks/ }).first();
    await expect(addPickBtn).toBeVisible({ timeout: 10000 });
    await addPickBtn.click();
    await page.waitForTimeout(500);

    // Submit the PickEditor form
    const submitBtn = page.getByRole('button', { name: 'Add to My Picks' });
    await expect(submitBtn).toBeVisible({ timeout: 5000 });
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/rest/v1/picks') && r.request().method() === 'POST'),
      submitBtn.click(),
    ]);

    // Click "Done" to close the dialog
    await expect(page.getByRole('button', { name: 'Done' })).toBeVisible({ timeout: 10000 });
    await page.getByRole('button', { name: 'Done' }).click();
    await page.waitForTimeout(1000);

    // Switch to "my picks" view
    await page.getByRole('radio', { name: 'my picks' }).click();
    await page.waitForTimeout(1000);

    // Verify at least one pick is showing
    await expect(page.getByText('1 events')).toBeVisible({ timeout: 5000 });

    // Remove the pick (title varies, use .first())
    const removeBtn = page.getByRole('button', { name: /Remove from my picks/ }).first();
    await expect(removeBtn).toBeVisible({ timeout: 5000 });
    await removeBtn.click();
    await page.waitForTimeout(1000);

    // Switch back to list view
    await page.getByRole('radio', { name: 'list' }).click();
    await page.waitForTimeout(1000);

  } finally {
    await captureTrace(page);
  }
});
