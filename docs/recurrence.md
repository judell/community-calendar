# Recurrence and Enrichment

Curators (signed-in users) can attach recurrence rules to events, making them visible to all users as recurring virtual events.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Curator clicks checkbox on a feed event (e.g., "Circus jam")   │
│                         ↓                                          │
│  2. PickEditor modal opens, pre-populated from the event           │
│     - Title, date, time, location, description                     │
│     - Recurrence section (auto-expands if text says "every Wed")   │
│                         ↓                                          │
│  3. Curator sets frequency (Weekly/Monthly) + days                 │
│                         ↓                                          │
│  4. "Add to My Picks" creates:                                     │
│     - A pick (picks table) — personal                              │
│     - An enrichment (event_enrichments table) — public             │
│       with RRULE, title, start_time, city, curator_name            │
│                         ↓                                          │
│  5. Client-side RRULE expansion generates virtual events           │
│     visible to ALL users in the main feed                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Recurrence Detection

`detectRecurrence()` in `helpers.js` scans event text for recurrence language. It accepts multiple arguments (description, title) and returns the first match:

- `"every Wednesday"` → `{ frequency: 'WEEKLY', days: ['WE'] }`
- `"weekly"` / `"every week"` → `{ frequency: 'WEEKLY', days: [] }`
- `"1st Tuesday of every month"` → `{ frequency: 'MONTHLY', ordinal: 1, monthDay: 'TU' }`
- `"monthly"` → `{ frequency: 'MONTHLY' }`

When the PickEditor opens, if recurrence is detected, the recurrence section auto-expands with frequency and days pre-selected.

## Self-Standing Enrichments

The `event_enrichments` table stores enrichment data that can survive independently of the original event:

| Column | Purpose |
|--------|---------|
| `event_id` | Links to original event (nullable — enrichment survives if event is deleted) |
| `curator_id` | User who created the enrichment |
| `rrule` | RFC 5545 recurrence rule (e.g., `FREQ=WEEKLY;BYDAY=WE`) |
| `title`, `start_time`, `city` | Copied from event at enrichment time |
| `curator_name` | GitHub username for source attribution |

## Client-Side RRULE Expansion

`expandEnrichments()` in `helpers.js` uses the [rrule.js](https://github.com/jakubroztocil/rrule) library to generate virtual events:

1. For each enrichment with an `rrule`, parse it via `rrule.RRule.fromString()`
2. Set `dtstart` from the enrichment's `start_time`
3. Call `rule.between(fromDate, toDate)` to get occurrences in the visible date range
4. Create virtual event objects with `source: 'Picks: ' + curator_name`

## Merging with Feed Events

Virtual events from enrichments merge with feed events via `dedupeEvents()`:

- **Key**: `title.toLowerCase() + start_time` — same event from different sources merges into one card
- **Source attribution**: Sources are joined with `, ` — e.g., `"Bohemian, Picks: Jon"`
- **RRULE carry-through**: When an enrichment event merges with a feed event, the RRULE is preserved on the merged result so ICS downloads include recurrence

Example scenarios:
- "Circus jam" from Bohemian feed + enrichment on same date → source shows `"Bohemian, Picks: Jon"`
- "Circus jam" from enrichment only (no feed event that week) → source shows `"Picks: Jon"`
- User downloads ICS for a merged event → RRULE is included in the VEVENT

## Pinning in My Picks

Recurring picks stay pinned in the "my picks" view regardless of whether the original event date has passed. The `PickItem` component uses `getNextOccurrence()` to display the next upcoming occurrence date instead of the original (possibly past) date.

## Pick/Unpick Flow

- **Picking**: Click checkbox → PickEditor modal opens → confirm with optional recurrence → pick + enrichment created
- **Unpicking**: Click checkbox on already-picked event → one-click remove (no modal), deletes both the pick and any associated enrichment
- **DataSource refresh**: Both paths increment a `refreshCounter` var in `Main.xmlui.xs`, which triggers a `ChangeListener` in `Main.xmlui` to call `refetch()` on the events, picks, and enrichments DataSources

## Three Capture Paths, One Editor

All paths converge on the same `PickEditor` component:

| Path | Entry point | Pre-population |
|------|-------------|----------------|
| **Feed pick** | Checkbox on EventCard | Event data from feed |
| **Photo capture** | Camera icon → CaptureDialog | Claude API extraction from poster image |
| **Audio capture** | Play icon → AudioCaptureDialog | Whisper transcription → Claude extraction from audio |

## ICS Download

The `AddToCalendar` component generates a downloadable `.ics` file for any event. If the event has an RRULE (from enrichment), it's included in the VEVENT so calendar apps that support recurrence (Google Calendar, Apple Calendar, Outlook) will create recurring entries.
