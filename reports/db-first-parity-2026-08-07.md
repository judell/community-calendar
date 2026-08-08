---
report_id: db-first-parity-2026-08-07
title: DB-first scraper execution parity proof, all eight cities
date: 2026-08-07
commit: a135e162c0b271644b3480f1ed696a862b7a4680
overall_status: pass
summary:
  total_checks: 3
  passed: 3
  failed: 0
  warning: 0
findings:
  - id: F001
    status: pass
    title: Static parity — every active DB scraper command exactly equals its workflow-manifest counterpart in all eight cities
    scope: execution-set equality
    action_ids: []
  - id: F002
    status: pass
    title: Dynamic parity — all eight cities build healthily in --db-first mode with zero failures, zero missing outputs, zero fallback uses, zero drift
    scope: db-first builds
    action_ids: []
  - id: F003
    status: pass
    title: Fallback telemetry verified — unreachable DB triggers a loud, counted feeds.txt fallback, and a fallback on a credentialed --db-first run fails the build
    scope: fallback behavior
    action_ids: []
actions:
  - id: A001
    status: open
    title: Harden output cleanup for retired sources — stale artifacts from since-retired rows pollute the combine glob and validation until manually deleted (cleaned by hand today in toronto, santarosa, montclair, raleighdurham)
    owner: agent
  - id: A002
    status: open
    title: Re-check the SiteGround-blocked scrapers after the next CI run — the WAF is transient/IP-based and asymmetric (Uptown Napa cleared to 23 events, Ner Tamid partially to 50, LBC/YWCA/Buddies/High Park/Scadding/Carolina Theatre/Buskirk-Chumley blocked from this machine at various points today)
    owner: human+agent
---

# Outcome

| Check | Result |
| --- | --- |
| Static parity | ALL-MATCH: 350/350 active DB scraper rows equal the workflow manifest (canonicalized) across all eight cities |
| Dynamic parity | 8/8 cities: mode `db`, 0 scraper failures, 0 missing outputs, 0 fallbacks, 0 drift |
| Fallback telemetry | Verified: loud `[db-first] fallback=feeds.txt reason=...`, counted in the report, fails a credentialed `--db-first` run |

# Dynamic runs (all 2026-08-07 afternoon, Python 3.10 parity venv)

| City | Rows | Failures | Fallbacks | Drift | Events (combine=convert) | vs same-day workflow baseline |
| --- | --- | --- | --- | --- | --- | --- |
| asheville | 43 | 0 | 0 | 0 | 4,558 | +27 (rhp_events fix baked in; dedup absorbs most of the 111-event raw recovery) |
| bloomington | 70 | 0 | 0 | 0 | 6,386 | +29 (live drift) |
| davis | 8 | 0 | 0 | 0 | 633 | identical to the workflow-driven reconcile run |
| lancaster | 30 | 0 | 0 | 0 | 2,524 | +8 (live drift; 2 Chameleon rows retired since baseline, both were 0-event) |
| montclair | 29 | 0 | 0 | 0 | 2,358 | +150 (film repair +50, Foundation conversion, Ner Tamid partial WAF clearing +50) |
| raleighdurham | 22 | 0 | 0 | 0 | 2,613 | −26 (NC Cultural Resources blocked locally by the known SSL trust-store gap; WAF trio at 0 this run) |
| santarosa | 64 | 0 | 0 | 0 | 5,777 | −125 (Sonoma Valley Events owner-removal −~503 netted against the day's repairs; within documented same-day swing) |
| toronto | 84 | 0 | 0 | 0* | 8,095 | +1,871 (retired legacy row stopped clobbering blogTO's 1,016 events; TPL fetches recovered from morning rate-limiting) |

\* toronto surfaced one cosmetic drift item mid-sweep — the DB's mis-cased
"Blogto" display name, exposed for the first time because blogTO's real
local output finally provided a trustworthy `X-SOURCE`. Fixed the same
hour via the provenance-safe sync; final state 0.

Every non-zero exit code in the sweep traces to pre-existing, documented
source-health issues (HTML-serving live feeds classified `not_ics`, the
WAF-blocked scrapers below, the local SSL gap) — none are DB-first
breakage.

# Findings of note

## Stale artifacts from retired sources (A001)

`local_build.py` cleans outputs only for currently-active rows, and the
validator scans the whole city directory — so outputs left behind by
sources retired earlier the same day kept tripping `not_ics` warnings
and, in toronto's case, feeding 16 junk files to the combine glob.
Cleaned by hand today in toronto (22 files), santarosa (6), montclair
(2), and raleighdurham (3). Hardening candidate: clean or quarantine
`.ics` files in the city directory that belong to no active source and
no declared static reference.

## SiteGround WAF: transient, IP-based, asymmetric (A002)

The day's heavy probing from this machine progressively tripped
SiteGround's captcha across at least eight venues in four cities.
Decisive observations: Uptown Theatre Napa cleared fully (23 events
this sweep after being blocked at conversion time), Temple Ner Tamid
cleared partially (50 events, page 2 blocked), and Carolina Theatre —
81 events in the morning baseline — returned a challenge page (HTTP
202, 178 bytes) parsed as a clean-but-empty fetch. The conversions
behave exactly as adjudicated: valid empty calendars on blocked days,
events when the WAF relents. The next CI run (different IP, one small
burst) is the real test; if CI also blocks persistently, the open
venue-allowlist / headless-harness follow-up in the santarosa and
toronto checklists is the path.

# Verdict

DB-first execution is proven: the DB and workflow express the identical
execution set statically, and executing from the DB produces healthy
builds in every city with fallback telemetry demonstrably loud. The
workflow switch (cleanup-plan step 6) can proceed on this evidence.

# Artifacts

- Per-city build reports/logs: scratchpad `{city}-dbfirst-build.{json,log}` (session-local)
- Static parity check: inline (backfill canonicalization over all eight cities, ALL-MATCH)
- Baselines: `reports/*-2026-08-07-soak.md`, `reports/davis-2026-08-07-reconcile.md`, `reports/bloomington-2026-08-07-postsync.md`
