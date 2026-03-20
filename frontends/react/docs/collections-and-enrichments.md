# Collections and Enrichments

## Overview

Curators (authenticated users) can organize events into **collections** and add **enrichments** (metadata overrides) to events. Collections are shareable via public feed URLs. Both features are city-scoped.

---

## Collections

A collection is a named group of events belonging to a curator, scoped to a city. Collections come in two types: **manual** and **auto**.

### Manual Collections

A manual collection contains events explicitly added by the curator.

- Events are stored in the `collection_events` join table.
- Curators add events via the bookmark button (when a target collection is selected) or from the picks page.
- Removing an event deletes the `collection_events` row.

### Auto Collections

An auto collection defines filter **rules** and automatically includes all matching events.

- Rules are stored as JSON on the collection row: `{ "sources": [...], "categories": [...] }`.
- Both arrays are optional. An event matches if its source is in the sources list AND its category is in the categories list. Omitted arrays impose no filter on that dimension.
- Only future events (start_time >= now) are included.

**Exclusions:** When a curator removes an event from an auto collection, its `source_uid` is recorded in the `auto_collection_exclusions` table. Exclusions use `source_uid` (not `event_id`) so they survive the nightly batch job that deletes and recreates event rows. Excluded events can be restored from the collection manager.

**Manual additions:** Curators can also manually add events to an auto collection (stored in `collection_events`). These appear alongside rule-matched events and aren't affected by the rule filters.

### Database Tables

**collections**
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key |
| user_id | uuid | Owner (FK to auth.users) |
| city | text | City scope |
| name | text | Display name |
| type | text | `'manual'` (default) or `'auto'` |
| rules | jsonb | Auto-collection filter rules |
| card_style | text | Card variant for feed display (default: `'accent'`) |
| description | text | Optional description |
| created_at | timestamptz | |

**collection_events** (manual membership)
| Column | Type | Notes |
|--------|------|-------|
| id | bigint | Primary key |
| collection_id | uuid | FK to collections |
| event_id | bigint | FK to events |
| sort_order | int | Display order |
| added_at | timestamptz | |

Unique constraint on (collection_id, event_id).

**auto_collection_exclusions**
| Column | Type | Notes |
|--------|------|-------|
| id | bigint | Primary key |
| collection_id | uuid | FK to collections (cascade delete) |
| source_uid | text | Stable identifier for the event across batch rebuilds |
| excluded_at | timestamptz | |

Unique constraint on (collection_id, source_uid).

### RLS Policies

- All collection tables are publicly readable (SELECT).
- Only the collection owner can INSERT, UPDATE, or DELETE.
- For `collection_events` and `auto_collection_exclusions`, ownership is verified via a join to `collections.user_id`.

### Feed Pages

Any collection can be viewed as a public feed at `?feed={collection_id}`. The feed page:

- Displays the collection name, description, event count, and (for auto collections) a summary of the rules.
- Applies the collection owner's enrichments to all displayed events.
- If the viewer is the collection owner, remove buttons (X) appear on each card. For auto collections, clicking X creates an exclusion. For manual collections, it deletes the membership row.

---

## Enrichments

An enrichment is a curator's metadata override for a single event. Each (event_id, curator_id) pair can have one enrichment.

### Enrichment Fields

| Field | Purpose |
|-------|---------|
| title | Override the event title |
| start_time | Override start time |
| end_time | Override or add end time |
| location | Override location |
| description | Override description |
| url | Add or override the event link |
| notes | Internal curator notes (not shown publicly) |
| rrule | Recurrence rule (e.g., `FREQ=WEEKLY;BYDAY=MO,WE`) |
| curator_name | Display name for source attribution |
| city | Copied from event at creation time |

Enrichments also store their own `title`, `start_time`, and `city` so they remain meaningful if the original event row is deleted by a batch rebuild.

### How Enrichments Are Applied

The `applyEnrichments(events, enrichments)` helper merges enrichment fields into event objects. For each event, if an enrichment exists, its non-null fields override the corresponding event fields. This happens client-side when loading:

- **Picks page:** The curator's own enrichments are applied to their picked events.
- **Feed pages:** The collection owner's enrichments are applied to all events in the feed.

### Category Overrides

Category overrides are a separate mechanism stored in the `category_overrides` table. When a curator sets a category override:

- The original category is preserved in `original_category`.
- A database trigger updates the event's `category` column directly, so the override is visible to all users.
- The EnrichmentEditor saves category overrides alongside enrichment data when the curator changes the category.

### Database Table

**event_enrichments**
| Column | Type | Notes |
|--------|------|-------|
| id | bigint | Primary key |
| event_id | bigint | FK to events (nullable) |
| curator_id | uuid | FK to auth.users |
| title | text | |
| start_time | timestamptz | |
| end_time | timestamptz | |
| location | text | |
| description | text | |
| url | text | |
| notes | text | |
| rrule | text | |
| city | text | |
| curator_name | text | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Unique constraint on (event_id, curator_id).

RLS: publicly readable; only the curator (curator_id = auth.uid()) can insert, update, or delete.

---

## Picks

A pick is a bookmark — a curator saving an event for later. Picks are stored in the `picks` table with a unique constraint on (user_id, event_id).

### Relationship to Collections and Enrichments

- Picking an event is independent of adding it to a collection.
- When a curator uses the target collection bar, clicking the bookmark on an unpicked event will both pick it and add it to the target collection.
- When adding a pick via the EnrichmentEditor (mode='pick'), an enrichment is also created if the curator sets recurrence.
- Removing a pick also deletes the curator's enrichment for that event.

### Target Collection

The target collection bar (on the main city page) lets curators select an active collection. While a target is set:

- The bookmark icon on each card reflects whether the event is in that collection (not just whether it's picked).
- Clicking an unfilled bookmark adds the event to the target collection (and picks it if not already picked).
- Clicking a filled bookmark removes the event from the target collection.

---

## Key Files

| File | Purpose |
|------|---------|
| `hooks/useCollections.js` | Curator's collection CRUD, membership map, event fetching |
| `hooks/useCollection.js` | Public feed: fetch a single collection + its events |
| `hooks/useTargetCollection.jsx` | Target collection context for quick-add from main page |
| `hooks/useFeedContext.jsx` | Feed context providing remove capability to cards |
| `hooks/usePicks.jsx` | Picks context with external store for efficient rendering |
| `components/CollectionManager.jsx` | Collection list, create/rename/delete, expanded event view |
| `components/FeedView.jsx` | Public feed page rendering |
| `components/EnrichmentEditor.jsx` | Modal for editing enrichment fields + category |
| `components/cards/shared.jsx` | BookmarkButton, CuratorTools, ActionBar |
| `supabase/ddl/07_collections.sql` | Collections + collection_events schema |
| `supabase/ddl/06_event_enrichments.sql` | Enrichments schema |
| `supabase/ddl/15_alter_collections_auto.sql` | Auto-collection columns (type, rules) |
| `supabase/ddl/16_auto_collection_exclusions.sql` | Exclusions table |
| `supabase/ddl/11_category_overrides.sql` | Category overrides schema + trigger |
