# Discovery Lessons Learned

Real-world lessons from source discovery across cities. These complement the strategies in [AGENTS.md](../AGENTS.md).

## Table of Contents

- ["Curl-and-Done" Sources: No Scraper Needed](#curl-and-done-sources-no-scraper-needed)
  - [WordPress + The Events Calendar = Free ICS](#wordpress--the-events-calendar--free-ics)
  - [WordPress + Modern Events Calendar (MEC) = Free ICS](#wordpress--modern-events-calendar-mec--free-ics)
  - [Public Google Calendar = Free ICS](#public-google-calendar--free-ics)
  - [Integration checklist for curl-and-done sources](#integration-checklist-for-curl-and-done-sources)
- [Squarespace = ?format=json](#squarespace--formatjson)
- [Wix Sites: Don't Scrape, Find the Ticketing Platform](#wix-sites-dont-scrape-find-the-ticketing-platform)
- [Eventbrite JSON-LD is Reliable](#eventbrite-json-ld-is-reliable)
- [CKAN Open Data Portals Have Government Meeting & Event Data](#ckan-open-data-portals-have-government-meeting--event-data)
- [Bibliocommons Library Platforms Have a Reusable API Pattern](#bibliocommons-library-platforms-have-a-reusable-api-pattern)
- [MembershipWorks ICS is Hidden but Standard](#membershipworks-ics-is-hidden-but-standard)
- [GrowthZone Chambers Have XML APIs](#growthzone-chambers-have-xml-apis)
- [Youth Sports Leagues Are Almost Never Viable](#youth-sports-leagues-are-almost-never-viable)
- [Probe WordPress Sites Directly with ?ical=1](#probe-wordpress-sites-directly-with-ical1)
- [Neighbourhood Associations and Business Districts Are Worth Checking](#neighbourhood-associations-and-business-districts-are-worth-checking)
- [Settlement and Newcomer Services Are Event Goldmines](#settlement-and-newcomer-services-are-event-goldmines)
- [Don't Over-Research Before Running the Playbook](#dont-over-research-before-running-the-playbook)
- [Meetup Feeds Need User-Agent](#meetup-feeds-need-user-agent)
- [Regional Groups Need Geo-Filtering](#regional-groups-need-geo-filtering)
- [LiveWhale University Calendars](#livewhale-university-calendars)
- [Legistar WebAPI for Government Meetings](#legistar-webapi-for-government-meetings)
- [University Event Systems Vary Widely](#university-event-systems-vary-widely)
  - [1. Centralized platforms (curl-and-done)](#1-centralized-platforms-curl-and-done)
  - [2. Decentralized — scrape the aggregate page](#2-decentralized--scrape-the-aggregate-page)
- [Drupal Sites Don't Have Standardized Feed Patterns](#drupal-sites-dont-have-standardized-feed-patterns)
- [Classify WordPress Sites at Scale with Plugin Detection](#classify-wordpress-sites-at-scale-with-plugin-detection)
- [Topical Searches Yield Long-Tail Sources](#topical-searches-yield-long-tail-sources)
  - [Example: History/Heritage](#example-historyheritage)
  - [Other Topical Searches to Try](#other-topical-searches-to-try)
- [When a Source Goes Dark, Follow the Events](#when-a-source-goes-dark-follow-the-events)

## "Curl-and-Done" Sources: No Scraper Needed

Many sources provide ICS feeds that can be added with just a curl command in the workflow — no scraper required. Always check for these before writing a scraper:

### WordPress + The Events Calendar = Free ICS
Sites running WordPress with "The Events Calendar" plugin (by StellarWP/Modern Tribe) have a built-in iCal endpoint:
```
https://example.com/events/?ical=1
```
Look for `PRODID:-//...ECPv6...` in the response to confirm.

**Examples:** The Big Easy Petaluma (30 events), Polly Klaas Community Theater (8 events).

### WordPress + Modern Events Calendar (MEC) = Free ICS
A different WordPress calendar plugin from The Events Calendar. Look for `wp-content/plugins/modern-events-calendar` in page source. The ICS endpoint is:
```
https://example.com/events/?mec-ical-feed=1
```
Look for `PRODID:-//WordPress - MEC` in the response to confirm. MEC feeds can be very large (thousands of events including past ones) — the pipeline filters by date automatically.

**Example:** York University Events Calendar (6,558 events via MEC).

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
4. Update `cities/{city}/SOURCES_CHECKLIST.md`
5. Run `python scripts/sync_feeds_txt.py` to regenerate `feeds.txt`

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

## CKAN Open Data Portals Have Government Meeting & Event Data

Many cities publish structured event data through CKAN (Comprehensive Knowledge Archive Network), an open-source data portal. The datastore API is standardized across all CKAN instances:
```
https://{ckan-host}/api/3/action/datastore_search?resource_id={id}&limit=500
```

Use `scrapers/lib/ckan.py` (`CKANScraper` base class) — subclasses just provide a resource ID and a `map_record()` method to map fields to event properties. The base class handles pagination automatically.

**How to find CKAN datasets:** Search for `{city} open data portal` or check `open.{city}.ca` / `data.{city}.gov`. Look for datasets with "meeting schedule", "events", or "calendar" in the name.

**Example:** Toronto has two CKAN datasets — meeting schedules (162 future meetings across 56 committees) and festivals/events (2,101 future events across 37 categories).

## Bibliocommons Library Platforms Have a Reusable API Pattern

Public-library systems on Bibliocommons expose structured event data via:
```
https://gateway.bibliocommons.com/v2/libraries/{library_slug}/events
```

The response includes event entities and embedded definitions (title, description, start/end, audience IDs, location IDs), so this is better than scraping rendered HTML pages.

Use `scrapers/lib/bibliocommons.py` (`BibliocommonsEventsScraper`) as the reusable base:
- handles pagination
- maps entities to ICS-ready event objects
- supports filter hooks (`audience_ids`, `type_ids`, `program_ids`, `language_ids`)

**Example:** `scrapers/toronto_public_library.py` configures `library_slug = "tpl"` and kids/family audience filters.

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

## Probe WordPress Sites Directly with `?ical=1`

Don't just rely on search engines to find WordPress Tribe Events sites. If you know venue or organization names in a city, **try appending `?ical=1` to their `/events/` page** directly. Many sites running The Events Calendar plugin don't show up in `inurl:/tribe_events/` searches but still serve ICS at that endpoint.

**Toronto example:** Probing known museums, theatres, community centres, and BIAs turned up 8 working feeds (Gardiner Museum, Bata Shoe Museum, Textile Museum, Toronto Botanical Garden, Buddies in Bad Times Theatre, Scadding Court, CultureLink, Bloor West Village BIA) — none of which appeared in search results.

## Neighbourhood Associations and Business Districts Are Worth Checking

Business Improvement Districts (called BIDs in the US, BIAs in Canada) often maintain WordPress event calendars for their neighbourhood. Same goes for neighbourhood associations and community councils.

**Toronto examples:** Bloor West Village Business Improvement Area (6 events), St. Lawrence Neighbourhood Association (82 events via Tockify), Councillor Jamaal Myers community calendar (27 events via Tockify).

## Settlement and Newcomer Services Are Event Goldmines

Immigrant settlement organizations and newcomer service agencies run huge numbers of community programs and events. They're often overlooked but can be the single highest-volume community source in a city.

**Toronto example:** CultureLink Settlement Services had 494 events via WordPress Events Manager ICS — the second-largest source after the main aggregator.

## Don't Over-Research Before Running the Playbook

It's tempting to spend time cataloging aggregators, building venue lists, and writing scrapers before trying the standard discovery playbook. Resist this. The platform searches (Tockify, WordPress `?ical=1`, Meetup ICS) reliably turn up dozens of ready-to-use feeds in a single pass. Run those first, then assess gaps.

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

## Legistar WebAPI for Government Meetings

Cities using Legistar (Granicus) for agenda management often have a public WebAPI. The API provides structured JSON for all government meetings.

**API endpoint pattern:**
```
https://webapi.legistar.com/v1/{client}/events
```

**Finding the client name:**
- Check the Legistar URL (e.g., `santa-rosa.legistar.com` → client is `santa-rosa`)
- Try variations: `santarosa`, `santa-rosa`, `SantaRosa`

**OData query examples:**
```bash
# Future events only
curl "https://webapi.legistar.com/v1/santa-rosa/events?\$filter=EventDate%20ge%20datetime'2026-02-14'&\$orderby=EventDate%20asc"

# Specific board/commission
curl "https://webapi.legistar.com/v1/santa-rosa/events?\$filter=EventBodyName%20eq%20'City%20Council'"
```

**Script:** `scrapers/legistar.py --client {client} --source "Source Name" -o output.ics`

**Note:** Not all Legistar instances have the WebAPI enabled. Test with a simple events request first. If you get a "Key or Token is required" error, the API may require authentication.

**Example:** Santa Rosa — 3,995 total records, WebAPI returns future scheduled meetings.

## University Event Systems Vary Widely

Universities range from fully centralized (one platform, one feed) to fully decentralized (every department runs its own CMS). Check in this order:

### 1. Centralized platforms (curl-and-done)
Many universities use a single events platform with standard endpoints:

| Platform | How to detect | Feed endpoint |
|----------|--------------|---------------|
| **Localist** | URL contains `/localist/` or uses `events.{university}.edu` | `/api/2/events`, `/events.rss`, or ICS export |
| **LiveWhale** | URL contains `/live/` | `{domain}/live/ical/events` |
| **WordPress Tribe** | `wp-content/plugins/the-events-calendar` in source | `?ical=1` |
| **WordPress MEC** | `wp-content/plugins/modern-events-calendar` in source | `?mec-ical-feed=1` |

These are the best case — one curl command gets the whole university.

**Examples:** UC Davis Library (Localist, 118 events), York University (MEC, 6,558 events), SRJC (LiveWhale, 130+ events).

### 2. Decentralized — scrape the aggregate page
Some universities (especially large ones with legacy infrastructure) have a central events page that aggregates feeds from dozens of departments, each running its own CMS. Don't try to add 30 individual department feeds — instead:

1. **Check the central events page** for an ICS feed (rare) or scrapeable HTML (common)
2. **Follow "More" links** from the aggregate page to get deeper per-department coverage
3. **Detect WordPress plugins** on department sites by checking `wp-content/plugins/` in page source — some departments will have Tribe Events (`?ical=1`) or MEC (`?mec-ical-feed=1`)

The aggregate page may cap events per department (UofT shows 5 each). Following "More" links with theme-specific parsers gets deeper coverage without writing 30 separate scrapers.

**Example:** UofT has 32 department calendars across 4+ Drupal themes and WordPress. One scraper with 5 parser patterns handles them all: 176 events from one scraper + 3 direct ICS feeds from departments that have Tribe Events.

## Drupal Sites Don't Have Standardized Feed Patterns

Unlike WordPress (where Tribe = `?ical=1` and MEC = `?mec-ical-feed=1`), Drupal sites vary wildly. Every Drupal installation has its own theme, views configuration, and CSS class names. Don't expect to build a reusable "Drupal scraper" — each site needs its own parser.

**What to look for in Drupal event pages:**
- `node-events-*` classes (common in university Drupal themes)
- `views-row` with event links (generic Drupal Views)
- `listing-item--events` (BEM-style custom themes)
- `field-event` or `field--name-title` (Drupal field formatters)

**What to try first:** Always check `?_format=json` on Drupal URLs — some sites have REST exports enabled (returns JSON). If you get `"A route that returns a rendered array..."`, REST is not configured for that view.

## Classify WordPress Sites at Scale with Plugin Detection

When probing many sites for feeds, check `wp-content/plugins/` in page source to quickly classify:
```bash
curl -sL "https://example.com/events/" | grep -o "wp-content/plugins/[^/]*" | sort -u
```

| Plugin | Feed URL |
|--------|----------|
| `the-events-calendar` | `?ical=1` |
| `modern-events-calendar` | `?mec-ical-feed=1` |
| `events-calendar-pro` | `?ical=1` (same as Tribe, pro adds filters) |
| Anything else | No standard ICS feed |

This is faster than trial-and-error with `?ical=1` on every site.

## Topical Searches Yield Long-Tail Sources

Beyond platform searches (Meetup, Tockify, WordPress `?ical=1`), topical searches find niche community groups that don't show up otherwise. The pattern: search `{topic} {city} site:meetup.com` and `{topic} {city} events calendar`, then probe each result for ICS feeds.

### Example: History/Heritage

Searching for history/heritage sources in Toronto found 25 events from 3 new ICS feeds:

**High-value Meetup groups:**
- **Walking tour groups** ("Toronto History Walks", "Hidden History") — often 5,000-10,000 members with regular events
- **Reenactment groups** (Society for Creative Anachronism chapters) — weekly medieval arts events
- **History discussion groups** — may be inactive but worth checking

**Provincial/state historical societies:**
- Search `{province/state} historical society` — often have WordPress Tribe Events with ICS feeds
- Events may be province-wide but include local events worth capturing
- Example: Ontario Historical Society had Toronto Postcard Club, Canada Black Music Archives

**Heritage organizations (often seasonal):**
- Heritage {City} organizations — walking tours typically summer only (June-November)
- **Doors Open** events — annual city-wide heritage events
- Architectural Conservancy chapters — annual symposiums, often static pages

**Non-starters to skip:**
- **Genealogy societies** — often Cloudflare protected or members-only
- **Historic sites with ticketing** — often have static sites or broken ticketing feeds
- **Historical associations** — many are inactive (check when last events were posted)

**Search terms that work:**
```
{city} historical society events
{city} history heritage site:meetup.com
{city} walking tours history
{city} architecture preservation events
```

### Other Topical Searches to Try

The same pattern applies to other topics. See AGENTS.md for the full list:
```
music, hiking, dance, dogs, yoga, art, running, cycling, wine,
beer, trivia, book club, garden, comedy, theater, kids, seniors,
church, history, heritage, architecture, genealogy
```

Document findings in `cities/{city}/SOURCES_CHECKLIST.md` under a "Topical Search" section, noting which searches have been done and what was found.

## When a Source Goes Dark, Follow the Events

Sources break. A site adds Cloudflare bot protection, a platform redesigns its API, a domain expires. The health report dashboard shows the symptom: a feed drops to 0 events. What happens next depends on whether a curator cares about that category.

**Case study: Volunteer Toronto**

The health report showed `volunteer_toronto` at 0 events. The scraper had targeted `volunteertoronto.ca` directly — RSS, ICS, and HTML endpoints — but the entire site was now behind Cloudflare, returning 403 on every request.

A curator who cares about volunteerism in Toronto won't stop there. The investigation path:

1. **Web search for the same events elsewhere.** Searching for "volunteer toronto" events turned up listings on Toronto Public Library's BiblioCommons, Eventbrite, Meetup, and City of Toronto pages.

2. **Check Eventbrite.** Volunteer Toronto has an [Eventbrite organizer page](https://www.eventbrite.ca/o/volunteer-toronto-9797196651) — but it showed 0 future events (last activity was 2023). Dead end.

3. **Check BiblioCommons.** TPL's events API at `gateway.bibliocommons.com` showed Volunteer Toronto events tagged with `programId: 68b050fad7b6cc3d009b8dcf`. These are the same "How to Become a Volunteer" workshops, newcomer settlement services, English conversation circles, and career programs — 182 events, all with per-event URLs, locations, and descriptions.

4. **Reuse existing infrastructure.** We already had a `BibliocommonsEventsScraper` base class for TPL kids events. The new scraper is 10 lines — just a subclass with `program_ids = ["68b050fad7b6cc3d009b8dcf"]`. It replaced 436 lines of Cloudflare-blocked code and immediately produced 82 events.

**The general pattern:** Events often exist in multiple places. When the original source becomes inaccessible, search for who else hosts, aggregates, or republishes the same events. Check:
- The organization's presence on Eventbrite, Meetup, Facebook
- Library systems that host their programs (BiblioCommons, LibCal)
- Municipal event calendars that list partner organizations
- Aggregator sites that may have picked up the events

Don't give up on a category just because one source is inaccessible. The events are still happening — they're just published somewhere else.
