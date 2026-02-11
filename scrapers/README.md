# Event Scrapers

Python scrapers for extracting events from various venues that don't provide standard iCal feeds.

## Scraper Libraries (`lib/`)

Reusable base classes for common calendar platforms:

### `lib/elfsight.py` - Elfsight Event Calendar
For sites using the [Elfsight Event Calendar](https://elfsight.com/event-calendar-widget/) widget.

```python
from scrapers.lib.elfsight import ElfsightCalendarScraper

class MySiteScraper(ElfsightCalendarScraper):
    name = "My Site Events"
    domain = "mysite.com"
    widget_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # From page source
    source_page = "https://mysite.com/events"

if __name__ == '__main__':
    MySiteScraper.main()
```

To find the widget_id, inspect the page source and look for `elfsight-app-` or `eapps-event-calendar-` followed by a UUID.

CLI options: `--location`, `--type`, `--list-locations`, `--list-types`, `--months`

### `lib/cityspark.py` - CitySpark Calendars
For sites using CitySpark (e.g., Bohemian, Press Democrat).

### `lib/base.py` - Base Scraper
Abstract base class for all scrapers with common ICS generation.

## Scrapers

### sonoma_parks.py
Sonoma County Regional Parks calendar
- URL: https://parks.sonomacounty.ca.gov/play/calendar
- Events: Hikes, nature programs, volunteer workdays
- Method: HTML scraping (server-rendered calendar)

### redwood_cafe.py  
Redwood Cafe Cotati live music
- URL: https://redwoodcafecotati.com/events/
- Events: Live music performances
- Method: WordPress My Calendar plugin HTML scraping

### cal_theatre.py
California Theatre Santa Rosa
- URL: https://www.caltheatre.com/calendar  
- Events: Concerts, theater, comedy shows
- Method: Wix calendar widget HTML scraping
- Note: Works with static fetch; --use-selenium option available for JS rendering

### copperfields.py
Copperfield's Books (multiple locations)
- URL: https://copperfieldsbooks.com/upcoming-events
- Events: Author readings, book signings, kids events
- Locations: Petaluma, Sebastopol, Healdsburg, San Rafael, Napa, Calistoga, Montgomery Village
- Method: Drupal HTML scraping

### sportsbasement.py
Sports Basement Community Events (Bay Area chain)
- URL: https://shop.sportsbasement.com/pages/calendar
- Events: Run clubs, bike rides, fitness classes, ski events, community events
- Locations: Santa Rosa, Novato, Berkeley, Presidio, and 13 other Bay Area stores
- Method: Elfsight calendar widget API (uses `lib/elfsight.py`)

```bash
# List locations
python sportsbasement.py --list-locations

# Santa Rosa events
python sportsbasement.py --location "Santa Rosa" -o sportsbasement.ics

# Filter by event type
python sportsbasement.py --location "Santa Rosa" --type "Run Events"
```

## Usage

Each scraper accepts `--year` and `--month` arguments and outputs an ICS file:

```bash
python3 sonoma_parks.py --year 2026 --month 2 --output sonoma_parks_2026_02.ics
python3 redwood_cafe.py --year 2026 --month 2 --output redwood_cafe_2026_02.ics
python3 cal_theatre.py --year 2026 --month 2 --output cal_theatre_2026_02.ics
python3 copperfields.py --year 2026 --month 2 --output copperfields_2026_02.ics
```

## Dependencies

- requests
- beautifulsoup4
- icalendar

Optional for cal_theatre.py with --use-selenium:
- selenium
- Chrome/Chromium browser

## Output Locations

- santarosa/: sonoma_parks, cal_theatre, copperfields
- cotati/: redwood_cafe
- sebastopol/: sebarts (existing), occidental_arts (existing)

## Notes

- Events for future months may be empty if the venue hasn't posted them yet
- Most venues post events 1-2 months in advance
- SebArts (sebastopol/sebarts.py) was already implemented in the project

## Adding a New Scraper to the Pipeline

Creating a scraper is not enough - you must also integrate it into the build:

1. **Create & test the scraper locally**
   ```bash
   python scrapers/myscraper.py --output /tmp/test.ics
   grep -c "BEGIN:VEVENT" /tmp/test.ics  # Verify events
   ```

2. **Add to GitHub workflow** (`.github/workflows/generate-calendar.yml`):
   - Find the "Scrape {City} sources" step for your city
   - Add a line: `python scrapers/myscraper.py --output cities/{city}/myscraper.ics || true`

3. **Add source name mapping** (`scripts/combine_ics.py`):
   - Add to `SOURCE_NAMES` dict: `'myscraper': 'Human Readable Name',`

**All three steps are required or events won't appear in the calendar!**
