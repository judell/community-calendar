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

### Songkick Scrapers

| Source | Songkick ID | Events | Notes |
|--------|-------------|--------|-------|
| Asheville Music Hall | 107138 | 5 | 31 Patton Ave |
| Asheville Yards | 4591672 | 5 | 75 Coxe Ave; outdoor amphitheater |
| Static Age Records | 832601 | 5 | 82 N Lexington Ave |
| The Grey Eagle | 39035 | 5 | 185 Clingman Ave; Etix/Rockhouse Partners. RSS+JSON-LD scraper would be more complete (see below). |

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
| The Orange Peel | theorangepeel.net/events/feed/ | RSS + JSON-LD per-page | 70 RSS items; identical pattern to Grey Eagle. Both use Etix/Rockhouse Partners ticketing. |
| Harrah's Cherokee Center | ticketmaster.com/venue/368913 | Ticketmaster scraper | Needs `TICKETMASTER_API_KEY` env var (free at developer.ticketmaster.com). TM venue ID: `KovZpZAJvnIA`. Scraper: `scrapers/ticketmaster.py`. |
| Asheville Community Theatre | ashevilletheatre.org | TBD | WordPress, no Tribe/MEC. Check Eventbrite organizer page. |
| Wortham Center for the Performing Arts | worthamarts.org | TBD | WordPress, no Tribe/MEC. Own box office (ASP.NET). Check Songkick. |
| UNC Asheville Music Dept | music.unca.edu/engage/upcoming-events/?ical=1 | ICS direct | 17 events; may partially duplicate main UNCA feed — add if events differ. |

---

## To Investigate

- [ ] **Grey Eagle** — build RSS+JSON-LD scraper (see `scrapers/sweetwater.py`; 97 items, `startDate` confirmed at `2026-06-07T17:30:00-0400` on test page)
- [ ] **Orange Peel** — same scraper pattern as Grey Eagle (70 items)
- [ ] **Harrah's Cherokee Center** — get free Ticketmaster API key; run `scrapers/ticketmaster.py --venue-id KovZpZAJvnIA --name "Harrah's Cherokee Center Asheville" --timezone America/New_York`
- [ ] **Asheville Tourists (MiLB)** — check milb.com/asheville/schedule for iCal subscription link
- [ ] **AB Tech** — Drupal site; try `?_format=json` on event pages; or check if Sidearm scraper applies
- [ ] **Asheville Chamber** — `web.ashevillechamber.org` uses GrowthZone but `/api/events` returns 404; investigate correct endpoint
- [ ] **Buncombe County Libraries** — `buncombe.librarycalendar.com`; custom Drupal-based platform; no ICS found; investigate API
- [ ] **Pack Square Park** — check for a park-specific events sub-calendar on ashevillenc.gov
- [ ] **Additional Meetup groups** — topical searches not yet done: arts, dance, theater, LGBTQ+, faith, seniors, civic orgs
- [ ] **Topical venue discovery** — live music blogs/directories for WNC not yet checked (e.g., LiveMusicAsheville already added; check northbaylivemusic.com equivalent for AVL)

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
| Buncombe County CivicEngage | `/iCalendar.aspx` returns HTML not ICS |
| Isis Music Hall (Songkick) | 0 future events on Songkick (lounge sub-venue; check direct site) |
| Etix public API | `api.etix.com/v3` requires partner credentials; no public endpoint |
| Harrah's Cherokee Center (Songkick) | 0 future events on Songkick; use Ticketmaster scraper instead |
