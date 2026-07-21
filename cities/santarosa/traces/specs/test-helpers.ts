import { test as base, expect, type Page } from '@playwright/test';

type PageDiagnostics = {
  consoleErrors: string[];
  pageErrors: string[];
  responseErrors: string[];
};

const diagnosticsByPage = new WeakMap<Page, PageDiagnostics>();

function isIgnorableConsoleError(message: string): boolean {
  return /Failed to load resource: the server responded with a status of 404\b/i.test(message);
}

function getDiagnostics(page: Page): PageDiagnostics {
  let diagnostics = diagnosticsByPage.get(page);
  if (!diagnostics) {
    diagnostics = {
      consoleErrors: [],
      pageErrors: [],
      responseErrors: [],
    };
    diagnosticsByPage.set(page, diagnostics);
  }
  return diagnostics;
}

async function collectXmluiRuntimeErrors(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const logs = (window as any)._xsLogs || [];
    return logs
      .filter((entry: any) => String(entry.kind || '').startsWith('error'))
      .map((entry: any) => entry.error || entry.text || JSON.stringify(entry));
  });
}

async function collectVisibleErrorMarkers(page: Page): Promise<string[]> {
  const markers: string[] = [];

  if (await page.getByText(/error while processing xmlui markup/i).first().isVisible().catch(() => false)) {
    markers.push('Visible XMLUI markup error overlay');
  }

  if (await page.getByText(/invalid time input/i).first().isVisible().catch(() => false)) {
    markers.push('Visible invalid time input error');
  }

  return markers;
}

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const diagnostics = getDiagnostics(page);

    // config.json ships xsVerbose:false (the engine's trace serialization is
    // too slow for production with ~5k-row state). Trace capture still needs
    // the engine log, so re-enable it per session via the engine's
    // localStorage override before any page script runs.
    await page.addInitScript(() => {
      try {
        localStorage.setItem('xmlui:xsVerbose', 'true');
      } catch {}
    });

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const message = msg.text();
        if (!isIgnorableConsoleError(message)) {
          diagnostics.consoleErrors.push(message);
        }
      }
    });

    page.on('pageerror', (error) => {
      diagnostics.pageErrors.push(error.stack || error.message || String(error));
    });

    page.on('response', (response) => {
      if (response.status() >= 500) {
        diagnostics.responseErrors.push(
          `${response.status()} ${response.request().method()} ${response.url()}`,
        );
      }
    });

    await use(page);

    if (testInfo.status !== testInfo.expectedStatus) {
      return;
    }

    const xmluiRuntimeErrors = await collectXmluiRuntimeErrors(page).catch(() => []);
    const visibleErrorMarkers = await collectVisibleErrorMarkers(page).catch(() => []);
    const failures = [
      ...diagnostics.pageErrors.map((message) => `pageerror: ${message}`),
      ...diagnostics.consoleErrors.map((message) => `console error: ${message}`),
      ...diagnostics.responseErrors.map((message) => `response error: ${message}`),
      ...xmluiRuntimeErrors.map((message) => `XMLUI runtime error: ${message}`),
      ...visibleErrorMarkers,
    ];

    if (failures.length > 0) {
      throw new Error(`Browser/runtime errors detected:\n- ${failures.join('\n- ')}`);
    }
  },
});

export { expect };
