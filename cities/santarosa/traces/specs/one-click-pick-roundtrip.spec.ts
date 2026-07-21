import { test, expect } from './test-helpers';
import { captureTrace } from './trace-capture';

test('one-click-pick-roundtrip', async ({ page }) => {
  test.setTimeout(60000);

  try {
    await page.goto('./');

    const santaRosaBtn = page.getByText('Santa Rosa Now', { exact: true });
    await expect(santaRosaBtn).toBeVisible({ timeout: 15000 });
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/rest/v1/deduplicated_events')),
      santaRosaBtn.click(),
    ]);

    await expect(page.getByPlaceholder('Search events...')).toBeVisible({ timeout: 15000 });

    const settingsButton = page.getByRole('button', { name: 'Display settings' });
    await expect(settingsButton).toBeVisible({ timeout: 15000 });
    await settingsButton.click();
    await expect(page.getByText('Display Settings', { exact: true })).toBeVisible({ timeout: 15000 });

    const oneClickToggle = page.getByRole('checkbox', { name: 'One-click pick (skip editor)' });
    await expect(oneClickToggle).toBeVisible({ timeout: 15000 });

    if (!(await oneClickToggle.isChecked())) {
      await Promise.all([
        page.waitForResponse((r) =>
          r.url().includes('/rest/v1/user_settings?on_conflict=user_id,city') &&
          r.request().method() === 'POST' &&
          (r.request().postData() || '').includes('"one_click_pick":true')
        ),
        oneClickToggle.click(),
      ]);
    }

    await expect(oneClickToggle).toBeChecked({ timeout: 15000 });
    await settingsButton.click();
    await expect(page.getByText('Display Settings', { exact: true })).toHaveCount(0, { timeout: 15000 });

    const addPickBtn = page.getByRole('button', { name: /Add to my picks/ }).first();
    await expect(addPickBtn).toBeVisible({ timeout: 15000 });

    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/rest/v1/picks') && r.request().method() === 'POST'),
      addPickBtn.click(),
    ]);

    await expect(page.getByRole('button', { name: 'Add to My Picks', exact: true })).toHaveCount(0, { timeout: 5000 });
    await expect(page.getByRole('button', { name: 'Done' })).toHaveCount(0, { timeout: 5000 });

    await page.getByRole('radio', { name: 'my picks' }).click();
    await expect(page.getByText('1 events')).toBeVisible({ timeout: 15000 });

    const removeBtn = page.getByRole('button', { name: /Remove from my picks/ }).first();
    await expect(removeBtn).toBeVisible({ timeout: 15000 });
    await removeBtn.click();
    await page.waitForTimeout(1000);

    await page.getByRole('radio', { name: 'list' }).click();
    await page.waitForTimeout(1000);
  } finally {
    await captureTrace(page);
  }
});
