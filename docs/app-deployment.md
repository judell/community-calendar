# App deployment and returning-browser checks

The app version identifies runtime asset **paths and contents**, not a Git
revision or calendar-build date. `scripts/app_version.py` includes app code,
components, engine extensions, theme/icon assets, instance configuration,
categories, cities and source priorities. Event payloads and reports are not
inputs. Missing required files stop publication rather than producing a hash
of an incomplete site.

## Publication

`.github/workflows/deploy-pages.yml` runs on each push to `main` and by manual
dispatch. It exports the checked-out revision using `git archive`, generates
`xmlui/version.txt` inside that export, then uploads and deploys that exact
artifact. It preserves the existing `.nojekyll` static site. The version file
is generated output; it need not be committed. Calendar generation continues
committing its normal metadata/config, and its PAT-authenticated push triggers
the Pages workflow. There is no hash computed before a later rebase can change
the assets it describes.

**Activation prerequisite:** this repository currently uses Pages' legacy
`main`-branch publication. After reviewing and landing the workflow, change
Settings → Pages → Build and deployment → Source to **GitHub Actions**, then
dispatch **Deploy Pages**. The workflow checks that setting and skips deployment
while branch publication is active, preventing competing publishers. Preparing
these files does not change the repository setting or deploy anything.

See GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

The old workflow generated but did not publish `version.txt`. The previous
session recorded a production 404 and `missing-version` in the browser. That
demonstrates broken version publication; it does **not** establish the cause
of the reported multiple-refresh symptom. `index.html` already timestamps its
shell requests, and the engine also has its own loading/cache behavior. Inspect
actual requests instead of assuming every asset uses `APP_VERSION`.

## Local synthetic instance

Run from the repository root:

```sh
python3 -m pytest tests/test_app_version.py -q
node scripts/test_app_deployment.cjs
node scripts/test_app_deployment.cjs --serve
```

The browser test uses the Playwright installation in
`cities/santarosa/trace-tools/node_modules/playwright`. To use another installed
copy, set `PLAYWRIGHT_MODULE` to its absolute module path. Set `PYTHON` if needed.
The test runs one browser at a time, with a fresh isolated profile retained
across deployment transitions and a browser restart. Scratch snapshots,
profiles and `results.json` are left in the printed temporary directory.

`--serve` prints a control-page URL at `http://calendar.localhost:<port>/__fixture`.
Open it in Chromium/Chrome and use **Open calendar** to inspect the real app.
The A/B buttons change the served snapshot; revisit the calendar in the same
browser without clearing storage. The control page can fail the version endpoint
or hold/release event responses. Stop the process with Ctrl-C.

The hostname is intentional: ordinary `localhost` or `127.x.x.x` activates
`-dev-<timestamp>` asset URLs in `shell.js` and defeats a production-cache test.
The runner maps `calendar.localhost` to loopback for Chromium. HTTP responses
carry content ETags and `max-age=600`. A separate profile exercises expiration
using `max-age=0`; this compresses the cache expiration boundary, not elapsed
real-world days.

The fixture copies the current runtime assets into two isolated snapshots and
uses the same version generator as deployment. A/B have different helper-code
markers so the test verifies which code **executed**, not merely which version
was recorded in storage. It serves three synthetic future events and can change
only the middle title, preserving row count and endpoint IDs. App markup,
helpers and the vendored engine are real. Supabase auth is stubbed as logged out,
and the recurrence SDK is stubbed because the fixture has no enrichments.
This test covers boot/cache/render behavior, not authentication or recurrence.

Do not add `page.route()` or `context.route()` to this test:
[Playwright routing disables HTTP caching](https://playwright.dev/docs/api/class-browsercontext#browser-context-route).
Mocking and delayed responses belong in the HTTP server. Browser/CDP listeners
and server request logs observe cache hits, conditional requests, navigations,
executed markers and errors without disabling the cache.

The automated checks first demonstrate the failure: with a missing version,
deployment B still executes cached A helper code. Publishing B's content version
then loads B code on the same profile with one automatic reload. They also cover
first visit, unchanged deployment after restart, code A→B, repeated B visits,
cached→fresh middle-row replacement, version 503/404 and recovery, and
expired-asset ETag revalidation. The event response is
released only after stale rendered text proves that the cached paint happened.
Timeouts bound failures; they do not determine readiness.

## After activation

Check that the published `xmlui/version.txt` is successful and matches a hash
generated from the corresponding artifact. Visit with an existing browser
profile, confirm updated code and current cards, then revisit to check the
reload is not repeated. Local testing cannot establish GitHub Pages/CDN
propagation behavior or explain the original multi-day symptom by itself.
