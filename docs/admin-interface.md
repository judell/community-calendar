# Admin Interface

Features that currently require code deploys or direct DB access but should be manageable through an admin UI.

## 1. City configuration

The list of cities and their GitHub Pages URLs is hardcoded in the `load-events` edge function. Adding a city requires editing TypeScript and redeploying.

**Current**: `EVENTS_URLS` map in `supabase/functions/load-events/index.ts`

**Proposed**: A `city_config` table:

```sql
CREATE TABLE city_config (
  city text PRIMARY KEY,
  events_url text NOT NULL,
  enabled boolean DEFAULT true
);
```

The edge function queries `SELECT city, events_url FROM city_config WHERE enabled = true` instead of using a hardcoded map. Adding or disabling a city becomes a row insert/update, not a deploy.

The UI city picker (`index.html`) could also read from this table, eliminating the need to update frontend code when adding cities.

## 2. Description snippet junk-line patterns

The `getSnippet()` function in `helpers.js` strips junk lines from event descriptions before extracting a readable snippet. The patterns (e.g. lines starting with "Department:", "Tickets:", "Doors") are currently hardcoded as a regex.

**Current**: `junkPattern` regex in `getSnippet()` in `helpers.js`

**Proposed**: A `snippet_junk_patterns` table:

```sql
CREATE TABLE snippet_junk_patterns (
  id serial PRIMARY KEY,
  pattern text NOT NULL,
  description text,
  enabled boolean DEFAULT true
);
```

The client fetches enabled patterns at load time and builds the regex dynamically. Curators can add/remove patterns as new calendar sources introduce new boilerplate.

## 3. URL quality monitoring

The `/report.html` page includes a live URL Quality section that queries Supabase to show per-city breakdowns. Key metrics to monitor:

### Generic URLs

Domains where every event points to the same URL (a homepage or calendar page). These degrade the click experience — users land on a page with no direct connection to the event.

**Snapshot (2026-02-18, Santa Rosa):**

| Domain | Events | URL |
|---|---|---|
| bohemian.com | 301 | `/events-calendar/` |
| duttonestate.com | 75 | `/visit-us/tasting-reservations/` |
| pressdemocrat.com | 53 | `/events/` |
| arlenefranciscenter.org | 37 | `/calendar/` |
| sebastopolgallery.com | 25 | homepage |
| upstairsartgallery.net | 25 | homepage |

**838 of 3,771 events (22%)** use generic URLs. These come from aggregators (Bohemian, Press Democrat) that scrape venues without per-event URLs.

### Source specificity

Sources vary widely in URL quality:
- **100%**: Sonoma County Library, Riley Street Art Supply, Sonoma County Government, Sebastopol Center for the Arts
- **46-48%**: North Bay Bohemian, Press Democrat (aggregators)
- **3%**: Arlene Francis Center (single URL for all 37 events)

### HTTP sites

170 events across 35 domains still use HTTP. These may indicate unmaintained sites.

### Future: automated HTTP response checks

A scheduled check could HEAD-request a sample of URLs per domain to detect:
- Broken links (4xx/5xx)
- Redirects that dump users on a generic page
- Sites that have gone offline

This could feed into the anomaly system already in report.html.

## 4. Feed quality score

The health report currently shows feed-level metrics (event counts, errors) and URL quality separately. A composite per-feed quality score would give a single number summarizing how well a feed is performing.

### Available fields today (from events.json)

| Field | What it measures | Range across cities |
|---|---|---|
| has-description | Event has a description | 68–99% |
| has-location | Event has a location string | 52–93% |
| has-url | Event has any URL | 87–100% |
| url-specificity | Unique URLs / events (per source) | 59–96% |

### Future dimensions to add

- **has-geo**: Location includes lat/lon coordinates (not yet in the data)
- **url-reachable**: URL returns 2xx on HEAD request
- **has-end-time**: Event specifies an end time (not just start)
- **description-quality**: Description is more than boilerplate (length, uniqueness)

### Possible approach

Score each feed/source 0–100 as a weighted average of available dimensions. Display as a single percentage on the city summary line in the health report, analogous to URL Quality's "78% event-specific." Weights and thresholds TBD — the right formula depends on what dimensions matter most to users clicking through to events.
