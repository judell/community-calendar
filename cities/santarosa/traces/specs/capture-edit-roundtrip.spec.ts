import { test, expect } from '@playwright/test';
import { captureTrace, traceFileUpload } from './trace-capture';

test('capture-edit-roundtrip', async ({ page }) => {
  test.setTimeout(60000);

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

    // --- Edit the form fields before submitting (regression test for #edit-bug) ---

    // Edit the title
    const titleInput = page.getByLabel('Title');
    await titleInput.click();
    await titleInput.fill('Edited: Test Capture Event');

    // Edit the start time — this is the key regression: TimeInput.isoValue()
    // returns a different format after editing, which caused double-:00 in start_time
    const hourInput = page.getByLabel('Start time hour');
    await hourInput.click();
    await hourInput.fill('7');
    await hourInput.press('Tab');
    const minuteInput = page.getByLabel('Start time minute');
    await minuteInput.fill('30');
    await minuteInput.press('Tab');

    // Edit the description
    const descriptionInput = page.getByLabel('Description');
    await descriptionInput.click();
    await descriptionInput.fill('Edited description for regression test');

    await page.waitForTimeout(500);

    // Submit the PickEditor form and wait for the capture-event commit POST to complete
    // Use postData check to distinguish the commit POST from the earlier extract POST
    await Promise.all([
      page.waitForResponse(r =>
        r.url().includes('/functions/v1/capture-event') &&
        r.request().method() === 'POST' &&
        (r.request().postData() || '').includes('"mode":"commit"')
      ),
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
