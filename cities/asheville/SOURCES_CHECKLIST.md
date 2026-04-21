# Asheville Calendar Source Checklist

## Currently Implemented

### ICS / Platform Feeds

| Source | Platform | Events | Feed URL |
|--------|----------|--------|----------|
| Asheville Farmers Markets | Tockify (`wild.goods`) | 365 | `tockify.com/api/feeds/ics/wild.goods` |
| UNC Asheville | WordPress Tribe Events | 17 | `unca.edu/events/?ical=1` |
| NC Arboretum | WordPress Tribe Events | 27 | `ncarboretum.org/events/?ical=1` |
| City of Asheville | WordPress Tribe Events | 12 | `ashevillenc.gov/events/?ical=1` |
| LiveMusicAsheville.com | WordPress Tribe Events | 30 | `livemusicasheville.com/events/?ical=1` |
| Asheville Art Museum | WordPress Tribe Events | 30 | `ashevilleart.org/events/?ical=1` |
| River Arts District | WordPress Tribe Events | 30 | `riverartsdistrict.com/events/?ical=1` |
| Buncombe County Community Engagement | CivicPlus ICS (catID=26) | 130 | `buncombenc.gov/…?catID=26&feed=calendar` |
| Buncombe County Main Calendar | CivicPlus ICS (catID=14) | 107 | `buncombenc.gov/…?catID=14&feed=calendar` |
| Buncombe County Parks & Recreation | CivicPlus ICS (catID=40) | 51 | `buncombenc.gov/…?catID=40&feed=calendar` |
| Buncombe County Public Health Mobile Team | CivicPlus ICS (catID=35) | 39 | `buncombenc.gov/…?catID=35&feed=calendar`; added manually (add_feed.py test fails on cp1252 decode of feed content) |
| Buncombe County Planning | CivicPlus ICS (catID=37) | 23 | `buncombenc.gov/…?catID=37&feed=calendar` |

### Songkick Scrapers

| Source | Songkick ID | Events | Notes |
|--------|-------------|--------|-------|
| Asheville Music Hall | 107138 | 5 | 31 Patton Ave |
| Asheville Yards | 4591672 | 5 | 75 Coxe Ave; outdoor amphitheater |
| Static Age Records | 832601 | 5 | 82 N Lexington Ave |
| The Grey Eagle | 39035 | 5 | 185 Clingman Ave; Etix/Rockhouse Partners. RSS+JSON-LD scraper would be more complete (see below). |
| The Orange Peel | 289 | 5 | 101 Biltmore Ave; Etix/Rockhouse Partners. RSS+JSON-LD scraper would be more complete. |
| Eulogy | 4519500 | 8 | 10 Buxton Ave; punk/metal/indie |
| Revival | 4617227 | 8 | 66 Asheland Ave |
| The One Stop at Asheville Music Hall | 1333371 | 8 | 55 College St; smaller stage in same building as Asheville Music Hall |
| Harrah's Cherokee Center | 4371507 | 8 | 87 Haywood St; arena (7,700 cap); also wired for Ticketmaster scraper (see Needs Scraper) |

### Meetup Groups (32 groups)

