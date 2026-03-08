import { test } from '@playwright/test';

test('inspect pick flow DOM', async ({ page }) => {
  await page.goto('./');
  await Promise.all([
    page.waitForResponse(r => r.url().includes('/rest/v1/events')),
    page.getByText('Santa Rosa', { exact: true }).click(),
  ]);
  await page.waitForTimeout(3000);

  const authUser = await page.evaluate(() => (window as any).authUser);
  console.log('=== authUser:', authUser ? authUser.email : 'NULL');

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
  console.log('=== Radios:', JSON.stringify(radios, null, 2));

  const labels = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('label')).map(el => ({
      text: el.textContent?.trim(),
      htmlFor: el.htmlFor,
    }));
  });
  console.log('=== Labels:', JSON.stringify(labels, null, 2));

  // Bookmark buttons
  const bookmarkBtns = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('[role="button"]'))
      .filter(el => (el.getAttribute('aria-label') || '').includes('picks'))
      .map(el => ({ ariaLabel: el.getAttribute('aria-label'), tag: el.tagName }));
  });
  console.log('=== Bookmark buttons:', JSON.stringify(bookmarkBtns, null, 2));

  // Click bookmark if visible
  const firstBookmark = page.getByRole('button', { name: 'Add to my picks' }).first();
  if (await firstBookmark.isVisible().catch(() => false)) {
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
    console.log('=== Dialog buttons:', JSON.stringify(dialogBtns, null, 2));
  } else {
    console.log('=== Bookmark NOT visible');
  }
});
