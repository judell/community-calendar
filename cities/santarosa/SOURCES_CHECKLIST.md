# Santa Rosa / Sonoma County Calendar Source Checklist

## Currently Implemented

### Live ICS Feeds
| Source | URL | Notes |
|--------|-----|-------|
| Arlene Francis Theater | Google Calendar | Events at local theater |
| Luther Burbank Center | ~~`lutherburbankcenter.org/events/?ical=1`~~ | CONVERTED 2026-08-07 to `tribe_rest.py` scraper (feed served SiteGround 403 block page) |
| Schulz Museum | `schulzmuseum.org/events/?ical=1` | Charles Schulz museum events |
| Sonoma.com | `sonoma.com/events/?ical=1` | Regional tourism/events |
| GoLocal Coop | `golocal.coop` Tribe Events | Local business coop |
| Sonoma County AA | `sonomacountyaa.org/events/?ical=1` | Recovery community |
| DSA Sonoma County | Google Calendar | Political org |
| Sonoma Community Center | ~~`sonomacommunitycenter.org/events/?ical=1`~~ | REMOVED 2026-08-07 (dead after site redesign; `tribe_rest.py` scraper supersedes) |
| Santa Rosa Symphony | ~~`srsymphony.org/events/?ical=1`~~ | REMOVED 2026-08-07 (feed serves empty reply; `santa_rosa_symphony.py` scraper supersedes) |
| California Bluegrass Association | Filtered Tribe Events ICS | Sonoma-area bluegrass/jam/live performance feed (30 events as of 2026-05-10) |

### Scraped Sources
| Source | Scraper | Notes |
|--------|---------|-------|
| North Bay Derby | `squarespace.py` | Roller derby — Squarespace events page |
| Monroe County Library (Sonoma) | `library_intercept.py` | Library events |
| North Bay Bohemian | `cityspark/bohemian.py` | Alt-weekly events calendar |
| Press Democrat | `cityspark/pressdemocrat.py` | Newspaper events |
| Sonoma County Parks | `sonoma_parks.py` | Regional parks |
| California Theatre | `cal_theatre.py` | Historic theater |
| Copperfield's Books | `copperfields.py` | Bookstore events |
| Sonoma County Gov | `sonoma_county_gov.py` | Government meetings |
| SRCC | `srcc.py` | Santa Rosa Chamber? |
| Museum of Sonoma County | ICS | Local museum |
| Spreckels Performing Arts | `spreckels.py` | REWRITTEN 2026-08-07: Divi show pages under `/show/<season>-season/` (Tribe REST removed in site redesign); all-day run ranges, no showtimes exposed |
| Luther Burbank Center | `tribe_rest.py` | Converted 2026-08-07 from dead `?ical=1`; SiteGround PoW WAF blocks most programmatic access — valid-empty on blocked days, `--user-agent "Mozilla/5.0"`; reliable coverage needs venue allowlist or headless harness |
| Uptown Theatre Napa | `tribe_rest.py` | Converted 2026-08-07 from dead `?ical=1`; same SiteGround WAF situation as LBC |
| Lagunitas Brewing Company | `lagunitas.py` | Petaluma taproom; live music, trivia, food trucks (37 events) |
| Creative Sonoma | `creative_sonoma.py` | County arts agency aggregator (55 events) |
| Cinnabar Theater | `cinnabar.py` | Petaluma community theater (5 shows/season); date parser extended 2026-08-07 for abbreviated months and comma-less years ("Sept. 18 – Oct. 4 2026") |
| Green Music Center | `green_music_center.py` | Sonoma State performing arts venue (10 events) |
| Occidental Center for the Arts | `occidental_arts.py` | Occidental performing arts venue and studio classes (42 future events as of 2026-05-10) |
| Elephant in the Room (Songkick) | `songkick.py` | Healdsburg music pub — artist-sourced tour dates |
| Elephant in the Room (Eventbrite) | `eventbrite.py` | Healdsburg music pub — ticketed events |
| Rancho Nicasio | iCal feed | Nicasio roadhouse — WordPress Tribe Events (30 events) |
| The Big Easy | ~~iCal feed~~ `songkick.py` | Petaluma underground nightclub — Tribe ICS feed REMOVED 2026-08-07 (site replatformed, past-only events); Songkick scraper covers |
| Sweetwater Music Hall | `songkick.py` | Mill Valley — flagship North Bay venue (8+ events) |
| Mystic Theatre | `songkick.py` | Petaluma — major indie venue (8+ events) |
| HopMonk Tavern Sebastopol | `songkick.py` | Sebastopol — beer garden + live music (8+ events) |
| Phoenix Theater | `songkick.py` + `eventbrite.py` | Petaluma — Songkick (8+) + Eventbrite (13 events) |
| The Will Call | `songkick.py` | Cotati — music venue (8+ events) |
| Blue Note Napa | `songkick.py` | Napa — major jazz venue (8+ events) |
| Twin Oaks Roadhouse | `songkick.py` | Penngrove — HopMonk-owned roadhouse (3 events) |
| The Lost Church | `songkick.py` | Santa Rosa — intimate listening room (3 events) |
| The Fern Bar | `songkick.py` | Sebastopol — nightly live music (3 events) |
| Shady Oak Barrel House | `songkick.py` | Santa Rosa — brewery + live music (3 events) |
| THE 222 | `songkick.py` | Healdsburg — music venue (3 events) |
| Rio Nido Roadhouse | `songkick.py` | Rio Nido — live music (3 events) |
| Redwood Cafe | `redwood_cafe.py` | Cotati — live music; Songkick interim + My Calendar ICS both REMOVED 2026-08-07 per 2026-07-17 flags (first-party HTML scraper is the sole producer) |
| HenHouse Brewing | `songkick.py` | Santa Rosa — brewery (1 event) |

