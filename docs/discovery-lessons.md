# Discovery Lessons Learned

Real-world lessons from source discovery across cities. These complement the strategies in [AGENTS.md](../AGENTS.md).

## "Curl-and-Done" Sources: No Scraper Needed

Many sources provide ICS feeds that can be added with just a curl command in the workflow — no scraper required. Always check for these before writing a scraper:

### WordPress + The Events Calendar = Free ICS
Sites running WordPress with "The Events Calendar" plugin (by StellarWP/Modern Tribe) have a built-in iCal endpoint:
```
https://example.com/events/?ical=1
```
Look for `PRODID:-//...ECPv6...` in the response to confirm.

**Examples:** The Big Easy Petaluma (30 events), Polly Klaas Community Theater (8 events).

### Public Google Calendar = Free ICS
Some sites embed a public Google Calendar via iframe. Extract the calendar ID from the iframe `src` URL and construct the ICS feed:
```
https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics
```
The calendar ID is URL-encoded in the iframe src (look for `src=` parameter). Decode it to get the `...@group.calendar.google.com` ID.

**Example:** Brooks Note Winery — 142 events from a Google Calendar ICS feed.

### Integration checklist for curl-and-done sources
1. Add curl command to the workflow (`.github/workflows/generate-calendar.yml`)
2. Add SOURCE_NAMES entry in `scripts/combine_ics.py`
3. Add SOURCE_URLS fallback entry in `scripts/combine_ics.py`
4. Add note to `cities/{city}/feeds.txt`
5. Update `cities/{city}/SOURCES_CHECKLIST.md`

## Squarespace = `?format=json`

Squarespace sites expose event data at `?format=json` on any collection page. The JSON includes structured event objects with title, dates, location, excerpt, and URL.

Use `scrapers/lib/squarespace.py` (`SquarespaceScraper` base class) — each scraper is just ~10 lines of config. Note: the collection slug varies per site (e.g., `/events`, `/events-exhibitions`, `/calendar1`).

**Examples:** Mercury Theater, Petaluma Arts Center, Brewsters Beer Garden, Cool Petaluma.

**How to confirm Squarespace:** View page source, look for `<!-- This is Squarespace. -->` or `squarespace.com` in script/link URLs.

**Gotcha:** Some Squarespace sites have an `/events` page that is a regular page (type 10), not an events collection (type 11). The `?format=json` endpoint only returns event data on actual collection pages. If `/events?format=json` returns `"itemCount": 0`, look for the real collection slug in the site navigation.

## Wix Sites: Don't Scrape, Find the Ticketing Platform

Wix sites are heavy JS with cross-origin iframes — scraping them directly is a nightmare. Instead, find what ticketing platform the venue uses and scrape that.

**Example:** Phoenix Theater has a Wix site, but all events are on Eventbrite. Searching `eventbrite.com/d/ca--petaluma/phoenix-theater/` returns clean JSON-LD structured data. See `scrapers/phoenix_theater.py`.

## Eventbrite JSON-LD is Reliable

Eventbrite event pages embed `schema.org/Event` JSON-LD in the HTML. This is more reliable than their search API (which is undocumented and changes). The `scrapers/lib/jsonld.py` base class handles extraction.

## MembershipWorks ICS is Hidden but Standard

Community organizations using MembershipWorks have ICS feeds at:
```
https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}
```
Find the org ID by looking for a "Subscribe" or calendar export button on their events page.

**Example:** Aqus Community — 87 events from a single ICS feed.

## GrowthZone Chambers Have XML APIs

Chamber of Commerce sites on GrowthZone/ChamberMaster have public XML APIs:
```
https://business.{chamber}.us/api/events
```
The `scrapers/growthzone.py` scraper handles this generically.

## Youth Sports Leagues Are Almost Never Viable

Extensively investigated for Petaluma: Little League (BlueSombrero — member-only), AYSO, youth soccer, girls softball, swim teams. Results: member-only platforms, dead domains, or Cloudflare-blocked city rec sites. High school athletics via MaxPreps is the practical ceiling for public school sports data.

## Meetup Feeds Need User-Agent

Meetup ICS feeds sometimes return errors without a User-Agent header:
```bash
# This may fail:
curl -sL "https://www.meetup.com/group/events/ical/"
# This works:
curl -sL -A "Mozilla/5.0" "https://www.meetup.com/group/events/ical/"
```

## Regional Groups Need Geo-Filtering

Regional Meetup groups (e.g., "Sonoma County Outdoors") cover a wide area. Adding them is fine — the `combine_ics.py` geo-filter (`allowed_cities.txt`) drops events outside the target area automatically.

## LiveWhale University Calendars

Universities using LiveWhale have iCal at `{domain}/live/ical/events`. For multi-campus schools, you may need to filter by campus in the scraper.

**Example:** SRJC has 130+ events across campuses; `scrapers/srjc_petaluma.py` filters for Petaluma-specific events (17 events).