| Group | Slug | Events | Status |
|-------|------|--------|--------|
| Asheville Tech Events | avltech | 10 | ✅ feeds.txt |
| Asheville Runners | asheville-runners | 10 | ✅ feeds.txt |
| Asheville Introverts | asheville-introverts | 10 | ✅ feeds.txt |
| AVL Digital Nomads | avl-digital-nomads | 10 | ✅ feeds.txt |
| Asheville 20s-40s Social Group | asheville-20s-40s-social-group | 10 | ✅ feeds.txt |
| Asheville Area A Cappella Singers | asheville-area-a-cappella-singers | 10 | ✅ feeds.txt |
| Men in Harmony | men-in-harmony | 10 | ✅ feeds.txt |
| Awakening Asheville | awakeningasheville | 10 | ✅ feeds.txt |
| Inner Peace Collective | inner-peace-collective | 10 | ✅ feeds.txt |
| Skinny Beats Sound Meditation | skinny-beats-sound-meditation | 10 | ✅ feeds.txt |
| Asheville Movement Collective (dance) | amcdance | 10 | ✅ feeds.txt |
| Access Consciousness Asheville | access-consciousness-asheville | 10 | ✅ feeds.txt |
| PlayYourCourt Asheville Tennis | playyourcourt-asheville-tennis | 10 | ✅ feeds.txt |
| Asheville Singles Over 50 Golf | asheville-singles-golf | 10 | ✅ feeds.txt |
| Shut Up & Write Western NC | shutupandwriteasheville | 10 | ✅ feeds.txt |
| Haywood County Walking Group | haywood-county-walking-meetup-group | 9 | ✅ feeds.txt |
| Asheville Mountains-to-Sea Trail Hiking Club | asheville-mountains-to-sea-trail-hiking-club | 8 | ✅ feeds.txt |
| Friendly People in Asheville | 20s-30s-40s-friendly-people-do-cool-stuff | 7 | ✅ feeds.txt |
| Asheville Hiking Group | ashevillehikinggroup | 2 | ✅ feeds.txt |
| Asheville Adventures 30s & 40s | asheville-adventures-30-s-40-s | 4 | ✅ feeds.txt |
| Asheville Social Club | ashevillesocial | 3 | ✅ feeds.txt |
| Asheville Hash House Harriers | avlh3-on-on | 3 | ✅ feeds.txt |
| Asheville TENS Card Game Group | asheville-spade-games-meetup-group | 3 | ✅ feeds.txt |
| Mindful Meet & Mingle Asheville Singles | mindful-meet-mingle-asheville-singles | — | ✅ feeds.txt |
| Asheville Cuddle Collective | asheville-cuddle-collective | 4 | ✅ feeds.txt |
| AVL International Connections | international-connections-avl | 1 | ✅ feeds.txt |
| Asheville Beer Drinkers | asheville-beer-drinkers | 1 | ✅ feeds.txt |
| Asheville Garden Club | asheville-garden-club-meetup-group | 1 | ✅ feeds.txt |
| Asheville Lose The Booze Crew | asheville-lose-the-booze-crew | 1 | ✅ feeds.txt |
| Psychedelic Society of Asheville | psychedelic-society-of-asheville | 1 | ✅ feeds.txt |
| She Owns It AVL | she-owns-it-avl | 1 | ✅ feeds.txt |
| Dodgeball AVL | meetup-group-ssbjicnx | 2 | ✅ feeds.txt |
| BANG Broker Alliance Networking Group | bang-broker-alliance-networking-group | 0 | ❌ No events |

---

## Needs Scraper (buildable)

| Source | URL | Approach | Notes |
|--------|-----|----------|-------|
| The Grey Eagle | thegreyeagle.com/calendar/feed/ | RSS + JSON-LD per-page | 97 RSS items; `rhp-events` plugin; `startDate` confirmed in JSON-LD on each event page; same pattern as `scrapers/sweetwater.py`. Songkick added as interim (5 events). |
| The Orange Peel | theorangepeel.net/events/feed/ | RSS + JSON-LD per-page | 70 RSS items; identical pattern to Grey Eagle. Songkick added as interim (5 events). |
| Harrah's Cherokee Center | ticketmaster.com/venue/368913 | Ticketmaster scraper | Songkick (ID 4371507) now has 8 events — added as interim. Ticketmaster would be more complete: needs `TICKETMASTER_API_KEY` (free at developer.ticketmaster.com), TM venue ID `KovZpZAJvnIA`, scraper `scrapers/ticketmaster.py`. |
| Asheville Community Theatre | ashevilletheatre.org | TBD | WordPress, `mc_event` post type (27 shows, runs through Aug 2026). No Tribe/MEC detected. Try `?mec-ical-feed=1`; also check Eventbrite organizer page. |
| Wortham Center for the Performing Arts | worthamarts.org | HTML scraper | WordPress with Toolset Blocks (custom CPT). No Tribe/MEC plugin, no ICS. RSS at `/events/feed/` has show titles but pubDate is the season-announcement date, not show date. JSON-LD on event pages is `WebPage` type with no `startDate`. Would need to scrape show dates from HTML. ~10 shows per season. |
| NC Stage Company | ncstage.org | TBD | Professional equity theatre, 125-seat. WordPress; no feed detected. Small event count (~1 production at a time). |
| Southern Highland Craft Guild / Folk Art Center | southernhighlandguild.org/calendar/ | TBD | WordPress; `?ical=1` returns HTML (JS-loaded). Craft demos, folk art events. Try Tribe REST API. |
| Mountain Xpress | mountainx.com/events/ | TBD | Local alt-weekly; Tribe Events calendar but Cloudflare-protected (`?ical=1` blocked). High-value aggregator — covers music, arts, community across WNC. Contact web admin for WAF exception. |
| asheville.com/calendar-events | asheville.com | none | High-value tourism events calendar. Built on **MainStreet Online** (mainstreetonline.com), a proprietary SaaS for local/tourism sites based in Asheville. No public API, no ICS feed. Cloudflare managed challenge blocks all automated fetches. Contact MainStreet Online directly for a data partnership or ICS export. |
| Pisgah Brewing Company | pisgahbrewing.com/events/ | Eventbrite | Direct site blocked (403). Has Eventbrite organizer page: `eventbrite.com/o/pisgah-brewing-company-12162946786`. Live music venue in Black Mountain (~10 mi east). |
| Asheville Theater Alliance | ashevilletheateralliance.org/asheville-performance-calendar/ | TBD | Aggregate calendar for theater/dance/improv (NC Stage, HART, Attic Salt, Terpsicorps, etc.). No ICS found; membership-based. Investigate platform. |
| UNC Asheville Music Dept | music.unca.edu/engage/upcoming-events/?ical=1 | ICS direct | 17 events; may partially duplicate main UNCA feed — add if events differ. |
| Asheville Chamber of Commerce | web.ashevillechamber.org | RSS scraper (`asheville_chamber.py`) | ChamberMaster RSS; event dates parsed from title field (pubDate is listing date). 58 events: networking mixers, ribbon cuttings, business workshops, community events. |
| Asheville Tourists (MiLB) | milb.com/asheville/schedule | Custom scraper | 76 home + away games Apr–Sep 2026. No ICS on milb.com, OurSports Central, or LeagueApps. Would need HTML schedule scraper. Lower community value (sports games). |

