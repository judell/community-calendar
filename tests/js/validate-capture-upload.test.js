// tests/js/validate-capture-upload.test.js — poster capture upload seam.
//
// WHY: capture-event now requires a signed-in user's token. The dialog must
// fail with a sign-in prompt, and must not upload, when the session is gone.
'use strict';
import { describe, it, expect, afterEach } from 'vitest';
import { loadShipped } from './load-shipped.js';

loadShipped();

const realFetch = global.fetch;
const realResize = window.resizeImageFile;

afterEach(() => {
  global.fetch = realFetch;
  window.resizeImageFile = realResize;
  window.authSession = null;
});

describe('resizeAndUpload auth', () => {
  it('returns a sign-in error without a session', async () => {
    window.authSession = null;
    await expect(window.resizeAndUpload({}, 'https://example.com', 'key')).resolves.toEqual({
      error: 'Please sign in again to capture events',
    });
  });

  it('sends the session token', async () => {
    window.authSession = { access_token: 'token' };
    window.resizeImageFile = () =>
      Promise.resolve(new File(['x'], 'x.jpg', { type: 'image/jpeg' }));
    let headers;
    global.fetch = (_url, options) => {
      headers = options.headers;
      return Promise.resolve(new Response('{}', { status: 200 }));
    };
    await window.resizeAndUpload({}, 'https://example.com', 'key');
    expect(headers.Authorization).toBe('Bearer token');
  });

  it('maps a 401 response to the sign-in error', async () => {
    window.authSession = { access_token: 'expired' };
    window.resizeImageFile = () =>
      Promise.resolve(new File(['x'], 'x.jpg', { type: 'image/jpeg' }));
    global.fetch = () =>
      Promise.resolve(new Response('{"error":"Invalid authorization"}', { status: 401 }));
    await expect(window.resizeAndUpload({}, 'https://example.com', 'key')).resolves.toEqual({
      error: 'Please sign in again to capture events',
    });
  });
});
