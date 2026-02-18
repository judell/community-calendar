# Deduplication and Event Ordering

## For Curators: What You Need to Know

**Everything is automatic.** The system handles deduplication and event ordering without configuration.

**Deduplication:** A global policy favors authoritative sources (venues, libraries) over aggregators (newspapers, event platforms). When the same event appears in multiple sources, the primary source version is kept and all contributing sources are preserved in the attribution. This removes ~20% of duplicate events automatically.

**Event ordering:** Within each timeslot, events with similar titles are grouped together. "Family Storytime", "Bilingual Family Storytime", and "Yoga Storytime Series" will appear adjacent rather than scattered randomly. This uses title-similarity clustering, not just alphabetical sort.

**When adding a new source:**
- If it's a primary source (venue, library, etc.), its events will be kept over aggregator versions
- If it's an aggregator, add it to the `AGGREGATORS` set in `scripts/combine_ics.py`

**How to identify an aggregator:** pulls events from many other sources (like a newspaper events section), high event count with significant overlap, events often appear elsewhere with better metadata.

---

## Table of Contents

- [For Curators: What You Need to Know](#for-curators-what-you-need-to-know)
- [Pipeline Overview](#pipeline-overview)
- [Stage 1: Individual Scrapers](#stage-1-individual-scrapers)
- [Stage 2: combine_ics.py](#stage-2-combine_icspy)
- [Stage 3: ics_to_json.py](#stage-3-ics_to_jsonpy)
- [Stage 4: load-events Edge Function](#stage-4-load-events-edge-function)
- [Stage 5: PostgreSQL Database](#stage-5-postgresql-database)
- [Stage 6: JavaScript Client (helpers.js)](#stage-6-javascript-client-helpersjs)
- [Summary: Where Duplicates Are Handled](#summary-where-duplicates-are-handled)
- [The Root Problem](#the-root-problem)
- [Current Santa Rosa Duplicate Statistics](#current-santa-rosa-duplicate-statistics)
- [Current Solution: Global Aggregator List](#current-solution-global-aggregator-list)
- [Event Ordering by Title Similarity](#event-ordering-by-title-similarity)
- [Fuzzy LLM Dedup: Experiment Results](#fuzzy-llm-dedup-experiment-results-2026-02-17)
- [Remaining Work](#remaining-work)
- [Appendix: Future Architecture - Policy Flow](#appendix-future-architecture---policy-flow)

## Pipeline Overview

```
Sources (ICS/Scrapers)
        ↓
    combine_ics.py      ← Dedup by UID (same source only)
        ↓
    ics_to_json.py      ← Title-similarity ordering
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

**Mechanism:** Converts ICS to JSON. No dedup, but clusters events within each timeslot by title similarity (token-set algorithm, threshold 0.6) so related events appear adjacent in the calendar. See [Event Ordering by Title Similarity](#event-ordering-by-title-similarity).

**Scope:** Ordering only, not dedup.

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

| Stage | Same-Source Dups | Cross-Source Dups | Ordering |
|-------|-----------------|-------------------|----------|
| Scrapers | ✅ (within scraper) | ❌ | ❌ |
| **combine_ics.py** | ✅ (by UID) | **✅ (by title+date)** | ❌ |
| **ics_to_json.py** | ❌ | ❌ | **✅ (title similarity)** |
| load-events | ✅ (by source_uid) | ❌ | — |
| PostgreSQL | ✅ (UNIQUE constraint) | ❌ | — |
| Client (helpers.js) | ✅ | ✅ (safety net) | ✅ (by start_time) |

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

## Remaining Work

1. **Monitoring** - Add logging to track dedup effectiveness over time
2. **Report enhancement** - Show duplicate counts in the feed health report
3. ~~**Event ordering**~~ — Done. See "Event Ordering by Title Similarity" section below

---

## Fuzzy LLM Dedup: Experiment Results (2026-02-17)

### What Was Built

Fuzzy dedup in `combine_ics.py` using Claude 3.5 Haiku (batch clustering approach). Gated by `ENABLE_FUZZY_DEDUP` env var + `ANTHROPIC_API_KEY`. Code remains in `combine_ics.py` but is dormant — neither env var is set.

### Results: Not Worth Pursuing

Out of **282 "fuzzy matches"** found, roughly **~250 were false positives** (~10% precision). The LLM aggressively merged events that merely shared a date:

**Examples of wrong merges:**
- 'Tuesday Night Comedy Showcase' → 'Live Music Happy Hour' (different shows, same venue)
- 'Santa Rosa Symphony - Mahler's Third' → 'Disney's Descendants: The Musical'
- 'Beginning Watercolor Class' → 'Figure Drawing DROP-IN Session' (wrong every week for months)
- 'Vineyard Garden Wine Tasting' → 'Markham Vineyards Private Tasting' (different wineries)
- Different BiblioBus stops merged, different kids' camps merged, etc.

**Genuine catches (~20-30):** title variants like 'Boeing Boeing - The Play' → 'Boeing Boeing', 'Vallejo Gem & Mineral Show' → 'Vallejo Gem and Mineral Show'.

### Why It Was Abandoned

| Factor | Assessment |
|--------|-----------|
| Exact dedup already handles | ~1,200 events (20%) |
| Genuine fuzzy dupes remaining | ~20-30 (<1% of events) |
| Cost per run | 178 API calls, 140K input tokens |
| False positive rate | ~90% — would destroy the calendar |
| Marginal value | Not worth the complexity, cost, or risk |

The batch clustering approach (sending all events for a date to the LLM) is fundamentally ill-suited — the LLM lacks the domain knowledge to distinguish "same event, different title" from "different events, same day." Tightening the prompt might help precision but would likely hurt the already-small recall.

### If Revisited

If the ~20-30 edge cases ever matter enough, a **manual synonym table** (static mapping of known title variants) would be simpler, free, and 100% precise. No LLM needed.

---

## Event Ordering by Title Similarity

### The Problem

Events at the same day/time appeared in random order. Instances of the same recurring event — "Baby Storytime", "Family Storytime", "Preschool Storytime" at different library branches — should be grouped together, with alphabetical ordering as tiebreaker.

Simple alphabetical sort doesn't work because the *differentiating* word often comes first ("Baby", "Family", "Preschool"), scattering related events apart.

### Solution: Token-Set Similarity Clustering in `ics_to_json.py`

Events are clustered by title similarity within each timeslot during JSON generation, using a token-set similarity algorithm built on stdlib `difflib.SequenceMatcher` (no external dependencies).

**How it works:**
1. Events are sorted by `start_time`
2. Within each timeslot, pairwise token-set similarity is computed
3. Events with similarity >= 0.6 are grouped using union-find
4. Clusters are sorted alphabetically by first title; events within clusters sort alphabetically

**Token-set similarity** compares word *sets*, ignoring order. "Family Storytime" vs "Bilingual Family Storytime" scores high because the shared words dominate. This handles the core cases:
- "One-On-One Tech Help" / "Tech Help" → adjacent
- "Pine Ridge Après-Ski Cave Experience" / "Pine Ridge Après-Ski Cave Experience | Napa" → adjacent
- "Family Storytime" / "Yoga Storytime Series @ JFK" → adjacent
- "Themed Paint Along - Easter" / "Themed Paint Along - Valentine's Day" → adjacent

**Why not a library?** We evaluated `rapidfuzz` but the stdlib implementation performs well on our data sizes (~150 events/day max, small timeslots) and avoids adding a dependency to the build pipeline.

### Test Harness

The implementation was chosen using `scripts/similarity_test.py`, a standalone test harness that reads a city's `events.json` and previews how different similarity algorithms would order the calendar — without affecting it.

**Algorithms evaluated:**

| Algorithm | Pairs >= 0.6 (same timeslot) | Character |
|-----------|------------------------------|-----------|
| `sequencematcher` | 108 | Middle ground |
| `levenshtein` | 58 | Most conservative, position-sensitive |
| `token_set` | 149 | Best for this use case — catches word-order variants |

`token_set` was chosen because it handles the core case (shared words in different positions) that the others miss.

**Usage:**
```bash
# Preview calendar order for a specific date
python scripts/similarity_test.py --city santarosa --date 2026-02-19 --algorithm token_set

# Show only timeslots where clustering changes the order vs alphabetical
python scripts/similarity_test.py --city santarosa --changes-only --algorithm token_set

# Compare all algorithms side by side
python scripts/similarity_test.py --city santarosa --date 2026-02-20

# Pair analysis with score distribution
python scripts/similarity_test.py --city santarosa --pairs --algorithm token_set

# Adjust threshold
python scripts/similarity_test.py --city santarosa --changes-only --threshold 0.5
```

The test harness remains available for evolving the approach — trying new algorithms, adjusting thresholds, or evaluating on new cities. Any change to the similarity logic in `ics_to_json.py` can be previewed first in the test harness.

---

## Appendix: Future Architecture - Policy Flow

The current solution (global AGGREGATORS list) handles the immediate problem. But there will likely be a need for richer per-city policies that flow down through the entire pipeline, including scrapers.

### Why Policy Flow Matters

Currently, scrapers are city-agnostic. They output ICS files and don't know:
- What city context they're running in
- Whether their output will be deduplicated against other sources
- What quality standards apply
- What geographic boundaries matter

This means:
- Scrapers can't make intelligent decisions about what to include
- Duplicate work happens (scraping events that will be filtered later)
- No way for a city to customize scraper behavior

### Proposed Architecture

#### 1. City Policy File

Each city would have a `policy.json` (or expand the existing config):

```json
// cities/santarosa/policy.json
{
  "dedup": {
    "aggregators": ["North Bay Bohemian", "Press Democrat"],
    "match_key": "date+normalized_title_40"
  },
  "geo": {
    "allowed_cities": ["Santa Rosa", "Sebastopol", ...],
    "excluded_cities": ["San Francisco", ...]
  },
  "quality": {
    "require_location": false,
    "require_description": false,
    "min_title_length": 3
  },
  "sources": {
    "bohemian": {
      "enabled": true,
      "priority": "low",
      "notes": "Aggregator - deprioritize in dedup"
    },
    "library_intercept": {
      "enabled": true,
      "priority": "high",
      "geo_filter": true
    }
  }
}
```

#### 2. Scraper Context

Scrapers would receive city context, either via:

**Option A: Command-line flag**
```bash
python scrapers/bohemian.py --city santarosa --output cities/santarosa/bohemian.ics
```

**Option B: Environment variable**
```bash
CALENDAR_CITY=santarosa python scrapers/bohemian.py --output cities/santarosa/bohemian.ics
```

**Option C: Infer from output path**
```python
# Scraper detects city from output path
city = Path(args.output).parent.name  # "santarosa"
```

#### 3. BaseScraper Policy Integration

The `BaseScraper` class would gain policy awareness:

```python
class BaseScraper:
    def __init__(self, city=None):
        self.city = city
        self.policy = self.load_policy(city) if city else {}
    
    def load_policy(self, city):
        policy_file = Path(f'cities/{city}/policy.json')
        if policy_file.exists():
            return json.loads(policy_file.read_text())
        return {}
    
    def should_include_event(self, event):
        """Apply policy filters before yielding event."""
        # Geo filter
        if self.policy.get('geo', {}).get('allowed_cities'):
            if not self.location_matches_policy(event.get('location')):
                return False
        
        # Quality filter
        quality = self.policy.get('quality', {})
        if quality.get('require_location') and not event.get('location'):
            return False
        
        return True
```

#### 4. Policy-Aware Workflow

The GitHub Actions workflow would pass city context:

```yaml
- name: Scrape Santa Rosa sources
  run: |
    export CALENDAR_CITY=santarosa
    python scrapers/bohemian.py --output cities/santarosa/bohemian.ics
    python scrapers/library_intercept.py --output cities/santarosa/library.ics
```

### Benefits of Policy Flow

1. **Early filtering** - Scrapers skip irrelevant events at source, reducing downstream work

2. **City customization** - Different cities can have different quality thresholds, geo boundaries, source priorities

3. **Single source of truth** - Policy defined once, applied everywhere

4. **Scraper intelligence** - Scrapers can make informed decisions (e.g., "I'm an aggregator for this city, maybe I should yield fewer events")

5. **Easier testing** - Can validate scraper output against policy without running full pipeline

### Migration Path

1. **Phase 1** (current): Global AGGREGATORS list in combine_ics.py
2. **Phase 2**: Move AGGREGATORS to per-city policy files
3. **Phase 3**: Add city context to scraper invocations
4. **Phase 4**: BaseScraper reads and applies policy
5. **Phase 5**: Scrapers can declare their own characteristics ("I am an aggregator")

### Client Dedup Retained as Safety Net

The client-side `dedupeEvents()` function in `helpers.js` remains in place. It duplicates the logic in `combine_ics.py` but this is intentional:

- **Harmless overhead** - The function is fast and cached
- **Safety net** - Catches any duplicates that slip through upstream (edge cases, timing issues)
- **No code churn** - Removing it would require testing all the `mergedIds` logic for picks

The upstream dedup in `combine_ics.py` does the heavy lifting (~1,200 duplicates removed). The client dedup now rarely finds anything to merge, but keeping it costs nothing and provides defense in depth.
