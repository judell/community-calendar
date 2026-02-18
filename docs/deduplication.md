# Deduplication Mechanics in Community Calendar

This document describes the existing deduplication mechanisms at each stage of the pipeline, identifies gaps where cross-source duplicates are not being handled, and proposes a city-level policy system.

## Pipeline Overview

```
Sources (ICS/Scrapers)
        ↓
    combine_ics.py      ← Dedup by UID (same source only)
        ↓
    ics_to_json.py      ← No dedup (passthrough)
        ↓
    events.json
        ↓
    load-events (Supabase Edge Function) ← Dedup by source_uid
        ↓
    PostgreSQL (events table)  ← UNIQUE constraint on source_uid
        ↓
    Client (helpers.js dedupeEvents) ← Dedup by title+start_time
```

---

## Stage 1: Individual Scrapers

**Location:** `scrapers/*.py`, `scrapers/lib/*.py`

**Mechanism:** Many scrapers have their own internal deduplication to handle pagination bugs or multiple data sources within the same site.

Examples:
- `scrapers/lib/ics.py` - Deduplicates by UID when fetching multiple ICS feeds
- `scrapers/catscradle.py` - Deduplicates by URL (RSS pagination returns duplicates)
- `scrapers/volunteer_toronto.py` - Deduplicates by (title, start_time) tuple
- `scrapers/sonoma_county_gov.py` - Deduplicates by URL
- `scrapers/davis_chamber.py` - Deduplicates by event ID

**Scope:** Within a single scraper only. Does NOT handle cross-source duplicates.

---

## Stage 2: combine_ics.py

**Location:** `scripts/combine_ics.py`

**Mechanism:** Two-phase deduplication:

### Phase 1: UID-based dedup (same-source duplicates)
```python
# Remove duplicates based on UID
seen_uids = set()
uid_deduped = []
for event in all_events:
    uid_match = re.search(r'UID:([^\r\n]+)', event['content'])
    if uid_match:
        uid = uid_match.group(1)
        if uid not in seen_uids:
            seen_uids.add(uid)
            uid_deduped.append(event)
    else:
        uid_deduped.append(event)
```

### Phase 2: Cross-source dedup (title+date matching)
```python
unique_events = dedupe_cross_source(uid_deduped, input_dir)
```

The `dedupe_cross_source()` function:
1. Groups events by `(date, normalized_title[:40])`
2. Loads source priority from `dedup_policy.json` if present
3. For each group with multiple events, keeps only the highest-priority source
4. Logs how many duplicates were removed

**Scope:** Now handles BOTH same-source and cross-source duplicates.

**Result:** Santa Rosa went from 6,054 to 4,837 events (~20% reduction).

---

## Stage 3: ics_to_json.py

**Location:** `scripts/ics_to_json.py`

**Mechanism:** None. Pure conversion from ICS to JSON format.

**Scope:** Passthrough only.

---

## Stage 4: load-events Edge Function

**Location:** `supabase/functions/load-events/index.ts`, lines 53-59

**Mechanism:** Deduplicates by `source_uid` before upserting to database:

```typescript
// Deduplicate by source_uid
const uniqueEvents = new Map();
for (const event of allEvents) {
  if (event.source_uid && !uniqueEvents.has(event.source_uid)) {
    uniqueEvents.set(event.source_uid, event);
  }
}
```

Then upserts with conflict handling:
```typescript
const { error } = await supabase
  .from("events")
  .upsert(batch, {
    onConflict: "source_uid",
    ignoreDuplicates: false
  });
```

**Scope:** Prevents duplicate `source_uid` values across all cities. 

**Gap:** Same issue as combine_ics.py - cross-source duplicates have different `source_uid` values.

---

## Stage 5: PostgreSQL Database

**Location:** `supabase/ddl/events.sql`

**Mechanism:** UNIQUE constraint on `source_uid`:

```sql
source_uid text UNIQUE,   -- unique ID from source for deduplication

-- Compound unique index for deduplication by source
CREATE UNIQUE INDEX IF NOT EXISTS events_source_source_uid_key 
  ON events (source, source_uid);
```

**Scope:** Enforces that each `source_uid` appears only once in the database.

**Gap:** Still doesn't address cross-source duplicates with different UIDs.

---

## Stage 6: JavaScript Client (helpers.js)

**Location:** `helpers.js`, lines 185-247 (`dedupeEvents` function)

**Mechanism:** Groups events by `(normalized_title + start_time)` and merges duplicates:

```javascript
function dedupeEvents(events) {
  const groups = {};
  events.forEach(e => {
    // Normalize start_time to ISO string for consistent dedup
    const normalizedTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    const key = (e.title || '').trim().toLowerCase() + '|' + normalizedTime;
    if (!groups[key]) {
      groups[key] = { ...e, sources: new Set([e.source]), mergedIds: [e.id] };
    } else {
      // Track all merged event IDs (for picks to work across sources)
      groups[key].mergedIds.push(e.id);
      groups[key].sources.add(e.source);
      // Prefer non-empty values for other fields
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      // ...
    }
  });
  // ...
}
```

**Scope:** THIS IS THE ONLY PLACE that handles cross-source duplicates.

**Features:**
- Groups by normalized `title + start_time`
- Tracks `mergedIds` so picks work across sources
- Merges `sources` into a Set, displays comma-separated
- Prefers "authoritative" source (source name appears in location) first
- Falls back to non-empty field values from any source

