# Regression Testing

Community-calendar uses [trace-tools](https://github.com/xmlui-org/trace-tools) for regression testing. This document covers the auth and CI setup specific to this project. For the general trace-tools workflow (capturing baselines, running tests, semantic comparison), see the [trace-tools README](https://github.com/xmlui-org/trace-tools/blob/main/README.md).

## Test user

Tests run as `ci-test@community-calendar.test`, a Supabase auth user with an entry in `admin_google_users` so it has admin access (needed for features like the capture icon). This user was created via `mint-session.js` on first run.

## Session minting

Community-calendar uses Supabase Auth with Google OAuth. Since OAuth can't be driven headlessly, tests use the **pre-generated session** pattern described in the [trace-tools auth docs](https://github.com/xmlui-org/trace-tools/blob/main/README.md#path-2-pre-generated-session-mint-session).

The script at `cities/santarosa/traces/mint-session.js`:

1. Ensures the test user exists (creates via Supabase admin API if not)
2. Generates a magic link and verifies it server-side to get a session
3. Writes `.auth-state.json` in Playwright's `storageState` format, with the access token in localStorage under the `sb-<project-ref>-auth-token` key

Required environment variables:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | `https://dzpdualvwspgqghrysyz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Service role key (stored as CI secret) |
| `TEST_USER_EMAIL` | `ci-test@community-calendar.test` (stored as CI secret) |
| `BASE_URL` | `http://localhost:8080` (the app server) |

## CI workflow

The GitHub Actions workflow (`.github/workflows/regression-tests.yml`) runs on push to `main` when app or test files change:

1. Checks out the repo
2. Starts a static file server on port 8080
3. Clones trace-tools and installs Playwright
4. Runs `mint-session.js` with secrets from GitHub
5. Runs `./test.sh run-all` — executes every distilled baseline in `traces/baselines/`

### Secrets

Two GitHub Actions secrets are required:

- **`SUPABASE_SERVICE_KEY`** — the Supabase service role JWT (from Dashboard → Settings → API)
- **`TEST_USER_EMAIL`** — the test user's email address

## Baselines

Current baselines in `cities/santarosa/traces/baselines/`:

| Baseline | Journey |
|----------|---------|
| `capture-roundtrip.json` | Capture an event from an image, verify it appears |
| `pick-roundtrip.json` | Add an event to picks, verify, remove it |
| `search-roundtrip.json` | Select a city, search for events, clear search |

All baselines are in distilled format (5–30 KB). See [Distilled baselines: the gold standard](https://github.com/xmlui-org/trace-tools/blob/main/README.md#distilled-baselines-the-gold-standard) in the trace-tools README.

## Running locally

```bash
# Start the app server (from repo root)
python3 -m http.server 8080 &

# Mint a session
SUPABASE_URL=https://dzpdualvwspgqghrysyz.supabase.co \
SUPABASE_SERVICE_KEY=<your-service-key> \
TEST_USER_EMAIL=ci-test@community-calendar.test \
BASE_URL=http://localhost:8080 \
node cities/santarosa/traces/mint-session.js

# Run all baselines
cd cities/santarosa
./test.sh run-all

# Run a single baseline
./test.sh run search-roundtrip
```
