# Curator Enrichment Design

## Next Steps (2026-02-04)

### EnrichmentDialog
- [x] Component scaffolded in `components/EnrichmentDialog.xmlui`
- [ ] Need icons for recurrence UI (chevron, calendar, check)
- [ ] XMLUI has limited icon set (~100 icons, manually enumerated)

### Icons Blocker
XMLUI's `Icon` component only supports ~100 hand-registered icons in `IconProvider.tsx`. Posted proposal to [xmlui-org/xmlui#1203](https://github.com/xmlui-org/xmlui/issues/1203) recommending:
- Add **Lucide** (1500+ icons, Feather fork)
- Namespace syntax: `<Icon name="lucide/chevron-down" />`
- Dynamic lookup with `kebabToPascal` transform
- Backward compatible with existing icon names

**Workaround options while waiting:**
1. Use existing icons that are close enough
2. Inline SVG in XMLUI (if supported)
3. Build locally with added icons

### After Icons Resolved
1. Complete EnrichmentDialog UI (frequency select, day buttons, notes)
2. Create `event_enrichments` table (migration ready in design below)
3. Update `my-picks` edge function to include RRULE in ICS output
4. Wire save button to upsert enrichment

---

## Problem

Scraped event data is often sparse. Example: the Bluegrass Jam at Occidental Center for the Arts appears as individual `VEVENT` entries per occurrence, not as a proper recurring event with `RRULE`.

```ics
BEGIN:VEVENT
SUMMARY:Bluegrass Jam Night
DTSTART;VALUE=DATE-TIME:20260203T190000
DTEND;VALUE=DATE-TIME:20260203T210000
DESCRIPTION:
URL:https://www.occidentalcenterforthearts.org/upcoming-events/bluegrass-jam-night-7jhnj
END:VEVENT
```

No `RRULE` - just standalone events scraped from monthly listings.

## Vision

Curators who pick events can enrich them, producing high-quality calendar data. When you subscribe to a curator's feed, you get their enriched view.

## Current Schema

| Table | Purpose |
|-------|---------|
| `events` | Basic fields: title, start_time, end_time, location, description, url, source |
| `picks` | Simple join table: user_id → event_id (no enrichment capability) |
| `feed_tokens` | Maps user to their feed URL token |

### Current RLS Ownership

| Table | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| `events` | Anyone (public) | — | — | — |
| `picks` | Own rows (`auth.uid() = user_id`) | Own rows | — | Own rows |
| `feed_tokens` | Own rows | Own rows | — | — |

Events have no owner - public read, writes only via scrapers/edge functions with service role.

## Proposed: Enrichments with Attribution

Enrichments flow both ways - curators improve their own feed AND contribute to the commons with attribution.

### New Table

```sql
CREATE TABLE event_enrichments (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Enrichment fields (null = no change from canonical)
  rrule text,              -- "FREQ=WEEKLY;BYDAY=TU"
  description text,
  location text,
  categories text[],

  -- Provenance
  created_at timestamptz DEFAULT now(),

  UNIQUE(event_id, curator_id)
);
```

### RLS for Enrichments

```sql
-- Users can view all enrichments (for discovery/adoption)
CREATE POLICY "Enrichments are publicly readable"
  ON event_enrichments FOR SELECT
  USING (true);

-- Users can only create/edit their own enrichments
CREATE POLICY "Users can manage own enrichments"
  ON event_enrichments FOR INSERT
  WITH CHECK (auth.uid() = curator_id);

CREATE POLICY "Users can update own enrichments"
  ON event_enrichments FOR UPDATE
  USING (auth.uid() = curator_id);

CREATE POLICY "Users can delete own enrichments"
  ON event_enrichments FOR DELETE
  USING (auth.uid() = curator_id);
```

## UX for Enrichment

The curator should NOT need to know RRULE syntax. UI provides friendly inputs:

- "Repeats: weekly on Tuesdays" → system generates `RRULE:FREQ=WEEKLY;BYDAY=TU`
- Category picker
- Description editor

