# Feature: Link Source Names to Authoritative URLs

## Goal
Update the calendar display so source names are clickable links to the source's events page.

## Implementation Plan

### 1. Infrastructure Changes

**`scripts/combine_ics.py`**: Add `X-SOURCE-URL` header to events using `SOURCE_URLS` dict
```python
# In extract_events(), after adding X-SOURCE-ID:
if fallback_url and 'X-SOURCE-URL' not in event_content:
    event_content = f'X-SOURCE-URL:{fallback_url}\r\n{event_content}'
```

**`scripts/ics_to_json.py`**: Extract `X-SOURCE-URL` as `source_url` field
```python
source_url = extract_field(event_content, 'X-SOURCE-URL')
# Add to event dict:
'source_url': source_url or '',
```

**`components/EventCard.xmlui`**: Wrap source name in Link when `source_url` exists
```xml
<HStack when="{$props.event.source_url}" gap="$space-0">
  <Text fontSize="$fontSize-xs" fontStyle="italic" color="$color-text-tertiary" value="Source: " />
  <Link to="{$props.event.source_url}" target="_blank">
    <Text fontSize="$fontSize-xs" fontStyle="italic" color="$color-text-tertiary" value="{$props.event.source}" />
  </Link>
</HStack>
<Text
  when="{!$props.event.source_url}"
  fontSize="$fontSize-xs"
  fontStyle="italic"
  color="$color-text-tertiary"
  breakMode="word"
  value="{'Source: ' + $props.event.source}"
/>
```

**Database**: Add `source_url` column
```sql
ALTER TABLE events ADD COLUMN IF NOT EXISTS source_url text;
```

### 2. Add Missing URLs to SOURCE_URLS

The `SOURCE_URLS` dict in `combine_ics.py` needs entries for all sources. Currently ~150 are missing.

**To see missing sources:**
```bash
python3 -c "
from scripts.combine_ics import SOURCE_NAMES, SOURCE_URLS
missing = set(SOURCE_NAMES.keys()) - set(SOURCE_URLS.keys())
for s in sorted(missing):
    print(f'{s}: {SOURCE_NAMES[s]}')
"
```

**Missing source categories:**

1. **Aggregators** (high priority):
   - `bohemian` → `https://bohemian.com/events-calendar/`
   - `pressdemocrat` → `https://www.pressdemocrat.com/events/`

2. **Meetup groups** (~100 groups) - URL pattern: `https://www.meetup.com/{slug}/`
   - Extract slugs: `grep -oE 'meetup\.com/[^/]+' .github/workflows/generate-calendar.yml`

3. **Venues/Organizations** (~50 sources):
   - Santa Rosa: barrel_proof, cafefrida, srcc, museumsc, mystic_theatre, sebarts, etc.
   - Bloomington: bgc_bloomington, bluebird, buskirk_chumley, comedy_attic, etc.
   - Raleigh-Durham: catscradle, motorco, carolina_theatre, etc.
   - MaxPreps schools: pattern `https://www.maxpreps.com/ca/{city}/{school-mascot}/`

### 3. Deployment Steps

1. Run migration on Supabase
2. Deploy code changes
3. Regenerate calendar data (GitHub Actions workflow)
4. Reload events to populate `source_url` in database

## Notes

- `SOURCE_URLS` currently serves as fallback URL for events without their own URL
- Same dict works for source home page links
- Sources without entries will show plain text (graceful degradation)
