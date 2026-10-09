#!/usr/bin/env node
// Real HTTP caching + real app/engine, with isolated deployment snapshots.
// No Playwright routing: it disables the HTTP cache this test must exercise.
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'cc-deployment-'));
const python = process.env.PYTHON || 'python3';
const prefix = '/community-calendar/';
const state = { deployment: 'A', events: 'old', version: 'valid', holdEvents: false, maxAge: 600 };
const requests = [];
const pending = new Set();
const versions = {};
let origin;

// Only auth and recurrence SDK loading is replaced. This fixture is logged out
// and has no recurring enrichments; app markup, helpers and engine are real.
const sdk = `window.supabase = { createClient: () => ({auth: {
  onAuthStateChange: () => ({data: {subscription: {unsubscribe() {}}}}),
  getSession: () => Promise.resolve({data: {session: null}, error: null})
}})}; window.rrule = {};`;

function send(req, res, status, body, type = 'application/json', caching = 'no-store') {
  body = Buffer.isBuffer(body) ? body : Buffer.from(body);
  const etag = '"' + crypto.createHash('sha256').update(body).digest('hex') + '"';
  const unchanged = status === 200 && req.headers['if-none-match'] === etag;
  requests.push({ path: req.url, status: unchanged ? 304 : status,
    deployment: state.deployment, ifNoneMatch: req.headers['if-none-match'] || null });
  res.writeHead(unchanged ? 304 : status, {
    'Content-Type': type, 'Cache-Control': caching, ETag: etag,
  });
  res.end(unchanged ? undefined : body);
}

function events() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(12, 0, 0, 0);
  return [0, 1, 2].map(i => ({
    id: i + 1, title: i === 1 ? `Fixture ${state.events} middle` : `Fixture endpoint ${i}`,
    start_time: new Date(+tomorrow + i * 3600000).toISOString(),
    end_time: new Date(+tomorrow + (i + 1) * 3600000).toISOString(),
    source: 'Synthetic calendar', city: 'santarosa', location: 'Test venue',
    description: '', url: '', category: 'Music', all_day: false,
    cluster_id: null, image_url: null, merged_ids: [], source_urls: [],
  }));
}

function releaseEvents() {
  state.holdEvents = false;
  for (const reply of pending) reply();
  pending.clear();
}

const controlPage = `<!doctype html><title>Calendar deployment fixture</title>
<h1>Calendar deployment fixture</h1>
<p>Open the app in another tab. Change the deployment here, then revisit the app
without clearing browser storage. The app uses real HTTP caching and synthetic events.</p>
<p><a target="_blank" href="${prefix}xmlui/index.html?city=santarosa">Open calendar</a></p>
<button onclick="set({deployment:'A',version:'valid',events:'old'})">Deployment A</button>
<button onclick="set({deployment:'B',version:'valid',events:'new'})">Deployment B</button>
<button onclick="set({version:'missing'})">Version 404</button>
<button onclick="set({version:'error'})">Version 503</button>
<button onclick="set({version:'valid'})">Restore version</button>
<button onclick="set({holdEvents:true,events:'new'})">Hold fresh events</button>
<button onclick="fetch('/__fixture/release',{method:'POST'}).then(show)">Release events</button>
<pre id="state"></pre><script>
function show(){fetch('/__fixture/state').then(r=>r.json()).then(s=>{
document.getElementById('state').textContent=JSON.stringify(s,null,2)})}
function set(s){fetch('/__fixture/control',{method:'POST',body:JSON.stringify(s)}).then(show)}
show();</script>`;

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, origin);
  if (url.pathname === '/__fixture') return send(req, res, 200, controlPage, 'text/html');
  if (url.pathname === '/__fixture/state') {
    return send(req, res, 200, JSON.stringify({ ...state, versions, work }));
  }
  if (url.pathname === '/__fixture/release' && req.method === 'POST') {
    releaseEvents();
    return send(req, res, 200, '{}');
  }
  if (url.pathname === '/__fixture/control' && req.method === 'POST') {
    let body = '';
    for await (const chunk of req) body += chunk;
    try {
      const input = JSON.parse(body);
      for (const key of ['deployment', 'events', 'version']) {
        const allowed = { deployment: ['A', 'B'], events: ['old', 'new'], version: ['valid', 'missing', 'error'] };
        if (key in input && !allowed[key].includes(input[key])) throw new Error(key);
        if (key in input) state[key] = input[key];
      }
      if ('holdEvents' in input) {
        if (input.holdEvents) state.holdEvents = true;
        else releaseEvents();
      }
      return send(req, res, 200, '{}');
    } catch { return send(req, res, 400, '{}'); }
  }
  if (url.pathname === '/__fixture/sdk.js') return send(req, res, 200, sdk, 'text/javascript');
  if (url.pathname === '/rest/v1/deduplicated_events') {
    const reply = () => { if (!res.destroyed) send(req, res, 200, JSON.stringify(events())); };
    if (state.holdEvents) {
      pending.add(reply);
      res.on('close', () => pending.delete(reply));
    } else reply();
    return;
  }
  if (url.pathname.startsWith('/rest/v1/')) return send(req, res, 200, '[]');
  if (!url.pathname.startsWith(prefix)) return send(req, res, 404, '{}');
  const relative = decodeURIComponent(url.pathname.slice(prefix.length));
  const dir = path.join(work, state.deployment);
  const filename = path.resolve(dir, relative);
  if (!filename.startsWith(dir + path.sep)) return send(req, res, 403, '{}');
  if (relative === 'xmlui/version.txt' && state.version !== 'valid') {
    return send(req, res, state.version === 'missing' ? 404 : 503, 'version unavailable', 'text/plain');
  }
  try {
    const type = { '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
      '.html': 'text/html', '.svg': 'image/svg+xml' }[path.extname(filename)] || 'text/plain';
    send(req, res, 200, fs.readFileSync(filename), type, `max-age=${state.maxAge}`);
  } catch { send(req, res, 404, '{}'); }
});

