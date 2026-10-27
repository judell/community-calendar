# Dependency Management

Python dependencies live in `pyproject.toml`. `uv.lock` is the resolved
lockfile and the source of truth for what actually installs
([ADR 0005](adr/0005-uv-for-python-dependency-management.md)). Most runtime
dependencies use exact `==` pins; a few use deliberate ranges (the `icalendar`
major ceiling is one) that `uv.lock` resolves. Do not treat those ranges as
pins for Dependabot to collapse back to `==`. Dev tools live in the
`[dependency-groups].dev` group. Run `uv sync` to install the locked
environment.

Two automations keep the manifest from going stale — the failure mode that let
2022-era pins sit for years ([ADR 0015](adr/0015-modernize-stale-runtime-dependencies.md)).

## What is automatic

| Automation | Trigger | What it does |
| --- | --- | --- |
| Dependabot (`uv` ecosystem) | Weekly, Monday | Opens one grouped PR for minor/patch bumps across runtime deps and dev tools. Major bumps open as individual PRs. |
| Dependency Audit workflow (`.github/workflows/dependency-audit.yml`) | PRs touching `pyproject.toml` or `uv.lock`, plus weekly (Monday 06:00 UTC) | Runs `uv audit --locked`, checking the locked set against the OSV vulnerability database. The step passes `--preview-features audit-command` to silence the experimental-command warning; the flag does not affect pass/fail. |

Dependabot edits `pyproject.toml` and `uv.lock` together, so a bump is a
coherent lockfile change rather than a manifest edit that a later `uv sync`
re-resolves.

## What needs a human

The repository maintainers own both items below; nothing merges or clears an
alert on its own.

- **Merge Dependabot PRs.** There is no auto-merge. The normal PR gates
  (`make lint`, `make test-python`, feeds validation, and the rest of
  `validate-pr.yml`) are the review. Merge when green; if red, the bump broke
  something and needs a fix or a scoped `ignore`.
- **Act on audit alerts.** A failed run names the vulnerable package and the
  fixed version. Take the fix (usually a Dependabot security PR). If no fix
  exists yet, add a time-boxed `--ignore <ID>` to the audit step with a comment
  linking the advisory and the issue tracking the upgrade.

## Cadence at a glance

- **Weekly** — Dependabot PRs and the scheduled audit both run Monday.
- **On dependency changes** — the audit runs on any PR touching
  `pyproject.toml` or `uv.lock`.
- **Ad hoc** — run the audit locally with
  `uv audit --locked --preview-features audit-command`, or bump the lock with
  `uv lock --upgrade`.

## Deliberate holds

Dependabot proposes bumps; it does not decide what is safe. Known holds:

- None at present. The prior `pytz`/`Jinja2` hold — kept only for the abandoned
  `legacy/` tree — was resolved in
  [issue #162](https://github.com/B-Square-Bulletin/community-calendar/issues/162)
  by deleting the tree and dropping both dependencies (plus `types-pytz`).

See [ADR 0016](adr/0016-dependency-update-automation.md) for the decision record.
