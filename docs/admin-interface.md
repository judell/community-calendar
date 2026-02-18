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
