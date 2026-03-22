import { test, expect } from '@playwright/test';
import { captureTrace, traceFileUpload } from './trace-capture';

test('capture-roundtrip', async ({ page }) => {
  test.setTimeout(60000);

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

    // Click the mic icon to open AudioCaptureDialog (requires auth)
    const micBtn = page.getByRole('button', { name: 'Capture Event from Audio' });
    await expect(micBtn).toBeVisible({ timeout: 10000 });
    await micBtn.click();
    await page.waitForTimeout(500);

    // Select "Select Audio File" mode
    await page.getByRole('button', { name: 'Select Audio File' }).click();
    await page.waitForTimeout(500);

    // Upload the fixture audio file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('../traces/fixtures/stewarts-point.m4a');
    await traceFileUpload(page, ['stewarts-point.m4a']);

    // Wait for Whisper transcription + extraction — PickEditor opens with "Save Captured Event"
    await expect(page.getByText('Save Captured Event')).toBeVisible({ timeout: 45000 });
    await page.waitForTimeout(1000);

    // Submit the PickEditor form and wait for the capture-event POST to complete
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/functions/v1/capture-event') && r.request().method() === 'POST'),
      page.locator('button[type="submit"]').click(),
    ]);

    // After success, PickEditor shows "Done" button — click to close
    await expect(page.getByRole('button', { name: 'Done' })).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: 'Done' }).click();
    await page.waitForTimeout(1000);

    // Switch to "my picks" view
    await page.getByRole('radio', { name: 'my picks' }).click();
    await page.waitForTimeout(1000);

    // Verify at least one pick is showing
    const pickCount = page.locator('text=/\\d+ events/');
    await expect(pickCount).toBeVisible({ timeout: 5000 });

    // Verify exactly 1 pick, then remove it
    await expect(page.getByText('1 events')).toBeVisible({ timeout: 5000 });
    const removeBtn = page.getByRole('button', { name: 'Remove from my picks' });
    await expect(removeBtn).toBeVisible({ timeout: 5000 });
    await removeBtn.click();
    await page.waitForTimeout(1000);
    await page.waitForTimeout(1000);

  } finally {
    await captureTrace(page);
  }
});