---

## To Investigate

- [ ] **Grey Eagle** — build RSS+JSON-LD scraper (see `scrapers/sweetwater.py`; 97 items, `startDate` confirmed at `2026-06-07T17:30:00-0400` on test page)
- [ ] **Harrah's Cherokee Center** — get free Ticketmaster API key; run `scrapers/ticketmaster.py --venue-id KovZpZAJvnIA --name "Harrah's Cherokee Center Asheville" --timezone America/New_York`
- [ ] **Additional Meetup groups** — topical searches not yet done: arts, dance, theater, LGBTQ+, faith, seniors, civic orgs
- [ ] **Topical venue discovery** — initial pass done (see Needs Scraper); second pass not yet done: check `whereyatavlmusic.com/venues` directory and `exploreasheville.com/things-to-do/music/music-venues` for additional venues
- [ ] **Asheville Community Theatre** — try `?mec-ical-feed=1`; check Eventbrite organizer page
- [ ] **Mountain Xpress** — contact web admin for Cloudflare WAF exception (high-value aggregator)
- [ ] **Asheville Theater Alliance** — identify calendar platform; may be the best single source for all local theater/dance/improv
- [ ] **Pisgah Brewing** — wire up Eventbrite scraper (`eventbrite.com/o/pisgah-brewing-company-12162946786`)

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Tockify `wncevents` | 0 events |
| Tockify `bywater.asheville` | 0 events |
| Tockify `whns.calendar` | 95 events but Greenville/Spartanburg SC area, not Asheville |
| Legistar | "LegistarConnectionString not set up" — Asheville doesn't use Legistar |
| Asheville FM | Tribe Events plugin installed but 0 events; uses Radio Station Pro for show scheduling |
| ArtsAVL (connect.artsavl.org) | Cloudflare Turnstile bot protection |
| WNCW community calendar | Brightspot CMS; no standard ICS feed |
| Asheville Downtown Association | WordPress but no Tribe/MEC; no ICS |
| BPR Blue Ridge Public Radio | Custom CMS; no events calendar |
| Buncombe County CivicEngage (root) | `buncombenc.gov/iCalendar.aspx` is an HTML index page, not a feed — but per-category feeds at `/common/modules/iCalendar/iCalendar.aspx?catID=N&feed=calendar` return valid ICS; see Currently Implemented |
| Isis Music Hall (Songkick) | 0 future events on Songkick (lounge sub-venue; check direct site) |
| Etix public API | `api.etix.com/v3` requires partner credentials; no public endpoint |
| Harrah's Cherokee Center (Songkick, 2026-04) | Was 0 future events; now has 8 — added as Songkick source. Ticketmaster scraper still preferred for complete coverage. |
| AB Tech | Drupal site at `/event-calendar`; ~7 academic events only (art shows, career expos, commencement); no ICS feed, no `?_format=json` (returns 406); low community value |
| Buncombe County Libraries (librarycalendar.com) | LibraryCalendar proprietary platform; no ICS. **However:** Trumba hosts all 9 branches — `trumba.com/calendars/public-libraries.ics` (200 events: Pack Memorial, Black Mountain, Enka-Candler, Leicester, North Asheville, Oakley/South Asheville, Skyland/South Buncombe, Weaverville, West Asheville). Added to pending_feeds.txt. |
| Pack Square Park | No sub-calendar on ashevillenc.gov; city calendar has no category or location filters at all; already covered by City of Asheville Tribe feed |
| Pritchard Park (drum circle) | Asheville Downtown Association (ashevilledowntown.org) is Squarespace but `?format=json` returns site metadata, not events collection — Squarespace scraper pattern doesn't work here. LiveMusicAsheville.com lists the drum circle but covers all venues city-wide. The drum circle is a recurring weekly event (Fri 6–10pm, Apr–Oct) — no clean standalone feed found. |
