# 0018. A Scraper Fails When It Does Not Reach Its Source

Date: 2026-10-23

## Status

Accepted

## Context

A scraper that cannot reach its source used to catch the transport error and
return `[]`. `BaseScraper.run()` then wrote a valid-empty calendar and exited 0.
Under ADR 0017's `ran_sources` manifest, exit 0 plus a parseable calendar marks
a source as ran, so the stale sweep treated an outage as a dormant source and
deleted its rows. `CONTEXT.md` already called such a run a failed source, but
nothing enforced it: 54 of Bloomington's 72 commands rode a module that
swallowed its primary fetch.

## Decision

A scraper declares that its primary fetch reached the source by calling
`BaseScraper.mark_source_reached()` once the listing or API payload has come
back and parsed. `run()` resets the declaration, and when `fetch_events()`
returns no events without it, raises `SourceNotReachedError`: non-zero exit, no
`.ics`, rows preserved.

The check reads the raw result of `fetch_events()`, before the Horizon filter,
so a source whose events all sit beyond the Horizon still writes a quiet
calendar. A declared empty result is a genuine quiet source and stays
sweepable.

Migration is per subclass and fails safe. An unmigrated scraper that returns
events is unaffected; one that returns `[]` fails loudly and keeps its rows
instead of sweeping them. Non-Bloomington scrapers migrate when they are next
touched.

## Consequences

Quiet and failed are distinguishable for every migrated scraper; the "a source
that ran empty is indistinguishable from a failed one" cost recorded in ADR
0017 now applies only to scrapers that have not migrated. A scraper that
declares after merely receiving HTTP 200 will treat a block page or a changed
layout as quiet; that ambiguity is out of scope, so the declaration should
follow the parse the module relies on rather than the status code alone.

## Alternatives Considered

- A result object from `fetch_events()` carrying `(events, reached)` would
  change every scraper's signature and return type; a declaration call is one
  line at each fetch site.
- A template method splitting "fetch" from "parse" would rewrite every module.
- An opt-out flag for unmigrated scrapers would let undeclared empty runs hide,
  which is the defect this decision removes.