## Feed Generation

When generating a curator's ICS feed, layer:

1. Base event data from `events`
2. Curator's enrichments from `event_enrichments`

The `my-picks` function would need to handle RRULE in output:

```typescript
if (enrichment?.rrule) {
  lines.push(`RRULE:${enrichment.rrule}`);
}
```

## Open Question: Cross-Feed Visibility

If multiple curators enrich the same event differently, how does a non-curator consumer see it?

Options considered:

1. **First enrichment wins** - earliest timestamp
2. **Curator reputation** - weight by track record
3. **Consensus** - if 3 curators all say "weekly on Tuesday", use that
4. **Enrichments only in curator feeds** - subscribe to a good curator to get good data

**Current thinking: Option 4** - enrichments are a curator's value-add to *their* feed. The attribution is implicit in whose feed you're consuming. Simplest model, preserves curator identity.

---

## Broader View: Feed Composition

Curation isn't only adding and enriching - it's also filtering and remixing. A curator's feed is a composition of multiple sources with rules applied.

### Feed Sources

A curator's feed can include:

1. **Filtered base events** - declarative rules against the raw event pool
2. **Explicit picks** - hand-selected events
3. **Pass-alongs** - other curators' picks republished into this feed
4. **Enrichments** - overlaid on any of the above

### Curator Needs

- Declare filter rules (and test them)
- Make explicit picks
- Follow/pass-along other curators' picks
- Enrich events (recurrence, description, categories)
- Preview the composed result
- Evolve rules over time without breaking subscribers

### Proposed Data Structures

```sql
-- Filter rules for automatic inclusion/exclusion
CREATE TABLE feed_rules (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  name text,                    -- "Sebastopol music events"
  rule_type text NOT NULL,      -- 'include' or 'exclude'
  conditions jsonb NOT NULL,    -- filter conditions
  priority int DEFAULT 0,       -- higher = evaluated later
  enabled boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Pass-alongs: include another curator's picks in my feed
CREATE TABLE feed_sources (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,      -- me
  source_curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE, -- whose picks I include
  enabled boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  UNIQUE(curator_id, source_curator_id)
);

-- Explicit picks (existing, but shown for completeness)
CREATE TABLE picks (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, event_id)
);

-- Enrichments with attribution
CREATE TABLE event_enrichments (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  rrule text,
  description text,
  location text,
  categories text[],
  created_at timestamptz DEFAULT now(),
  UNIQUE(event_id, curator_id)
);
```

### Rule Conditions Schema

The `conditions` JSONB could support:

```json
{
  "source_in": ["occidental_arts", "sebastopol_times"],
  "title_contains": ["music", "concert", "jam"],
  "title_not_contains": ["cancelled"],
  "location_contains": ["Sebastopol", "Occidental"],
  "categories_include": ["music", "community"],
  "day_of_week": [2, 4],
  "date_after": "2026-01-01",
  "date_before": "2026-12-31"
}
```

All conditions within a rule AND together. Multiple include rules OR together. Exclude rules subtract from the result.

### Feed Generation Algorithm

```
1. Start with empty set
2. For each include rule (by priority):
   - Find matching events
   - Add to set
3. Add explicit picks
4. Add picks from followed curators (feed_sources)
5. For each exclude rule (by priority):
   - Remove matching events from set
6. For each event in set:
   - Apply enrichments (curator's own, or from source curator for pass-alongs)
7. Generate ICS
```

### Testing and Evolution

Curators need to:

- **Preview** - see what a rule matches before enabling it
- **Dry-run** - see full composed feed before publishing changes
- **Version** - maybe: track rule changes over time?
- **Debug** - understand why an event is/isn't in their feed

### Open Questions

1. **Rule complexity** - start simple (flat conditions) or support nested boolean logic?
2. **Pass-along enrichments** - when I pass along another curator's pick, do I get their enrichment? Can I override it?
3. **Circular follows** - A follows B follows A. Probably fine (just dedup events), but worth considering.
4. **Rule versioning** - do we need history, or just current state?

