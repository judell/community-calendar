# Plan: Single ICS Per Source

## Problem

Scrapers generate monthly files (`bohemian_2026_02.ics`, `bohemian_2026_03.ics`, etc.), causing report confusion, feeds.txt bloat, workflow complexity, and meaningless history comparisons.

## Solution

Each scraper produces a single rolling file (`bohemian.ics`) containing all events the source currently publishes.

## Checklist

### Database
- [x] Add `city` column to `events` table
- [x] Add `events_city_idx` index
- [x] Backfill existing events with `city = 'santarosa'`

### Base Classes
- [x] `scrapers/lib/base.py` — remove `--year`/`--month` args, `fetch_events()` takes no params
- [x] `scrapers/lib/rss.py` — `parse_entry(entry)` no longer takes year/month
- [x] `scrapers/lib/cityspark.py` — fetch today + 3 months instead of single month

### Scrapers (refactored to use BaseScraper)
- [x] `scrapers/srcc.py` — tested, 47 events
- [x] `scrapers/cityspark/bohemian.py` — uses CitySparkScraper (automatic)
- [x] `scrapers/cityspark/pressdemocrat.py` — uses CitySparkScraper (automatic)
- [x] `scrapers/wix/cafefrida.py`
- [x] `scrapers/cal_theatre.py`
- [x] `scrapers/copperfields.py`
- [x] `scrapers/occidental_arts.py`
- [x] `scrapers/redwood_cafe.py`
- [x] `scrapers/sebarts.py`
- [x] `scrapers/sonoma_city.py`
- [x] `scrapers/sonoma_county_gov.py`
- [x] `scrapers/sonoma_parks.py`
- [x] `scrapers/svma.py`
- [x] `library_intercept.py`

### Workflow & Config
- [x] Update `generate-calendar.yml` — remove month loops, single call per scraper
- [x] Update `santarosa/feeds.txt` — one entry per source
- [x] Update `sebastopol/feeds.txt`
- [x] Update `cotati/feeds.txt`
- [x] Update `sonoma/feeds.txt`
- [x] Update `bloomington/feeds.txt`
- [x] Remove `Calculate dates` step from workflow (no longer needed)

### Downstream
- [x] Verify `combine_ics.py` works with new filenames (date-suffix regex is a no-op)
- [x] Verify `ics_to_json.py` works (date-suffix regex is a no-op)
- [x] Verify `report.py` works (date-suffix regex is a no-op)
- [x] Update Supabase `load-events` edge function — now loads all cities, includes `city` field

### Cleanup
- [x] Delete old `*_YYYY_MM.ics` files from all city folders (72 files removed)
- [x] Remove `creative_sonoma.py` (not in any workflow)

## History Strategy

Use git history (already preserves daily state of all ICS files). No extra storage needed.

## New CLI

```bash
# Before
python scrapers/srcc.py --year 2026 --month 2 --output santarosa/srcc_2026_02.ics

# After
python scrapers/srcc.py --output santarosa/srcc.ics
```
