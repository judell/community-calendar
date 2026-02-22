# Source Attribution Links

## How It Works

Each event card displays a "Source:" line showing where the event came from. When an event appears in multiple sources (e.g., a venue's own calendar and an aggregator like the Bohemian), all contributing sources are listed. Each source name links to that source's page for the event when a URL is available.

### Data Flow

**`scripts/combine_ics.py`** — Two places where `X-SOURCE-URLS` gets populated:

1. **At extraction time**: Every event gets an `X-SOURCE-URLS` JSON dict mapping its source name to its event URL:
```python
evt_url = extract_field(event_content, 'URL')
if evt_url and 'X-SOURCE-URLS' not in event_content:
    event_content = f'X-SOURCE-URLS:{json.dumps({source_name: evt_url})}\r\n{event_content}'
```

2. **During cross-source dedup**: When duplicates are merged, source URLs from all copies are combined into a single dict:
```python
source_urls = {}
for e in group:
    src = extract_field(e['content'], 'X-SOURCE')
    evt_url = extract_field(e['content'], 'URL')
    if src and evt_url:
        source_urls[src.strip()] = evt_url
# Stored as: X-SOURCE-URLS:{"Bohemian":"https://...","GoLocal":"https://..."}
```

**`scripts/ics_to_json.py`** — Extracts `X-SOURCE-URLS` as a parsed JSON dict:
```python
source_urls_raw = extract_field(event_content, 'X-SOURCE-URLS')
source_urls = json.loads(source_urls_raw) if source_urls_raw else {}
```

**Database** — Stored as `jsonb`:
```sql
source_urls jsonb,  -- per-source URLs for aggregator attribution links
```

**`helpers.js`** — `formatSourceLinks(source, sourceUrls, hiddenSources)` renders the attribution line:
- Splits comma-separated source names
- Filters out hidden sources (from user settings), but keeps all if all would be removed
- Wraps each source name in a markdown link if `sourceUrls` has an entry for it
- Returns `Source: [Bohemian](https://...), [GoLocal](https://...)`

**`components/EventCard.xmlui`** — Renders the formatted source line using a Markdown component, passing `hiddenSources` from `userSettingsData`.

### Aggregator Attribution Principle

When an event was discovered via an aggregator, we link the aggregator's name to the aggregator's page for that event — not just to the aggregator's homepage. A reader who clicks through to the Bohemian may discover related events, editorial coverage, or other context. See [curator-guide.md - About Aggregators](curator-guide.md#about-aggregators).

### Graceful Degradation

- Events with `source_urls` entries: source names are clickable links
- Events without `source_urls`: source names display as plain text
- Single-source events always show their source, even if hidden by user settings
