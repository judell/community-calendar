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

## Goal: City-Level Deduplication Policy

**Deduplication policy should flow down from the city level and affect all calendars the same way, reliably.**

### Design Principles

1. **Single policy definition per city** - One file (e.g., `cities/{city}/dedup_policy.json`) defines that city's deduplication rules

2. **Policy applied in one place** - `combine_ics.py` is the natural location since it already processes all sources for a city

3. **Scrapers should NOT deduplicate cross-source** - Scrapers may still dedupe internal pagination issues, but should not make policy decisions about which sources win

4. **Client dedup becomes a safety net** - The client-side `dedupeEvents()` remains as a fallback for edge cases, but should rarely need to merge events if upstream dedup works correctly

### Proposed Policy Structure

```json
// cities/santarosa/dedup_policy.json
{
  "match_key": "date+normalized_title_40",
  "source_priority": [
    // Highest priority first - when duplicates found, keep the highest priority source
    "Copperfield's Books",
    "Barrel Proof Lounge",
    "Luther Burbank Center",
    "Charles M. Schulz Museum",
    "Sonoma County Library",
    "Santa Rosa Junior College",
    "Sonoma County Government",
    "City of Santa Rosa Legistar",
    "GoLocal Cooperative",
    "Meetup:*",
    "North Bay Bohemian",
    "Press Democrat"
  ],
  "always_keep": [
    // Sources that are never deduplicated away, even if lower priority
    // (useful for sources with unique metadata)
  ]
}
```

### Implementation Plan

1. **Phase 1: Define policy format**
   - Create JSON schema for dedup policies
   - Add sample policy for Santa Rosa

2. **Phase 2: Implement in combine_ics.py**
   - Load city's dedup_policy.json if present
   - After combining all ICS files, group by match_key
   - For each group, keep only the highest-priority source
   - Log what was deduplicated for debugging

3. **Phase 3: Remove scattered dedup logic**
   - Audit scrapers for cross-source dedup logic (keep internal dedup only)
   - Simplify client-side dedupeEvents() since most work happens upstream

4. **Phase 4: Per-city rollout**
   - Start with Santa Rosa (most duplicates)
   - Validate results, tune policy
   - Roll out to other cities

### Benefits

- **Predictable behavior** - Same policy applies everywhere
- **Easy to tune** - Edit one JSON file to change priority
- **Testable** - Can write tests that verify policy is applied correctly
- **City-specific** - Different cities can have different policies (e.g., Toronto might prioritize NOW Toronto over other aggregators)

---

## Implementation Status

### ✅ DONE: Cross-Source Deduplication in combine_ics.py

Implemented source-priority deduplication:

1. **Groups events by `(date, normalized_title[:40])`** - same logic as client
2. **Loads city policy** - reads `dedup_policy.json` if present
3. **Applies source priority** - when duplicates found, keeps highest-priority source
4. **Removes lower-priority duplicates** before writing combined.ics

**Results for Santa Rosa:**
- Before: 6,054 events
- After: 4,837 events
- Removed: 1,217 duplicates (~20% reduction)

### ✅ DONE: Santa Rosa dedup_policy.json

Created `cities/santarosa/dedup_policy.json` with source priority:
- Primary venues first (Copperfield's, Barrel Proof, Luther Burbank, etc.)
- Institutions next (Library, SRJC, Government)
- Meetup groups
- Aggregators last (Bohemian, then Press Democrat)

### Remaining Work

1. **Add policies for other cities** - Create `dedup_policy.json` for Petaluma, Toronto, etc.
2. **Client dedup simplification** - The client `dedupeEvents()` can now be simplified since most duplicates are removed upstream (still needed as safety net)
3. **Monitoring** - Add logging/metrics to track dedup effectiveness over time
