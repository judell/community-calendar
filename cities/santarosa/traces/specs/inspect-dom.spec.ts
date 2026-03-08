import { test } from '@playwright/test';

test('inspect after submit', async ({ page }) => {
  await page.goto('./');
  await Promise.all([
    page.waitForResponse(r => r.url().includes('/rest/v1/events')),
    page.getByText('Santa Rosa', { exact: true }).click(),
  ]);
  await page.waitForTimeout(3000);

  const info: string[] = [];

  const authInfo = await page.evaluate(() => {
    const u = (window as any).authUser;
    const s = (window as any).authSession;
    return {
      email: u?.email,
      id: u?.id,
      hasAccessToken: !!s?.access_token,
      tokenPrefix: s?.access_token?.substring(0, 20),
    };
  });
  info.push('Auth: ' + JSON.stringify(authInfo));

  // Click bookmark
  const firstBookmark = page.getByRole('button', { name: 'Add to my picks' }).first();
  await firstBookmark.click();
  await page.waitForTimeout(2000);

  // Click submit
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(5000);

  // What's visible now?
  const visibleText = await page.evaluate(() => {
    const dialog = document.querySelector('[role="dialog"]');
    if (!dialog) return 'NO DIALOG FOUND';
    return (dialog as HTMLElement).innerText.substring(0, 500);
  });
  info.push('Dialog text after submit: ' + visibleText);

  // Check for error text
  const errorText = await page.evaluate(() => {
    const els = document.querySelectorAll('[class*="danger"], [style*="color: red"], [style*="color: rgb(2"]');
    return Array.from(els).map(el => (el as HTMLElement).innerText).filter(t => t).join(' | ');
  });
  info.push('Error elements: ' + (errorText || 'NONE'));

  // All visible buttons
  const buttons = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button'))
      .filter(el => el.offsetParent !== null)
      .map(el => el.textContent?.trim().substring(0, 40))
      .filter(t => t);
  });
  info.push('Visible buttons: ' + JSON.stringify(buttons));

  throw new Error('POST-SUBMIT INSPECTION:\n' + info.join('\n'));
});