### City of Santa Rosa Calendars
Multiple ICS feeds from `srcity.org`:
- Main Calendar
- City Offices Closed
- Recreation and Parks
- Events

---

## Meetup Groups (Discovered 2025-02-08)

Ran Meetup discovery playbook. Found 66 groups, 33 with active events.

### Recommended High-Value Groups (Ready to Add)

| Group | ICS URL | Events | Category | Notes |
|-------|---------|--------|----------|-------|
| sonoma-county-go-wild-hikers | `meetup.com/sonoma-county-go-wild-hikers/events/ical/` | 3 | Outdoor | Local hiking group - "Islands in the Sky", "Lake Sonoma Hike" |
| shutupandwritewinecountry | `meetup.com/shutupandwritewinecountry/events/ical/` | 10 | Arts | Writing meetups in Petaluma/Sebastopol |
| scottish-country-dancing | `meetup.com/scottish-country-dancing/events/ical/` | 10 | Dance | Weekly classes at Monroe Hall |
| sonoma-county-womens-wine-club | `meetup.com/sonoma-county-womens-wine-club/events/ical/` | 9 | Social/Wine | Wine club + social events |
| santa-rosa-toastmasters-public-speaking-meetup-group | `meetup.com/santa-rosa-toastmasters-public-speaking-meetup-group/events/ical/` | 10 | Professional | Weekly meetings |
| nataraja-school-of-traditional-yoga | `meetup.com/nataraja-school-of-traditional-yoga/events/ical/` | 7 | Wellness | Yoga/pranayama classes |
| santa-rosa-womens-creativity-collective | `meetup.com/santa-rosa-womens-creativity-collective/events/ical/` | 6 | Arts | Creative workshops at The Arthaus |
| sonoma-county-boomers | `meetup.com/sonoma-county-boomers/events/ical/` | 6 | Social | Social events for boomers |

**EXCLUDED** (events are international destinations, not local):
- ~~The-International-Wanderers~~ - Travel trips to Patagonia, Ireland, Alaska, etc.
- ~~culturelovers~~ - International travel to Thailand, Egypt, Japan, etc.

### Other Active Groups (Lower Priority)

| Group | Events | Notes |
|-------|--------|-------|
| Hidden-Backroads-Adventures | 10 | Speed dating / social events |
| PlayYourCourt-Santa-Rosa-Tennis | 10 | Tennis - may be commercial |
| apa-pool-league | 10 | Pool league |
| real-estate-investor-community-santa-rosa | 10 | Real estate networking |
| Alternative-Healing-Exploration | 10 | Healing workshops |
| northern-california-plant-medicine-community | 10 | Plant medicine events |
| the-unstruck-drum-center-for-shamanism-healing | 8 | Shamanism events |
| sarogn | 7 | Unknown category |
| the-santa-rosa-spiritual-experiences-group | 6 | Spiritual events |
| north-bay-social-group-20s-and-30s | 3 | Young adult social |
| bce-before-christian-era | 3 | Historical interest |
| entheogens-in-sonoma | 3 | Entheogens |
| Woodworking-Workshops-for-Women | 2 | Woodworking |
| lets-go-golden-girls | 2 | Women's social |
| full-circle-studio | 2 | Studio events |

