#!/usr/bin/env node
// Mint a Supabase session for a test user via the admin API.
// Writes .auth-state.json in Playwright storageState format.
//
// Required env vars:
//   SUPABASE_URL          - e.g. https://dzpdualvwspgqghrysyz.supabase.co
//   SUPABASE_SERVICE_KEY  - service role key (legacy JWT from Supabase dashboard)
//   TEST_USER_EMAIL       - email of the test user
//
// Creates the user on first run if it doesn't exist.

const fs = require('fs');
const path = require('path');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const TEST_EMAIL = process.env.TEST_USER_EMAIL;

if (!SUPABASE_URL || !SERVICE_KEY || !TEST_EMAIL) {
  console.error('Missing required env vars: SUPABASE_URL, SUPABASE_SERVICE_KEY, TEST_USER_EMAIL');
  process.exit(1);
}

const headers = {
  'Authorization': `Bearer ${SERVICE_KEY}`,
  'apikey': SERVICE_KEY,
  'Content-Type': 'application/json',
};

async function ensureUser() {
  // Try to create the user — if it already exists, that's fine
  const createRes = await fetch(`${SUPABASE_URL}/auth/v1/admin/users`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      email: TEST_EMAIL,
      email_confirm: true,
      user_metadata: { user_name: 'ci-test-bot' },
    }),
  });

  if (createRes.ok) {
    const user = await createRes.json();
    console.log(`Created test user: ${user.email} (${user.id})`);
    return;
  }

  // 422 means user already exists — that's expected
  if (createRes.status === 422) {
    console.log('Test user already exists');
    return;
  }

  console.error('Failed to create user:', createRes.status, await createRes.text());
  process.exit(1);
}

async function mintSession() {
  await ensureUser();

  // Generate a magic link to get a session token
  const linkRes = await fetch(`${SUPABASE_URL}/auth/v1/admin/generate_link`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      type: 'magiclink',
      email: TEST_EMAIL,
    }),
  });

  if (!linkRes.ok) {
    console.error('Failed to generate link:', linkRes.status, await linkRes.text());
    process.exit(1);
  }

  const linkData = await linkRes.json();

  // Extract the token from the action_link and verify it to get a session
  const actionLink = linkData.action_link || linkData.properties?.action_link;
  if (!actionLink) {
    console.error('No action_link in response:', JSON.stringify(linkData, null, 2));
    process.exit(1);
  }

  const url = new URL(actionLink);
  const token = url.searchParams.get('token');
  const type = url.searchParams.get('type') || 'magiclink';

  // Verify the OTP to get access + refresh tokens
  const verifyRes = await fetch(`${SUPABASE_URL}/auth/v1/verify`, {
    method: 'POST',
    headers: {
      'apikey': SERVICE_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type, token, email: TEST_EMAIL }),
  });

  if (!verifyRes.ok) {
    console.error('Failed to verify token:', verifyRes.status, await verifyRes.text());
    process.exit(1);
  }

  const session = await verifyRes.json();

  if (!session.access_token) {
    console.error('No access_token in verify response:', JSON.stringify(session, null, 2));
    process.exit(1);
  }

  // Extract the Supabase project ref from the URL for the localStorage key
  const projectRef = new URL(SUPABASE_URL).hostname.split('.')[0];
  const storageKey = `sb-${projectRef}-auth-token`;

  const storageValue = JSON.stringify({
    access_token: session.access_token,
    refresh_token: session.refresh_token,
    expires_at: Math.floor(Date.now() / 1000) + session.expires_in,
    expires_in: session.expires_in,
    token_type: 'bearer',
    user: session.user,
  });

  // Write Playwright storageState format
  const baseURL = process.env.BASE_URL || 'http://localhost:8080';
  const storageState = {
    cookies: [],
    origins: [{
      origin: baseURL,
      localStorage: [{
        name: storageKey,
        value: storageValue,
      }],
    }],
  };

  const outputPath = path.join(__dirname, '..', 'trace-tools', '.auth-state.json');
  fs.writeFileSync(outputPath, JSON.stringify(storageState, null, 2));
  console.log(`Auth state written to ${outputPath}`);
  console.log(`User: ${session.user.email} (${session.user.id})`);
}

mintSession().catch(err => {
  console.error('Unexpected error:', err);
  process.exit(1);
});
