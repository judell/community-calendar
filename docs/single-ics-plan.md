# Plan: Single ICS Per Source

## Current State (Legacy)

Scrapers generate monthly files:
```
santarosa/bohemian_2026_02.ics
santarosa/bohemian_2026_03.ics
santarosa/bohemian_2026_04.ics
```

Problems:
1. **Report confusion**: Report tracks each monthly file separately, flags "0 events" for future months that legitimately have no data yet
2. **feeds.txt bloat**: Must list each month's file explicitly
3. **Workflow complexity**: Must loop over months when scraping
4. **History ambiguity**: Comparing different months' files isn't meaningful

## Proposed State

Each scraper produces a single rolling file:
```
santarosa/bohemian.ics
santarosa/cafefrida.ics
santarosa/copperfields.ics
```

Contains all events the source currently publishes (typically 1-3 months ahead).

## Migration Steps

### 1. Update Scrapers

Change scraper CLI from:
```bash
python scraper.py --year 2026 --month 2 --output santarosa/source_2026_02.ics
```

To:
```bash
python scraper.py --output santarosa/source.ics
```

Scrapers fetch ALL available events from source, not filtered by month.

**Files to modify:**
- `scrapers/cityspark/bohemian.py`
- `scrapers/cityspark/pressdemocrat.py`
- `scrapers/wix/cafefrida.py`
- `scrapers/cal_theatre.py`
- `scrapers/copperfields.py`
- `scrapers/creative_sonoma.py`
- `scrapers/occidental_arts.py`
- `scrapers/redwood_cafe.py`
- `scrapers/sebarts.py`
- `scrapers/sonoma_city.py`
- `scrapers/sonoma_county_gov.py`
- `scrapers/sonoma_parks.py`
- `scrapers/srcc.py`
- `scrapers/svma.py`
- `library_intercept.py`

### 2. Update feeds.txt Files

From:
```
santarosa/bohemian_2026_02.ics
santarosa/bohemian_2026_03.ics
santarosa/bohemian_2026_04.ics
```

To:
```
santarosa/bohemian.ics
```

### 3. Update GitHub Workflow

Simplify from month loops:
```yaml
for period in "this" "next" "next2"; do
  python scraper.py --year $Y --month $M --output source_${Y}_${M}.ics
done
```

To single call:
```yaml
python scraper.py --output santarosa/source.ics
```

### 4. Update Report

`report.py` changes:
- Track single file per source
- History becomes meaningful: same file, different days
- Anomaly detection simplified: compare today vs yesterday for same file

### 5. Update cal.py

May need changes if it expects monthly files. Review `--generate` logic.

## History & Backup Strategy

### Option A: Git History (Recommended)

Git already preserves history. Each daily commit captures the state of all ICS files.

To see historical data:
```bash
git log --oneline santarosa/bohemian.ics
git show HEAD~7:santarosa/bohemian.ics | grep -c "BEGIN:VEVENT"
```

Pros:
- No extra storage
- Already implemented
- Can diff any two points in time

Cons:
- Repo size grows (but ICS compresses well)
- Requires git commands to access history

### Option B: Daily Snapshots

Keep dated copies:
```
santarosa/history/bohemian_2026-02-07.ics
santarosa/history/bohemian_2026-02-08.ics
```

Pros:
- Easy to access without git
- Can serve historical files directly

Cons:
- Storage grows linearly
- Must implement rotation/cleanup

### Option C: Report JSON Only

Don't keep full ICS history. `report.json` already tracks event counts per day.

Pros:
- Minimal storage
- Sufficient for anomaly detection

Cons:
- Can't recover actual events from history
- Can't debug what changed

### Recommendation

**Use Option A (Git History)** for full ICS files.

**Enhance report.json** to store slightly more detail:
```json
{
  "feeds": {
    "bohemian": {
      "history": [
        {"date": "2026-02-07", "count": 912, "earliest": "2026-02-07", "latest": "2026-04-15"},
        {"date": "2026-02-08", "count": 920, "earliest": "2026-02-08", "latest": "2026-04-20"}
      ]
    }
  }
}
```

Adding `earliest` and `latest` event dates helps distinguish:
- Source stopped publishing (count drops, date range shrinks)
- Normal rolloff (old events removed, new ones added)

## Rollout Plan

1. **Phase 1**: Update one scraper (e.g., `srcc.py`) as pilot
2. **Phase 2**: Update report.py to handle both old and new formats
3. **Phase 3**: Migrate remaining scrapers one by one
4. **Phase 4**: Clean up old monthly files
5. **Phase 5**: Simplify workflow YAML

## Backwards Compatibility

During migration:
- `report.py` should detect file format from name (has `_YYYY_MM` = legacy)
- `feeds.txt` can mix old and new formats
- `cal.py` should work with either (it just reads ICS files)

## Testing

Before migration, verify:
1. Scraper produces valid ICS with all events
2. Event count matches sum of old monthly files
3. Report correctly tracks new single file
4. Combined calendar (`combined.ics`) still works
5. Supabase load still works