### Groups with No Current Events
The following groups exist but had no upcoming events at time of discovery:
ai-northbay, ambgroup, bootstrapped-af-podcast-mastermind-group, happy-over-50, 
kayaking-sonoma-beyond, ladieswithnobabies, localbitcoin-meetup, north-bay-adventures, 
north-bay-hikers-born-1990-2000, santa-rosa-30s-40s-50s-meet-and-hangout-group, 
senior-walkabouters, sonoma-county-millennials, sonoma-county-shenanigans, 
Sonoma-County-Photography-Group, Sonoma-County-Wanderers, womens-wellness-meetup-group

---

## Eventbrite (Retired 2026-02-15)

Retired: Eventbrite scraper stopped producing results (HTML scraping broke). No public feeds available.

---

## Potential Additional Sources

### Venues to Investigate
| Source | URL | Status |
|--------|-----|--------|
| Raven Performing Arts Theater | `raventheater.org` | PENDING |
| 6th Street Playhouse | `6thstreetplayhouse.com` | PENDING |
| Glaser Center | `glasercenter.com` | PENDING |
| Wells Fargo Center | ? | PENDING |

### Organizations
| Source | URL | Status |
|--------|-----|--------|
| Sonoma County Farm Trails | `farmtrails.org` | PENDING |
| Sonoma Land Trust | `sonomalandtrust.org` | PENDING |
| LandPaths | `landpaths.org` | PENDING - outdoor events |

### Colleges
| Source | URL | Status |
|--------|-----|--------|
| Santa Rosa Junior College | `calendar.santarosa.edu/live/ical/events` | ✅ ADDED (LiveWhale, 114 events) |
| Sonoma State University | `sonoma.edu/events` | PENDING |

---

## Tockify Calendars (Discovered 2026-02-08)

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Rileystreet Art Supply | `tockify.com/api/feeds/ics/rileystreet.art.com` | 561 | Multi-location art supply store, events tagged by location |

## Additional Meetup Groups (Discovered 2026-02-08)

| Group | ICS URL | Events | Notes |
|-------|---------|--------|-------|
| amorc-santa-rosa-pronaos | `meetup.com/amorc-santa-rosa-pronaos/events/ical/` | 10 | Monthly Mystical Seekers Series |
| sarogn (Game Night) | `meetup.com/sarogn/events/ical/` | 7 | 3rd Saturday board/card games |

## CitySpark / Shared Upstream (Discovered 2026-02-08)

