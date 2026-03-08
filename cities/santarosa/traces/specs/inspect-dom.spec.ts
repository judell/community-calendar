import { test } from '@playwright/test';

test('inspect pick flow DOM', async ({ page }) => {
  await page.goto('./');
  await Promise.all([
    page.waitForResponse(r => r.url().includes('/rest/v1/events')),
    page.getByText('Santa Rosa', { exact: true }).click(),
  ]);
  await page.waitForTimeout(3000);

  const info: string[] = [];

  const authUser = await page.evaluate(() => (window as any).authUser);
  info.push('authUser: ' + (authUser ? authUser.email : 'NULL'));

  // Radio group options
  const radios = await page.evaluate(() => {
    const els = document.querySelectorAll('[role="radio"]');
    return Array.from(els).map(el => ({
      tag: el.tagName,
      value: el.getAttribute('value'),
      ariaLabel: el.getAttribute('aria-label'),
      id: el.id,
    }));
  });
  info.push('Radios: ' + JSON.stringify(radios));

  const labels = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('label')).map(el => ({
      text: el.textContent?.trim(),
      htmlFor: el.htmlFor,
    }));
  });
  info.push('Labels: ' + JSON.stringify(labels));

  // Bookmark buttons
  const bookmarkBtns = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('[role="button"]'))
      .filter(el => (el.getAttribute('aria-label') || '').includes('picks'))
      .map(el => ({ ariaLabel: el.getAttribute('aria-label'), tag: el.tagName }));
  });
  info.push('Bookmark buttons: ' + JSON.stringify(bookmarkBtns));

  // Click bookmark if visible
  const firstBookmark = page.getByRole('button', { name: 'Add to my picks' }).first();
  const bookmarkVisible = await firstBookmark.isVisible().catch(() => false);
  info.push('Bookmark visible: ' + bookmarkVisible);

  if (bookmarkVisible) {
    await firstBookmark.click();
    await page.waitForTimeout(2000);

    // All visible buttons in dialog
    const dialogBtns = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button, [role="button"]'))
        .filter(el => (el as HTMLElement).offsetParent !== null)
        .map(el => ({
          tag: el.tagName,
          type: el.getAttribute('type'),
          role: el.getAttribute('role'),
          ariaLabel: el.getAttribute('aria-label'),
          text: el.textContent?.trim().substring(0, 60),
        }));
    });
    info.push('Dialog buttons: ' + JSON.stringify(dialogBtns));
  }

  // Fail with all the info so it shows in CI output
  throw new Error('DOM INSPECTION:\n' + info.join('\n'));
});