function prepareSnapshots() {
  const inputs = JSON.parse(execFileSync(python,
    [path.join(root, 'scripts/app_version.py'), '--root', root, '--list'], { encoding: 'utf8' }));
  for (const deployment of ['A', 'B']) {
    const dir = path.join(work, deployment);
    for (const name of inputs) {
      const target = path.join(dir, name);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.copyFileSync(path.join(root, name), target);
    }
    const configPath = path.join(dir, 'xmlui/config.json');
    const config = JSON.parse(fs.readFileSync(configPath));
    config.appGlobals.supabaseUrl = origin;
    config.appGlobals.supabasePublishableKey = 'synthetic-key';
    fs.writeFileSync(configPath, JSON.stringify(config));
    const indexPath = path.join(dir, 'xmlui/index.html');
    fs.writeFileSync(indexPath, fs.readFileSync(indexPath, 'utf8')
      .replace(/https:\/\/cdn\.jsdelivr\.net\/npm\/[^" ]+/g, '/__fixture/sdk.js'));
    fs.appendFileSync(path.join(dir, 'xmlui/helpers.js'),
      `\nwindow.__fixtureDeployment = ${JSON.stringify(deployment)};\n`);
    versions[deployment] = execFileSync(python,
      [path.join(root, 'scripts/app_version.py'), '--root', dir], { encoding: 'utf8' }).trim();
  }
  assert.notEqual(versions.A, versions.B);
}

async function runTests() {
  const modulePath = process.env.PLAYWRIGHT_MODULE ||
    path.join(root, 'cities/santarosa/trace-tools/node_modules/playwright');
  const { chromium } = require(modulePath);
  const profile = path.join(work, 'browser-profile');
  const results = [];
  let context, page, network, documents, errors;

  async function open(profilePath = profile) {
    context = await chromium.launchPersistentContext(profilePath, {
      headless: true,
      args: ['--host-resolver-rules=MAP calendar.localhost 127.0.0.1'],
    });
    page = context.pages()[0];
    page.setDefaultTimeout(15000);
    network = [];
    documents = [];
    errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      if (request.isNavigationRequest() && request.frame() === page.mainFrame()) documents.push(request.url());
    });
    // Observe the cache; do not change cache policy or intercept requests.
    const cdp = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    cdp.on('Network.responseReceived', ({ response }) => network.push({
      url: response.url, cached: !!response.fromDiskCache, status: response.status,
    }));
  }

  async function visit(label, marker, title, navigations = 1) {
    await page.goto('about:blank');
    const base = documents.length;
    try { await page.goto(origin + prefix + 'xmlui/index.html?city=santarosa'); }
    catch (error) { if (!/interrupted|ERR_ABORTED/.test(error.message)) throw error; }
    await page.getByText(title, { exact: true }).waitFor({ timeout: 30000 });
    await page.waitForFunction(() => window.__fixtureDeployment && window.__ccEmitSig);
    assert.equal(await page.evaluate(() => window.__fixtureDeployment), marker, label);
    assert.equal(documents.length - base, navigations, `${label}: document requests`);
    assert.equal(await page.evaluate(() => window.APP_VERSION.includes('-dev-')), false);
    assert.deepEqual(errors, [], `${label}: browser errors`);
    const actualVersion = await page.evaluate(() => window.APP_VERSION);
    results.push({ label, marker, actualVersion, navigations: documents.length - base });
    console.log('PASS', label, JSON.stringify(results.at(-1)));
  }

  try {
    // Negative control: demonstrate the stale-code mechanism with a missing
    // version, then repair it on the same origin and persistent profile.
    const legacyProfile = path.join(work, 'legacy-profile');
    state.version = 'missing';
    await open(legacyProfile);
    await visit('legacy A with missing version', 'A', 'Fixture old middle');
    await context.close();
    state.deployment = 'B';
    await open(legacyProfile);
    await visit('unversioned B still executes cached A', 'A', 'Fixture old middle');
    state.version = 'valid';
    await visit('publishing B version replaces cached A', 'B', 'Fixture old middle', 2);
    await context.close();
    state.deployment = 'A';
    await open();
    await visit('first visit', 'A', 'Fixture old middle');
    assert.equal(await page.evaluate(() => window.APP_VERSION), versions.A);
    await context.close();
    await open();
    const cacheStart = network.length;
    await visit('unchanged deployment after browser restart', 'A', 'Fixture old middle');
    assert(network.slice(cacheStart).some(r => r.url.includes('/helpers.js?v=') && r.cached),
      'unchanged deployment must actually reuse the HTTP cache');

    state.deployment = 'B';
    await visit('code deployment A to B', 'B', 'Fixture old middle', 2);
    assert.equal(await page.evaluate(() => window.APP_VERSION), versions.B);
    await visit('B stays stable', 'B', 'Fixture old middle');

    // Change only an interior event: count and first/last IDs are identical.
    // Hold the API at the server until stale DOM text proves cached paint.
    state.events = 'new';
    state.holdEvents = true;
    const base = documents.length;
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByText('Fixture old middle', { exact: true }).waitFor();
    releaseEvents();
    await page.getByText('Fixture new middle', { exact: true }).waitFor();
    await page.waitForFunction(() => window.__fixtureDeployment && window.__ccEmitSig);
    assert.equal(await page.getByText('Fixture old middle', { exact: true }).count(), 0);
    assert.equal(documents.length - base, 1);
    assert.equal(await page.evaluate(() => window.APP_VERSION), versions.B);
    results.push({ label: 'data-only middle-row replacement', version: versions.B });
    console.log('PASS data-only middle-row replacement');

    state.version = 'error';
    await visit('version 503 after valid deployment', 'B', 'Fixture new middle', 2);
    assert.equal(await page.evaluate(() => window.APP_VERSION), 'missing-version');
    await visit('repeated version failure is bounded', 'B', 'Fixture new middle');
    state.version = 'missing';
    await visit('version 404 fallback', 'B', 'Fixture new middle');
    state.version = 'valid';
    await visit('missing version to published version', 'B', 'Fixture new middle', 2);
    await visit('restored version stays stable', 'B', 'Fixture new middle');

    // A separate profile primes expired responses. max-age=0 compresses the
    // expiration boundary; it does not pretend to reproduce a multi-day visit.
    await context.close();
    state.maxAge = 0;
    const expiredProfile = path.join(work, 'expired-profile');
    context = await chromium.launchPersistentContext(expiredProfile, { headless: true });
    page = await context.newPage();
    const appUrl = origin + prefix + 'xmlui/index.html?city=santarosa';
    await page.goto(appUrl);
    await page.getByText('Fixture new middle', { exact: true }).waitFor();
    await page.waitForFunction(() => window.__fixtureDeployment && window.__ccEmitSig);
    const requestStart = requests.length;
    await page.goto('about:blank');
    await page.goto(appUrl);
    await page.getByText('Fixture new middle', { exact: true }).waitFor();
    await page.waitForFunction(() => window.__fixtureDeployment && window.__ccEmitSig);
    assert(requests.slice(requestStart).some(r => r.path.includes('/helpers.js?v=') && r.status === 304),
      'expired helper must revalidate with its ETag');
    results.push({ label: 'expired asset ETag revalidation' });
    console.log('PASS expired asset ETag revalidation');
  } finally {
    fs.writeFileSync(path.join(work, 'results.json'), JSON.stringify({ results, requests, network, errors }, null, 2));
    console.log('Evidence:', path.join(work, 'results.json'));
    releaseEvents();
    if (context) await context.close();
  }
}

server.listen(Number(process.env.PORT || 0), '127.0.0.1', async () => {
  origin = `http://calendar.localhost:${server.address().port}`;
  try {
    prepareSnapshots();
    console.log('Synthetic instance:', origin + '/__fixture');
    if (process.argv.includes('--serve')) return;
    await runTests();
  } catch (error) {
    console.error(error);
    process.exitCode = 1;
  } finally {
    if (!process.argv.includes('--serve') || process.exitCode) server.close();
  }
});
