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
3. **Fuzzy matching for variant titles** - See next section

---

## Fuzzy Title Matching with LLM

### The Problem

Current dedup uses exact matching on `(date, normalized_title[:40])`. This misses duplicates where the same event has different titles across sources:

| Date | Sports Basement (primary) | Bohemian (aggregator) |
|------|---------------------------|----------------------|
| 2026-02-22 | `SANTA ROSA RIDE GROUP` | `Group Rides with Sports Basement` |
| 2026-02-24 | `SANTA ROSA RUN CLUB` | `Tuesday Night Run Club at Sports Basement` |
| 2026-03-10 | `BROOKS DEMO RUN AT SB SANTA ROSA` | `Brooks Demo Run at Sports Basement Santa Rosa` |

These are clearly the same events but title normalization doesn't catch them.

### Proposed Solution: LLM-Assisted Fuzzy Matching

Use OpenAI or Anthropic API to identify likely duplicates that exact matching misses.

#### Approach 1: Candidate Generation + LLM Verification

**How it works:**
1. Use cheap heuristics to find *candidate* duplicate pairs (same date + same location, or same date + overlapping keywords)
2. Only send candidates to the LLM for verification
3. LLM returns yes/no for each pair

**Pros:**
- Minimal LLM calls (only candidates, not all events)
- Easy to tune heuristics to reduce false candidates
- Can cache pair results

**Cons:**
- May miss duplicates if heuristics are too strict
- Multiple LLM calls (one per candidate pair)
- Heuristics add complexity

```python
def find_fuzzy_duplicates(events):
    # Group by date first (cheap filter)
    by_date = group_by_date(events)
    
    candidates = []
    for date, day_events in by_date.items():
        if len(day_events) < 2:
            continue
        
        # Find pairs with same location or overlapping keywords
        for i, e1 in enumerate(day_events):
            for e2 in day_events[i+1:]:
                if likely_same_event(e1, e2):  # cheap heuristics
                    candidates.append((e1, e2))
    
    # Ask LLM to verify candidates
    verified = []
    for e1, e2 in candidates:
        if llm_says_same_event(e1, e2):
            verified.append((e1, e2))
    
    return verified

def likely_same_event(e1, e2):
    """Cheap heuristics to find candidate duplicates."""
    # Same location?
    loc1, loc2 = e1.get('location', '').lower(), e2.get('location', '').lower()
    if loc1 and loc2 and (loc1 in loc2 or loc2 in loc1):
        return True
    
    # Overlapping significant words in title?
    words1 = set(w for w in e1.get('title', '').lower().split() if len(w) > 3)
    words2 = set(w for w in e2.get('title', '').lower().split() if len(w) > 3)
    if len(words1 & words2) >= 2:
        return True
    
    # Same time and one source is aggregator?
    if e1.get('start_time') == e2.get('start_time'):
        if is_aggregator(e1.get('source')) or is_aggregator(e2.get('source')):
            return True
    
    return False
```

#### Approach 2: Batch LLM Clustering

**How it works:**
1. For each date, send ALL events to the LLM in one prompt
2. Ask it to return clusters of same-event groups
3. Keep one event per cluster (highest priority source)

**Pros:**
- Single LLM call per date (simpler, potentially cheaper)
- LLM sees full context, can catch non-obvious matches
- No heuristics to tune

**Cons:**
- Larger prompts (more tokens)
- May hit context limits on busy days
- Less control over matching logic

```
Prompt: "Here are events on 2026-02-22. Group any that are the same event:

1. SANTA ROSA RIDE GROUP (Sports Basement, 9am)
2. Group Rides with Sports Basement (North Bay Bohemian, 9am)
3. Farmers Market at Plaza (GoLocal, 8am)
4. Tuesday Run Club (Sports Basement, 6pm)
5. Evening Run at Sports Basement (Bohemian, 6pm)

Respond ONLY with JSON grouping indices: [[1,2], [4,5], [3]]"
```

**Response:** `[[1,2], [4,5], [3]]`

This tells us events 1&2 are the same, 4&5 are the same, and 3 is unique.

#### Recommendation

**Start with Approach 2** (batch clustering) because:
- Simpler to implement
- No heuristics to tune and maintain
- Single call per date is easier to reason about
- Can fall back to Approach 1 if costs are too high

#### Cost Considerations

- Only run on events sharing the same date AND location (or no location)
- Cache results (same event pairs don't need re-verification)
- Run as batch job, not real-time
- Estimate: ~$0.01-0.05 per city per day with GPT-4o-mini

#### Implementation Location

Add to `combine_ics.py` after exact-match dedup:

```python
# Phase 1: Exact match dedup (current)
unique_events = dedupe_cross_source(uid_deduped, input_dir)

# Phase 2: Fuzzy match dedup (new)
if os.environ.get('ENABLE_FUZZY_DEDUP'):
    unique_events = dedupe_fuzzy(unique_events)
```

Gate behind environment variable for gradual rollout.

#### Matching Signals

Beyond title similarity, the LLM can consider:
- Same date and time
- Same or similar location
- Overlapping keywords ("run", "club", "sports basement")
- One title is substring/expansion of another
- Same venue mentioned in description

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
