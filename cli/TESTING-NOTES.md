# cc-cli Testing Notes

Running commentary from testing sessions.

## gh auth: multiple login methods (2026-04-02)

**Problem:** Josh ran `cc-cli init` and it failed to recognize he was logged into `gh`, even though `gh auth status` showed him as authenticated.

**Cause:** `gh auth status` showed two login methods — one unintended. When multiple auth methods exist, `gh` may use the wrong one for API calls. Common scenarios:

- `GH_TOKEN` or `GITHUB_TOKEN` env var is set (takes precedence over interactive login)
- Two entries in `~/.config/gh/hosts.yml`

**Diagnosis:**

```bash
gh auth status          # shows all auth methods and which is active
echo $GH_TOKEN          # check for env var override
echo $GITHUB_TOKEN
```

**Fixes:**

```bash
# If an env var is overriding:
unset GH_TOKEN
unset GITHUB_TOKEN

# If two entries in hosts.yml — switch active account:
gh auth switch

# Or remove the unwanted one:
gh auth logout --hostname github.com   # prompts which account
```

**Note for cc-cli:** The `CheckGHInstalled()` function (`internal/github/github.go:25`) just runs `gh auth status` and checks the exit code. It doesn't detect *which* account is active. If users hit this, they need to resolve it at the `gh` level before running `cc-cli init`.

## Run cc-cli init from a bare directory (2026-04-02)

**Problem:** Josh first tried from a worktree, then from `main` of an existing clone — both caused trouble.

**Why existing repos are problematic:** `findRepoRoot()` walks up looking for `config.json` + `supabase/ddl/`. If it finds them (i.e., you're in any community-calendar clone), it skips the fork/clone step and operates on whatever repo you're in — which may be the upstream, someone else's fork, or your own dev copy. `GetCurrentRepo()` then parses that repo's origin, and all the `gh secret set` / `gh variable set` / `gh repo set-default` calls target the wrong place.

Worktrees are even worse — they share `.git` state with the parent, so remotes and `gh` default-repo resolution point to the parent's origin.

**Recommendation:** Always run `cc-cli init` from a bare directory (e.g., `mkdir ~/my-calendar && cd ~/my-calendar`). Let the CLI do the fork and clone itself — that's the only way to guarantee the origin and `gh` context are correct.

## Stale file paths after repo restructure (2026-04-02)

**Problem:** `cc-cli init` failed with "could not find community-calendar repo root" even after a successful fork/clone.

**Cause:** `findRepoRoot()` looked for `config.json` at the repo root, but it moved to `xmlui/config.json` during a restructure. Similarly, `UpdateHTMLFiles` referenced files at old locations.

**Fixes applied:**
- `findRepoRoot()`: now checks for `cities/` + `supabase/ddl/` (stable root markers)
- `UpdateConfigJSON()`: now targets `xmlui/config.json`
- `UpdateHTMLFiles()`: updated to `xmlui/index.html`, `xmlui/test.html`, `report.html` (removed nonexistent `embed.html`)

## UX improvements to init prompts (2026-04-02)

Issues found during Josh's walkthrough, all fixed in `init.go`:

- **Supabase step:** No mention of creating an account first. Added "create one at https://supabase.com" before the token link.
- **Anthropic step:** User asked "individual or org?" at console. Added hint: "individual account is fine."
- **OpenAI step:** Unclear why it's optional. Added: "for audio event capture via Whisper, skip if not needed." Fixed URL to link directly to https://platform.openai.com/api-keys.
- **GitHub OAuth:** Instructions jumped to form fields without saying to create an app. Restructured as numbered steps: go to page → click New OAuth App → fill form → register → copy Client ID → generate secret.
- **Google OAuth:** "Left sidebar" doesn't exist — Google Cloud uses a hamburger menu. Updated path. Added "Skip Authorized JavaScript origins — scroll down to Authorized redirect URIs." Added missing "Click Create" step. Prefixed prompts with "Google" for clarity. Softened "check the policy box" to "if shown" (UI may have changed).
- **Enable workflows:** Conditional now — "If workflows aren't already enabled" since active forks already have them.

## Anthropic API 400 on classify (2026-04-02)

**Problem:** First build succeeded through feed download but failed on `classify_events_json.py` with `HTTP Error 400: Bad Request`.

**Cause:** Brand new Anthropic account — likely no credits loaded. The classify script uses `claude-haiku-4-5-20251001`.

**Diagnosis:** The Python script doesn't print the response body on error. Test the key directly:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

**Fix:** Add payment method / credits at https://console.anthropic.com.

## OpenAI Whisper 429 on audio capture (2026-04-02)

**Problem:** Audio event capture failed with `Whisper API error: 429` (visible in XMLUI Inspector trace).

**Cause:** New OpenAI account on free tier — rate limits too low for Whisper API.

**Fix:** Add payment method / credits at https://platform.openai.com/settings/organization/billing/overview. Audio capture is optional — the rest of the app works without it.