**Gap:** 
- Deduplication happens at render time, so the database still contains duplicates
- Every page load re-runs deduplication on potentially thousands of events
- The `mergedIds` logic is complex and necessary because the database has multiple records

---

## Summary: Where Duplicates Are Handled

| Stage | Handles Same-Source Dups | Handles Cross-Source Dups |
|-------|-------------------------|---------------------------|
| Scrapers | ✅ (within scraper) | ❌ |
| **combine_ics.py** | ✅ (by UID) | **✅ (by title+date)** |
| ics_to_json.py | ❌ (passthrough) | ❌ |
| load-events | ✅ (by source_uid) | ❌ |
| PostgreSQL | ✅ (UNIQUE constraint) | ❌ |
| Client (helpers.js) | ✅ | ✅ (safety net) |

---

## The Root Problem

Cross-source duplicates occur because:

1. **CitySpark is a shared upstream** - Both North Bay Bohemian and Press Democrat use CitySpark as their event aggregation platform. CitySpark itself scrapes events from many local sources.

2. **Each aggregator assigns its own UID** - When Bohemian and Press Democrat both have the same event, they each generate a unique identifier:
   - Bohemian: `260217UHmG-QHZsEmxyEc-inQ_6w`
   - Press Democrat: `260217mDgKX_6hIk22Q_0HsUy5bw`

3. **Primary sources + aggregators** - Events from primary sources (libraries, venues) also get scraped by aggregators, creating duplicates:
   - Sonoma County Library: `event-12345@sonomalibrary.org`
   - Bohemian (via CitySpark): `260217xyz...`

---

## Current Santa Rosa Duplicate Statistics

| Metric | Value |
|--------|-------|
| Total events | 6,064 |
| Unique (title+date) | 4,846 |
| Duplicate entries | 1,218 (~20%) |

### Top Overlapping Source Pairs

| Source Pair | Duplicate Count |
|-------------|----------------|
| North Bay Bohemian ↔ Press Democrat | 509 |
| North Bay Bohemian ↔ Sonoma County Library | 310 |
| Press Democrat ↔ Sonoma County Library | 72 |

---

## Key Architectural Problem: Scattered Deduplication Policies

The current system has deduplication logic scattered across multiple locations:

- Individual scrapers implement their own internal deduplication
- `combine_ics.py` has its own UID-based dedup
- The edge function has its own source_uid dedup
- The client has the most sophisticated title+time dedup

**This is wrong.** Each component implementing its own policy means:

1. **Inconsistent behavior** - Different scrapers handle duplicates differently
2. **No city-level control** - A city can't say "prefer library events over aggregators"
3. **Policy changes require touching multiple files** - Want to change dedup logic? Edit scrapers, combine_ics.py, helpers.js...
4. **Testing is difficult** - Hard to verify deduplication works correctly end-to-end

---

## Current Solution: Global Aggregator List

Rather than per-city policy files, we use a simple global rule: **primary sources beat aggregators**.

### How It Works

`combine_ics.py` has a global `AGGREGATORS` set:

```python
AGGREGATORS = {
    'North Bay Bohemian',
    'Press Democrat', 
    'NOW Toronto',
    'Toronto Events (Tockify)',
}
```

When duplicates are found (same title + date), the code keeps the non-aggregator version:

```python
def is_aggregator(source_name):
    return source_name in AGGREGATORS

# Sort: primary sources first, aggregators last
group.sort(key=lambda e: (1 if is_aggregator(source) else 0))
# Keep the first (primary source if available)
unique_events.append(group[0])
```

### Why Not Per-City Policies?

We initially planned per-city `dedup_policy.json` files with source priority lists. But we realized:

1. The only rule that matters is "aggregators go last"
2. Everything else (venue vs library vs meetup) doesn't matter - those sources rarely overlap
3. Per-city files would just list every source in arbitrary order

A simple global aggregator list accomplishes the same thing with zero configuration.

### Results

| City | Before | After | Removed |
|------|--------|-------|--------|
| Santa Rosa | 6,054 | 4,837 | 1,217 (20%) |
| Toronto | 5,097 | 4,558 | 539 (11%) |

---

## For Curators: What You Need to Know

**Deduplication is automatic.** You don't need to configure anything.

When you add a new source:
- If it's a primary source (venue, library, etc.), its events will be kept over aggregator versions
- If it's an aggregator, add it to the `AGGREGATORS` set in `combine_ics.py`

**How to identify an aggregator:**
- Pulls events from many other sources (like a newspaper events section)
- High event count with significant overlap with other sources  
- Events often appear elsewhere with better metadata

**When adding a new aggregator:**
1. Add the source name to `AGGREGATORS` in `scripts/combine_ics.py`
2. That's it - duplicates will be handled automatically

---

## Remaining Work

1. **Monitoring** - Add logging to track dedup effectiveness over time
2. **Report enhancement** - Show duplicate counts in the feed health report

### Client Dedup Retained as Safety Net

The client-side `dedupeEvents()` function in `helpers.js` remains in place. It duplicates the logic in `combine_ics.py` but this is intentional:

- **Harmless overhead** - The function is fast and cached
- **Safety net** - Catches any duplicates that slip through upstream (edge cases, timing issues)
- **No code churn** - Removing it would require testing all the `mergedIds` logic for picks

The upstream dedup in `combine_ics.py` does the heavy lifting (~1,200 duplicates removed). The client dedup now rarely finds anything to merge, but keeping it costs nothing and provides defense in depth.
