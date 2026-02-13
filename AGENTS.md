# Agent Strategies for Calendar Source Discovery

## Discovery Philosophy

**We want COMPLETE coverage, not curated coverage.** This means:

1. **Long-tail events matter** - A book club with 5 members, a small craft meetup, a neighborhood cleanup - these ARE our target. Don't skip sources just because they seem niche or low-volume.

2. **Schools are gold mines** - High schools and colleges have athletic events, theater, band concerts, art shows, parent nights, graduation ceremonies.

3. **Churches and community centers** - Weekly services may not be interesting, but special events (concerts, fundraisers, community dinners) are.

4. **Youth sports leagues** - Little League, youth soccer, swim teams often have public calendars.

5. **If in doubt, add it** - We can always filter later. Missing events is worse than having too many.

## Quick Reference: Adding a New City

1. **Create city directory** under `cities/` with `feeds.txt` and `SOURCES_CHECKLIST.md`
2. **Set up geo-filtering** - create `allowed_cities.txt` with center, radius, and allowed cities:
   ```
   # center: 38.5449, -121.7405
   # radius: 30
   # state: CA
   Davis
   Woodland
   Sacramento
   ```
   Then run: `python scripts/geocode_cities.py --city {cityname}`
3. **Run Meetup discovery** - see [docs/curator-guide.md](docs/curator-guide.md)
4. **Run Eventbrite scraper** - `python scrapers/eventbrite_scraper.py --location {state}--{city} --months 2`
5. **Update the GitHub Actions workflow** (`.github/workflows/generate-calendar.yml`):
   - Add curl commands for Meetup ICS feeds
   - Add Eventbrite scraper command
   - Add combine_ics.py step
6. **Update `combine_ics.py`** - add SOURCE_NAMES entries for new Meetup groups
7. **Add city to UI** - TWO places must be updated:
   - `index.html`: add entry to `cityNames` map (e.g., `petaluma: 'Petaluma'`)
   - `Main.xmlui`: add a Button in the city picker VStack (search for "Choose your city")
8. **Add city to load-events function** - add URL entry to `EVENTS_URLS` in `supabase/functions/load-events/index.ts`, then redeploy the edge function
9. **Update SOURCES_CHECKLIST.md** - document findings, track pending sources
10. **Commit and push** - workflow runs daily or trigger manually

## App Architecture

The XMLUI app lives at the repo root and serves all cities from a single set of files:

- **`index.html`** — Entry point. Reads `?city=` URL param to set `window.cityFilter` and `window.cityName`. No param shows the city picker.
- **`Main.xmlui`** — App layout. Shows city picker when `!window.cityFilter`, calendar UI when a city is selected. Queries Supabase filtered by `window.cityFilter`.
- **`components/`** — Shared XMLUI components (EventCard, PickItem, etc.)
- **`Globals.xs`** — Shared state (pickEvent, picksData, enrichmentsData, refreshCounter) and functions (togglePick, removePick)
- **`helpers.js`**, **`config.json`** — Pure helper functions and app configuration

**URLs:** `index.html?city=santarosa`, `index.html?city=davis`, `index.html?city=bloomington`, etc.

**Do not duplicate app files into city directories.** City directories (`cities/<name>/`) hold only data (ICS files, events.json) and city-specific docs.

**Edge function gotcha:** Redeploying any edge function via the Supabase MCP tool resets "Require JWT" to ON. The workflow calls `load-events` with the anon key, so after redeploying you must manually turn off "Require JWT" in the Supabase dashboard.

**DDL files (`supabase/ddl/`)** document the live database state — they are not migration scripts.

### SOURCES_CHECKLIST.md

Each city should have a `SOURCES_CHECKLIST.md` to track ongoing discovery:
- **Currently Implemented** - sources already in the workflow
- **Meetup Groups** - results of Meetup discovery with dates
- **Eventbrite** - scraper results and key venues found
- **Potential Additional Sources** - venues/orgs to investigate
- **Non-Starters** - sources that were checked but don't work (and why)

---

## Quick Reference: Adding a New Scraper

When creating a new scraper for an existing city, **all three steps are required**:

1. **Create the scraper** in `scrapers/` directory
2. **Add to workflow** (`.github/workflows/generate-calendar.yml`)
3. **Add source name** (`scripts/combine_ics.py`)

### Recommended: Use the add_scraper script

```bash
python scripts/add_scraper.py myscraper santarosa "My Source Name"
python scripts/add_scraper.py myscraper santarosa "My Source Name" --test      # test first
python scripts/add_scraper.py myscraper santarosa "My Source Name" --dry-run   # preview
```

**If you skip steps 2-3, the scraper won't run in CI and events won't appear!**

---

## Reusable Scrapers

### MaxPreps (`scrapers/maxpreps.py`) - High School Athletics
```bash
python scrapers/maxpreps.py --school petaluma-trojans -o events.ics
python scrapers/maxpreps.py --school casa-grande-gauchos -o events.ics
python scrapers/maxpreps.py --url "https://www.maxpreps.com/ca/davis/davis-blue-devils/events/" --name "Davis High" -o events.ics
```

### GrowthZone (`scrapers/growthzone.py`) - Chamber of Commerce
```bash
python scrapers/growthzone.py --site petalumachamber -o events.ics
```

### Eventbrite (`scrapers/eventbrite_scraper.py`)
```bash
python scrapers/eventbrite_scraper.py --location ca--petaluma --months 2 > events.ics
```

### Library Intercept (`scripts/library_intercept.py`)
```bash
python scripts/library_intercept.py --location petaluma -o library.ics
```

### Elfsight Calendar (`scrapers/lib/elfsight.py`)
For sites using Elfsight Event Calendar widget. See `scrapers/sportsbasement.py` for example.

---

## Platform-Specific Techniques

| Platform | Feed Pattern |
|----------|--------------|
| **MembershipWorks** | `https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}` |
| **Tockify** | `https://tockify.com/api/feeds/ics/{CALENDAR_ID}` |
| **LiveWhale** | `https://{domain}/live/ical/events` |
| **Localist** | `https://{domain}/api/2/events` |
| **WordPress Tribe** | `https://example.com/events/?ical=1` |

### SeeTickets Widgets
HTML classes: `.title a`, `.date`, `.see-showtime`, `.see-doortime`, `.genre`, `.ages`, `.price`
Example: `scrapers/mystic_theatre.py`

### Wix Events
Complex - cross-origin iframes from `geteventviewer.com`. Often easier to check if venue is on Eventbrite.

---

## Source Discovery

**See [docs/curator-guide.md](docs/curator-guide.md) for the complete discovery workflow including:**
- Platform searches (Meetup, Tockify, Localist)
- Testing discovered feeds
- DuckDuckGo search templates
- Meetup discovery process

---

## Pipeline Validation

### Validation Script
```bash
python scripts/validate_pipeline.py --cities santarosa,bloomington,davis
python scripts/validate_pipeline.py --cities santarosa --strict
```

### Common Silent Failure Causes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| events.json not updated | Whitespace in city name | `xargs` trim in workflow |
| Scraper produces 0 events | Site changed or blocked | Check logs, update scraper |
| Source missing from events.json | Scraper not in workflow | Run `add_scraper.py` |

---

## Known Platform Limitations

| Platform | Issue |
|----------|-------|
| **Planning Center/Church Center** | No public API; requires login |
| **Simpleview CMS** | Tourism sites; no public events API |
| **Cloudflare-protected sites** | Challenge pages block scrapers |
| **Facebook Events** | No public API since 2018 |
