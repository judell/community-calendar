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