---

## Design Principles

### Prefer tried-and-true libraries over bespoke code

When functionality is available in a well-maintained library, use it rather than hand-rolling. Examples:

- **rrule** for RRULE parsing/generation (not string manipulation)
- **ical.js** for ICS parsing if needed
- Standard Supabase client patterns over raw fetch

Benefits: fewer bugs, better edge case handling, community-tested code.

---

## EnrichmentDialog Reactivity

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              PickItem                                    │
│                                                                         │
│   onClick ──────────────────┐                                           │
│                             │                                           │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
                              ▼
                    enrichmentDialog.open({ pick })
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EnrichmentDialog                                  │
│                                                                         │
│   $param.pick ─────────────────────┐                                    │
│        │                           │                                    │
│        │                           ▼                                    │
│        │                    ┌─────────────┐                             │
│        │                    │ DataSource  │                             │
│        │                    │ url={...pick.event_id...}                 │
│        │                    └──────┬──────┘                             │
│        │                           │                                    │
│        │                      onLoaded                                  │
│        │                           │                                    │
│        │                           ▼                                    │
│        │              ┌────────────────────────┐                        │
│        │              │   Component Variables  │                        │
│        │              │   - frequency          │                        │
│        │              │   - selectedDays       │                        │
│        │              │   - urlValue           │                        │
│        │              │   - notesValue         │                        │
│        │              └───────────┬────────────┘                        │
│        │                          │                                     │
│        │         ┌────────────────┼────────────────┐                    │
│        │         │                │                │                    │
│        │         ▼                ▼                ▼                    │
│        │    ┌────────┐      ┌──────────┐    ┌──────────┐               │
│        │    │ Select │      │ Day Btns │    │ TextBoxes│               │
│        │    └───┬────┘      └────┬─────┘    └────┬─────┘               │
│        │        │                │               │                      │
│        │        │ onDidChange    │ onClick       │ onDidChange          │
│        │        │                │               │                      │
│        │        └────────────────┼───────────────┘                      │
│        │                         │                                      │
│        │                         ▼                                      │
│        │              ┌──────────────────┐                              │
│        │              │ Variables Update │◄─────────────────────┐       │
│        │              └────────┬─────────┘                      │       │
│        │                       │                                │       │
│        │                       │ Save button onClick            │       │
│        │                       ▼                                │       │
│        │              ┌─────────────┐                           │       │
│        │              │  APICall    │                           │       │
│        │              │  .execute({ │                           │       │
│        │              │    event_id,│                           │       │
│        │              │    rrule,   │                           │       │
│        │              │    url,     │                           │       │
│        │              │    notes    │                           │       │
│        │              │  })         │                           │       │
│        │              └──────┬──────┘                           │       │
│        │                     │                                  │       │
│        │                onSuccess                               │       │
│        │                     │                                  │       │
│        │                     ▼                                  │       │
│        │              dialog.close()                            │       │
│        │              toast('saved')                            │       │
│        │                                                        │       │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              │ (APICall invalidates caches)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           my-picks edge function                         │
│                                                                         │
│   Fetches picks + enrichments ──► ICS with RRULE                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key reactive triggers

| Trigger | Causes |
|---------|--------|
| `dialog.open({pick})` | `$param.pick` set → DataSource URL changes → fetch fires |
| DataSource `onLoaded` | Variables populated → UI re-renders with values |
| Select `onDidChange` | `frequency` updates → day buttons show/hide |
| Save button click | APICall executes → onSuccess closes dialog |

### Note on AppState for global functions

AppState is designed for reactive state management. However, we currently use it to share functions across components (e.g., `togglePick`, `removePick`, `openEnrichment`) because XMLUI's sandbox doesn't yet expose a cleaner mechanism for global functions. This is a temporary pattern - XMLUI is transitioning to proper global function support in the sandbox. When available, these functions should move out of AppState.