The Bohemian, Press Democrat, and NorCal Public Media calendars all use **CitySpark** as their upstream platform. ~58% of events overlap between Bohemian and Press Democrat. NorCal Public Media (acct #6164) would mostly duplicate existing coverage.

| Publisher | CitySpark Slug | PPID | Geo Radius |
|-----------|---------------|------|------------|
| Bohemian | `Bohemian` | 9093 | 30mi |
| Press Democrat | `SRPressDemocrat` | 8662 | 40mi |
| NorCal Public Media | `norcalpublicmedia` | 6164 | unknown |

## Non-Starters (Investigated 2026-02-08)

| Source | Platform | Why |
|--------|----------|-----|
| Cal Theatre (caltheatre.com) | Wix | No calendar export |
| Downtown Santa Rosa (downtownsantarosa.org) | Unknown | No discoverable feed |
| Santa Rosa Metro Chamber | Unknown | No discoverable feed |
| Sonoma Valley Events (sonomavalleyevents.com) | GatherBoard | RSS page says "Coming Soon" |
| Bandsintown | Proprietary | 403, no public feed |
| Visit Santa Rosa (visitsantarosa.com) | Simpleview | Tourism site, no public feed |
| Brew Coffee and Beer (brewcoffeeandbeer.com) | WordPress (All-in-One Event Calendar) | ICS feed exists but empty; site directs to Facebook for events |
| Happy over 50 Meetup | Meetup | 0 events |
| NorCal Public Media | CitySpark | Would mostly duplicate Bohemian + Press Democrat |

---

## Notes

- Santa Rosa is the largest city in Sonoma County (Wine Country)
- Many events are wine/food related
- Strong outdoor recreation community (hiking, biking)
- Arts scene centered around downtown Santa Rosa

## Direct Scraper Sources (Added 2026-02-13)

### Occidental Center for the Arts
| Field | Value |
|-------|-------|
| URL | https://www.occidentalcenterforthearts.org/upcoming-events |
| Platform | Squarespace events with per-event `?format=ical` exports |
| Scraper | `scrapers/occidental_arts.py` |
| Output | `cities/santarosa/occidental_arts.ics` |
| Events Found | 42 future events (as of 2026-05-10) |

**Note:** Direct source added because indirect coverage from regional aggregators was incomplete. The scraper now uses the Squarespace ICS export for canonical start/end times and location, and falls back to the listing-card description when the ICS payload is sparse.

### Sebastopol Center for the Arts (SebArts)
| Field | Value |
|-------|-------|
| URL | https://www.sebarts.org/classes-and-events |
| Platform | Squarespace |
| Scraper | `scrapers/sebarts.py` |
| Output | `cities/santarosa/sebarts.ics` |
| Events Found | 29 (as of 2026-02-13) |

**Note:** SebArts events were already appearing via the Bohemian (CitySpark) feed, but this direct scraper provides:
- Faster updates (no dependency on Bohemian's crawl schedule)
- All events (not just those Bohemian editors select)
- More reliable event details

### Sebastopol Documentary Film Festival
| Field | Value |
|-------|-------|
| URL | https://www.sebastopolfilm.org/ |
| Platform | Squarespace (static pages) |
| Status | No dedicated events feed needed |

**Note:** SDFF events appear on SebArts calendar (they're hosted there). For example:
- SDFF 2026 Launch Party (Feb 20, 2026) shows on SebArts as "SDFF Program LAUNCH/ Q&A"
- Festival dates: April 9-12, 2026

The film festival doesn't maintain its own events feed - it's more of a promotional site. Their events are listed through SebArts and may also appear in Bohemian/Press Democrat coverage.

## Mobilize.us (Added 2026-03-12)

| Field | Value |
|-------|-------|
| URL | https://www.mobilize.us/indivisiblesonomacounty/ |
| Platform | Mobilize.us (embedded `__MLZ_EMBEDDED_DATA__`) |
| Script | `scrapers/mobilize.py --url <org_page> --name <source_name>` |
| Output | `cities/santarosa/mobilize_indivisible_sonoma.ics` |
| Events Found | ~142 (as of 2026-03-12) |

**Note:** Generic scraper — can be reused for any Mobilize.us organization page in any city. Events include civic actions, phone banks, protests, and political organizing from Indivisible Sonoma County and partner orgs (Swing Left, No Kings, etc.). Many events are recurring with multiple timeslots.

---

## City of Santa Rosa Legistar (Added 2026-02-14)

| Field | Value |
|-------|-------|
| URL | https://santa-rosa.legistar.com/Calendar.aspx |
| API | `https://webapi.legistar.com/v1/santa-rosa/events` |
| Platform | Legistar (Granicus) |
| Script | `scrapers/legistar.py --client santa-rosa` |
| Output | `cities/santarosa/legistar.ics` |

**Note:** The Legistar WebAPI provides structured JSON data for all city government meetings - City Council, Planning Commission, Board of Public Utilities, Design Review Board, and many other boards and commissions. This replaces the stale srcity.org ICS feeds which were not being updated.

**Coverage:** Future meetings only (events are added to Legistar as they're scheduled, typically a few weeks/months ahead). Historical meetings remain in Legistar but are filtered out.

**Cancelled meetings:** The script automatically skips events with `EventAgendaStatusName: "Cancelled"`.

---

## High School Athletics (Added 2026-02-21)

### MaxPreps Integration

Added MaxPreps scraper for Santa Rosa area high schools. The scraper parses `__NEXT_DATA__` JSON from MaxPreps pages to extract upcoming sports events.

| School | MaxPreps Key | Events | Notes |
|--------|--------------|--------|-------|
| Santa Rosa High | `santa-rosa-panthers` | ~2 | Varsity basketball, soccer |
| Montgomery High | `montgomery-vikings` | ~2 | Varsity basketball, soccer |
| Maria Carrillo High | `maria-carrillo-pumas` | ~2 | Various varsity sports |
| Piner High | `piner-prospectors` | ~1 | Limited events |
| Elsie Allen High | `elsie-allen-lobos` | 0 | No upcoming events currently |
| Cardinal Newman High | `cardinal-newman-cardinals` | ~4 | Private school; baseball, lacrosse, soccer, basketball |

**Note:** Event counts vary by season. Spring sports (baseball, softball, track, lacrosse) typically have more events than winter playoffs.

### Not Added

| School | Reason |
|--------|--------|
| Windsor High | 0 upcoming events |
| Healdsburg High | 0 upcoming events |
| Sonoma Valley High | Outside Santa Rosa city limits |

### Middle Schools

Middle school athletics are not tracked on MaxPreps. The district (SRCS) does not publish a public calendar for middle school sports.
---

## Rediscovery Pass (2026-07-17)

Six-lane agent fan-out (Meetup refresh, platform sweeps with the post-2025 toolbox, directory cross-reference, faith/civic/seniors, dead-end re-litigation + feed health, Phase 4 upstream authority). 22 feeds + 14 scrapers wired; details below. Includes the two revived srcity.org feeds (`santarosa-srcity-revived-feeds` item): Courthouse Square Events (catID=52, 54 events — food trucks, festivals, tree lighting) and Recreation & Parks (catID=31, 10 — park volunteer days). The feeds went stale in 2025, were removed, and are maintained again; Main Calendar and board categories deliberately skipped (Legistar covers meetings). Issuu activity guide and ActiveNet confirmed non-starters (seasonal print PDF; API unlicensed, classic UI serves the SPA shell).

### Added — live feeds (22)

| Source | Type | Events | Notes |
|---|---|---|---|
| Congregation Beth Ami | Google Calendar ICS | 613 future | UA note: works with the full pipeline UA string; bare "CommunityCalendar/1.0" returns empty |
| Sebastopol Calendar | Tribe ICS | 30 | Community aggregator for Sebastopol — in source_priority.json |
| Center for Spiritual Living Santa Rosa | Tribe ICS | 30 | Their Meetup was 0-event; the website feed is live |
| Children's Museum of Sonoma County | Tribe ICS | 18 | Was aggregator-only (13 events via aggregators) |
| Healdsburg Community Events | CivicPlus catID=33 | 56 | catID=14 (Main) skipped: gov-meeting noise |
| Town of Windsor | CivicPlus catID=14 | 10 | |
| Rohnert Park City Events | CivicPlus catID=29 | 12 | Party on the Plaza concert series |
| Redwood Cafe | existing `redwood_cafe.py` HTML scraper (wired 2026-07-17, was orphaned) | 19 | The My Calendar ICS added earlier this pass has BROKEN per-event URLs (`/mc-events/` pages render empty — venue theme lacks the template); remove BOTH that ICS feed AND the 0-event Songkick interim via Manage Feeds. The HTML scraper links to the working `/events/` page and captures showtimes |
| Sonoma County DSA | Google Calendar ICS (new at socodsa.org) | 59 future | REPLACEMENT — old gcal deleted (404); remove old feed via Manage Feeds |
| Gundlach Bundschu Winery | Tribe ICS | 10 | Ani DiFranco-tier concerts |
| Mark West Area Chamber | Tribe ICS | 5 | |
| Russian River Brewing (Windsor) | Tribe ICS (slug `/the-events-calendar/`) | 3 | |
| + 10 Meetup groups | Meetup ICS | ~60 | Contra dance, book clubs, pool league, healing, woodworking, kayaking (2025's 0-event group now live), PlayYourCourt tennis, Unstruck Drum |

### Added — scrapers (14)

| Source | Scraper | Events (test) | Notes |
|---|---|---|---|
| Visit Santa Rosa | `visit_santa_rosa.py` (new) | 271 | **Formerly a non-starter** — public Algolia creds embedded in page JS, extracted at runtime. AGGREGATOR. The Metro Chamber Algolia index (262) is a near-duplicate — deliberately not added |
| ~~Sonoma Valley Events~~ | ~~`gatherboard.py`~~ | 594 at add | **REMOVED 2026-08-07 by owner decision** — site has a history of rejecting our probes; workflow line, DB row, and events all removed. Do not re-add without owner sign-off (see Reconciled section) |
| Sonoma Community Center | `tribe_rest.py` | 457 | Site redesign 404'd the Tribe ICS; REST API alive. Remove the dead `?ical=1` feed via Manage Feeds |
| Santa Rosa Symphony | `santa_rosa_symphony.py` (new) | 10 | Tribe ICS/REST dead; admin-ajax card backdoor. KNOWN LIMITATION: cards carry no times — events emit at 00:00; follow-up could fetch detail pages |
| Raven Performing Arts Theater | `thundertix.py` (new, parameterized) | 7 | ThunderTix ItemList JSON-LD |
| The California (Cal Theatre) | `cal_theatre.py` REPAIRED | 20 | Was 0 ("Wix may require JavaScript") — events still in `wix-warmup-data` embedded JSON |
| Little Saint (Healdsburg) | `dice_venue.py` | 22 | Only DICE venue in scope (city sweep: all other towns 0); not on Songkick |
| Sebastopol Chamber of Commerce | `growthzone.py` | 27 | Live-music-heavy chamber; Windsor + Healdsburg chambers skipped (member-meeting noise) |
| Sonoma County Board of Supervisors | `legistar.py --client sonoma-county` | 7 | Only body on the county's Legistar |
| Windsor / Analy / Rancho Cotate / Healdsburg HS Athletics | `maxpreps.py` ×4 | 3–6 each | Fall seasons starting; El Molino 0 (recheck Sep) |

### Feed health flags (2026-07-17 audit: 27 live feeds, 16 healthy)

- **Remove via Manage Feeds dialog:** old Sonoma County DSA gcal (deleted, 404), The Big Easy Tribe ICS (site replatformed to Astro/Vercel; Songkick scraper still covers), Meetup `sonoma-county-go-wild-hikers` + `sonoma-county-boomers` (groups deleted), Redwood Cafe Songkick (superseded above), Sonoma Community Center `?ical=1` (404; tribe_rest scraper supersedes)
- **UA-gated (WAF-exception ask per curator-guide, or accept loss):** Luther Burbank Center, Uptown Theatre Napa — both 403/202-challenge the pipeline UA; browser UA gets 30 events each
- **Stale:** sonoma.com feed serves only past events while its HTML shows future ones — watch; scrape HTML if it persists
- **PIPELINE ANOMALY:** GoLocal Cooperative feed serves 28 future VEVENTs to the pipeline UA, but 0 events land in the DB — investigate download/combine side, not the source
- Dormant-not-dead: Meetup womens-creativity-collective (445 members, 0 upcoming) — keep watching

### Needs Scraper (new bench from this pass)

| Source | Approach | Volume | Notes |
|---|---|---|---|
| Napa County Library | Communico/libnet (events.napalibrary.gov) | 54–73 via aggregators | Largest remaining gap; JS widget, BiblioCommons API 403 |
| Sonoma Botanical Garden | Veevart ticketing API | 41 via aggregators | |
| Downtown Santa Rosa | ctykit CityCMS listing→detail (`dldate`/`dltime`) | 65 | Overlaps Visit SR + Barrel Proof; build only if gaps show |
| Eventbrite city listing | browser-header fetch + JSON-LD ItemList | 47 | Replaces retired Eventbrite scraper; bot-fragile — revisit if wanted |
| THE 222 | EventON server-rendered HTML (REST disabled) | 8 via Creative Sonoma | |
| Blue Note Napa | bluenotejazz.com/napa/shows/ HTML | ~15 | Songkick interim carries 1 |
| Sugarloaf Ridge State Park | Eventbrite organizer discovery | 11 via aggregators | Site is a JS shell |
| Santa Rosa Symphony times | fetch detail pages for showtimes | — | Removes the 00:00 limitation |

### Fall rechecks

El Molino HS MaxPreps (0, off-season) · Sonoma State Sidearm athletics (2026-27 schedules unpublished; `sidearm.py` ready) · 30+ dormant Meetup groups (list in lane report)

### Non-starters confirmed this pass

Barrel Proof Lounge scraper dead (27 aggregator-only events — repair or retire, investigate separately) · SR City Schools (Finalsite `calendarsEnabled=false`) · Windsor/Mark West/Rincon Valley/Bellevue/Piner-Olivet/Roseland USDs (PDF or Cloudflare) · sonoma.edu + events.sonoma.edu (Cloudflare/dead) · Sebastopol city (`rg-event`, no export) · 6th Street Playhouse (JS SPA, no Ludus/OvationTix API) · Cotati CivicPlus (3 sparse) · Windsor + Healdsburg chambers (member-meeting noise) · Farm Trails, LandPaths, Habitat SoCo, Sonoma Land Trust, seb.org (Cloudflare/captcha-class blocks) · ShulCloud (Shomrei Torah), Church Center (Spring Hills, New Vintage), Wix faith/civic sites (no exports) · Oakmont Village (member-gated) · Rotary Sunrise ClubRunner (internal events) · Bandsintown (still 403) · Trumba/TeamUp/LibCal/guild.host area sweeps empty · DICE: no venues beyond Little Saint

## Clean pass (2026-08-07)

Source-health soak (`reports/santarosa-2026-08-07-soak.md`) plus the executed
fixes. Local audit and the same-day GitHub run agreed on producer set,
failures, and zero-event roster before these changes.

### Retired

- **Cafe Frida** — venue rebranded: `cafefridagallery.com` now redirects to
  `cafelittledeer.com`, which has no public events page (only
  private-event booking; checked 2026-08-07). `/events` 404s locally and in
  Actions. Scraper `scrapers/cafefrida.py` deleted, workflow line removed,
  DB row (id 351) marked removed. Mondavi/Davis-Chamber pattern.
- **New World Ballet** — DB scraper row (id 416) had no command and no
  producer; marked removed.
- **North Bay Derby duplicate** — malformed DB row (id 822) keyed on the
  page URL instead of an output path (the feed downloader saved 596KB of
  HTML as an "ics"); marked removed. The real
  `squarespace_northbayderby.ics` row (id 1101) is untouched.

### Repaired

- **Spreckels Performing Arts Center** — Tribe REST API 404s after the 2026
  site redesign; `scrapers/spreckels.py` rewritten against the Divi
  server-rendered `/show/<season>-season/<slug>/` pages (Arts People
  ticketing). Season slug supplies the year (Aug–Dec → first year, Jan–Jul
  → second). No per-performance times exposed — all-day run ranges, like
  the Santa Rosa Symphony 00:00 limitation. 6 shows parsed on rewrite day.
- **Cinnabar Theater** — `_parse_date_range` extended for abbreviated
  months with periods and comma-less years ("Sept. 18 – Oct. 4 2026",
  "April 9 – 25 2027"); cross-year ranges ("Dec. 19 – Jan. 4") now roll the
  end year. All 4 current-season shows parse (2 within the 6-month
  horizon).

### Executed the 2026-07-17 "Remove via Manage Feeds" flags (production `remove_feed` path: events delete + feed hard-delete)

- old Sonoma County DSA gcal (id 392; feed served a Google 404 page) — new
  socodsa.org gcal (id 1055) remains
- Meetup: Go Wild Hikers (id 403) and Meetup: Sonoma County Boomers
  (id 410) — groups deleted
- The Big Easy Tribe ICS (id 402) — replatformed site, past-only events;
  Songkick scraper covers
- Redwood Cafe My Calendar ICS (id 1060) and Songkick interim (id 381,
  workflow line also removed) — first-party `redwood_cafe.py` (id 1071) is
  the sole producer
- Sonoma Community Center `?ical=1` (id 398) — `tribe_rest.py` scraper
  supersedes
- Santa Rosa Symphony `?ical=1` (id 399) — `santa_rosa_symphony.py`
  scraper supersedes

### Reconciled

- **Sonoma Valley Events** (id 1066) — row was `status=removed` while the
  workflow still ran it (451+ events/run); removal judged accidental
  against this checklist's 2026-07-17 record, set back to `active`.
  **REVERSED later on 2026-08-07 by owner decision — REMOVED for good.**
  The DB `removed` status had been deliberate: sonomavalleyevents.com has
  a history of rejecting our probes, and the owner chose to drop the
  source rather than keep an intermittently-hostile aggregator. The
  same-day reactivation (made before that intent was known) was undone:
  workflow line removed, 333 events deleted, feed row 1066 hard-removed
  via `remove_feed`, `feeds.txt` re-exported (106 rows). Do NOT
  re-reconcile this source back to active in future clean passes — the
  removal is intentional even though the site may answer probes on any
  given day.
- **Sonoma County Board of Supervisors** (id 1054) — `scraper_cmd`
  normalized to the workflow form (`--source` + `--output`).
- `feeds.txt` re-exported from the DB (107 rows).

### Adjudicated 2026-08-07 (display names, A004 — resolved)

- The 6 MaxPreps workflow lines gained explicit `--name "<School> High
  School Athletics"` flags matching the DB display names, and the DB
  `scraper_cmd` rows were synced to the new commands.
- `scrapers/santa_rosa_arts_center.py` and `scrapers/movingwriting.py`
  now emit stable `X-WR-CALNAME` values ("Santa Rosa Arts Center",
  "MovingWriting") instead of month-stamped titles — the "- 2026/08"
  artifacts are gone at the source.
- Post-fix `--sync-existing --dry-run` is fully clean: 63/63 rows,
  0 updates, 0 retirements, 0 weak-name skips.

### Adjudicated 2026-08-07 (A007 review queue — user decisions)

- **Barrel Proof Lounge — REPAIRED.** Site alive; the 2026 redesign moved
  events to `/events/`, whose Widget-for-Eventbrite FullCalendar embeds the
  full list as an inline `var wfea_events_N = [...]` JSON array.
  `scrapers/barrel_proof.py` rewritten to parse that array (was scraping
  homepage widget blocks that no longer carry events). 291 events on the
  repair-day run (was 0). Workflow line unchanged (already runs
  `barrel_proof.py`).
- **Sweetwater Music Hall — REPAIRED.** First-party RSS + JSON-LD scraper
  emitted 0 under Python 3.10 because every event page's JSON-LD
  `startDate` carries a colon-less UTC offset (`...T20:00:00-0800`), which
  3.10's `datetime.fromisoformat` rejects (3.11+ accepts it) — so every
  event hit the "bad startDate" skip. Added `_normalize_iso` to insert the
  offset colon (and map `Z`). 33 future events now parse (was 0). The
  Songkick duplicate (`songkick_sweetwater.ics`, id 367) stays by user
  decision — dedup reconciles.
- **Luther Burbank Center + Uptown Theatre Napa — converted to
  `tribe_rest` scrapers (final user adjudication 2026-08-07), with the WAF
  reality documented.** The Tribe REST APIs return real JSON (LBC `total`
  43, Uptown 35) reliably only to a real browser: SiteGround answers
  `requests`/`curl` with a `202` JavaScript proof-of-work challenge, then
  a hard `403` block page even after the PoW is solved in code (SHA1,
  complexity 21, ~1.45M hashes, `_I_` pass cookie issued — the homepage
  itself still `403`s), and the identical block produced 0 events for both
  `?ical=1` feeds in the same-day GitHub run. The user chose conversion
  anyway, matching the toronto/raleighdurham precedent: on blocked days
  the scraper writes a valid empty calendar (audits read "quiet", not
  "broken" `not_ics`), and any WAF relenting harvests events. Old feed
  rows removed via `remove_feed` (LBC id 393, Uptown id 400, both 0
  events); new scraper rows inserted via the reviewed sync; workflow lines
  carry `--user-agent "Mozilla/5.0"`. The real fix for reliable coverage
  remains a venue-side WAF allowlist ask (per the 2026-07-17 curator-guide
  note) or a headless-browser scraper harness — **that part stays open.**
- **Deliberately kept, watching (no change):** Sonoma County AA empty feed,
  sonoma.com past-only staleness, Santa Rosa Arts Center (quiet, no
  errors), and the 9 quiet Songkick venues (Elephant/Will Call/Rancho
  Nicasio/Big Easy/Twin Oaks/Fern Bar/Shady Oak/THE 222/HenHouse — valid
  but no current listings). Sonoma Community Center REST stays productive
  locally but quiet in Actions (possible datacenter-IP gating) — watch.
