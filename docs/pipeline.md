# Event Pipeline

## Event Sources

### Discovery Philosophy

**We want COMPLETE coverage, not curated coverage.** This means:

- **Long-tail events matter** - A book club with 5 members, a small craft meetup, a neighborhood cleanup - these ARE our target. Don't skip sources just because they seem niche or low-volume.
- **Schools are gold mines** - High schools and colleges have athletics, theater productions, band concerts, art shows, parent nights, and graduations.
- **Churches and community centers** - Special events like concerts, fundraisers, and community dinners are valuable even if weekly services aren't.
- **Youth sports leagues** - Little League, youth soccer, swim teams often have public calendars.
- **If in doubt, add it** - We can always filter later. Missing events is worse than having too many.

### Source Types

**ICS feeds are preferred** when available. Many venues and organizations publish standard iCalendar feeds that we consume directly:
- Luther Burbank Center
- Schulz Museum
- GoLocal Coop
- Sonoma County AA
- City calendars (Google Calendar)
- And more...

**Scraping is a fallback** for sources that don't provide ICS feeds:
- Sonoma County Library (via API interception)
- Cal Theatre
- Copperfield's Books

**Generic/reusable scrapers** work across multiple sites:
- `maxpreps.py` - High school athletics (any school)
- `growthzone.py` - Chamber of Commerce sites

Scrapers are in `scrapers/` and per-city data lives in `cities/<name>/`.

## ICS Combination

**`scripts/combine_ics.py`** - Combines multiple ICS files into a single subscribable feed:

```bash
python scripts/combine_ics.py -i cities/santarosa -o cities/santarosa/combined.ics --name "Santa Rosa Community Calendar"
```

## Deduplication and Source Attribution

The pipeline performs two rounds of deduplication:

1. **Cross-source dedup** — Events with identical title + date from different sources are merged. The non-aggregator version is kept (better URL/description), and `X-SOURCE` headers are merged alphabetically (e.g., "North Bay Bohemian, Press Democrat").

2. **Fuzzy dedup** — `scripts/ics_to_json.py` clusters events within the same timeslot using token-set string similarity (`difflib.SequenceMatcher`, threshold 0.85). Events at different locations are never clustered. Uses union-find to assign a shared `cluster_id` to similar titles — no events are removed; all are kept and tagged for the front-end to group visually.

Source attribution flows through the pipeline as `X-SOURCE` ICS headers, which become the `source` column in the database. Display names are mapped from filenames via `SOURCE_NAMES` in `combine_ics.py`.

## ICS to JSON Conversion

**`scripts/ics_to_json.py`** - Converts ICS to JSON format for Supabase ingestion:

```bash
python scripts/ics_to_json.py cities/santarosa/combined.ics -o cities/santarosa/events.json
```

### Title Clustering

Events within the same timeslot are clustered by title similarity so the UI can visually group them with colored borders. Uses token-set similarity (word overlap) with a threshold of 0.85, plus location awareness — events at different locations are never clustered even if titles match.

Good clusters (score 0.98-1.0): "Tech Help" / "One-On-One Tech Help" at the same library.
Rejected (score < 0.85): "Community Yoga" / "Community Coffee Tasting" — different events sharing a common word. See the `cluster_by_title_similarity` docstring for tuning details.

Output format:
```json
{
  "title": "Event Name",
  "start_time": "2026-02-01T14:00:00",
  "end_time": "2026-02-01T16:00:00",
  "location": "Venue, Address",
  "description": "Event description",
  "url": "https://...",
  "source": "Source Name",
  "source_uid": "unique-id@source.com",
  "cluster_id": 0
}
```

## Event Classification

Events are automatically classified into 10 categories (Music & Concerts, Sports & Fitness, Arts & Culture, etc.) by `scripts/classify_events_anthropic.py`, which runs in CI after each build. The script uses the Anthropic API (Claude Haiku) with batch classification — ~20 events per API call — to categorize all uncategorized future events. It pulls curator overrides from the `category_overrides` table as examples to improve accuracy over time.

Curators can correct misclassified events via the UI. See [curator-guide.md](curator-guide.md#event-categories) for details on categories and the override workflow.

## GitHub Actions Workflow

The workflow in `.github/workflows/generate-calendar.yml` runs automatically.

**Schedule**: Daily at midnight UTC (`0 0 * * *`)

**Cities processed**:
- `santarosa` - Santa Rosa, CA (America/Los_Angeles)
- `bloomington` - Bloomington, IN (America/Indiana/Indianapolis)
- `davis` - Davis, CA (America/Los_Angeles)
- `petaluma` - Petaluma, CA (America/Los_Angeles)
- `toronto` - Toronto, ON (America/Toronto)

**Time range**: Current month + next 2 months

**Per-city workflow**:
1. Run scrapers for sources without ICS feeds
2. Download live ICS feeds from venues that provide them
3. Combine all ICS files into `combined.ics`
4. Commit and push changes

**Manual trigger**: Can also be triggered manually via GitHub Actions UI with options:
- `locations`: Comma-separated list (e.g., `santarosa,bloomington`) or `all`
- `regenerate_only`: Skip scraping, just regenerate from existing ICS files

## Adding a New Scraper

Use the `add_scraper.py` script to integrate a new scraper into the pipeline:

```bash
python scripts/add_scraper.py myscraper santarosa "My Source Name"

# Options:
#   --test      Run the scraper first to verify it works
#   --dry-run   Preview changes without applying them
```

This automatically verifies the scraper exists, adds it to the GitHub Actions workflow, and adds the source name to `scripts/combine_ics.py`. **All three steps are required** — if you skip the workflow or source name, events won't appear in the calendar.

## Manual Pipeline Run

```bash
# 1. Run scrapers (produces individual ICS files)
# (varies by scraper)

# 2. Combine ICS files
python scripts/combine_ics.py -i cities/santarosa -o cities/santarosa/combined.ics

# 3. Convert to JSON
python scripts/ics_to_json.py cities/santarosa/combined.ics -o cities/santarosa/events.json

# 4. Commit and push
git add cities/santarosa/events.json cities/santarosa/combined.ics
git commit -m "Update events"
git push

# 5. Trigger Supabase ingestion
curl -L -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer <LEGACY_ANON_KEY>'
```
