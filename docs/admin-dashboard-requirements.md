# Admin Dashboard Requirements

Replaces `report.html` with a richer, per-city dashboard for curators and admins.

## Current state (report.html)

- Feed health: list of all feeds with status (ok/error/empty), event counts, last-fetched timestamps
- Category overrides: table of curator corrections (currently empty after category rename)
- No city filtering — everything is one flat list
- No auth-gated features — public page

## Core requirements

### Per-city views
- City picker (dropdown or tabs) filters all sections to one city
- Default to the city from URL param (`?city=raleighdurham`) for consistency with main app
- Summary card per city: source count, event count, last build time

### Feed health (per city)
- Table of sources with status, event count, last successful fetch
- Flag feeds that returned 0 events (may be broken)
- Flag feeds that haven't changed in N days (may be stale)
- Sortable/filterable columns

### Category overrides (per city)
- Show corrections made by curators
- Display curator identity
- Link to the corrected event
- Show original vs new category
- These serve as few-shot examples for LLM categorization — surface stats on how often each category gets corrected

### Source coverage
- Category breakdown: how many events per category for this city
- Source breakdown: events per source, sorted by count
- Gaps: categories with few or no events (helps curators know where to look)

### Event quality
- Events missing location
- Events missing description
- Events with suspiciously short titles
- Duplicate detection stats (how many dupes were merged)

## Future considerations (not v1)

- City-scoped curator permissions (user X can only correct city Y)
- Curator activity log (who corrected what, when)
- Feed management UI (add/remove feeds without editing YAML)
- Alerting (notify curator when a feed breaks)
- Build trigger (kick off a rebuild from the dashboard)

## Tech decisions (TBD)

- XMLUI app (like the main calendar) vs standalone HTML page?
- Same Supabase project, same auth?
- Embed in main app as a route, or separate deployment?
