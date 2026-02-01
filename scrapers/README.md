# Event Scrapers

Python scrapers for extracting events from various Sonoma County venues that don't provide standard iCal feeds.

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
