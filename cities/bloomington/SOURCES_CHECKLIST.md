# Bloomington Calendar Source Checklist

Prioritized list of potential event sources for the Bloomington, IN community calendar.

## Currently Implemented (77 sources)

### University — IU LiveWhale (17 feeds)

| Source | Group ID | Events | Notes |
|--------|----------|--------|-------|
| IU Jacobs School of Music | 56 | ~514 | |
| IU Auditorium | 378 | ~23 | |
| Eskenazi Museum of Art | 234 | ~74 | |
| IU Cinema | 81 | ~19 | |
| IU La Casa Latino Cultural Center | 59 | ~109 | |
| IU Maurer School of Law | 64 | ~80 | |
| IU Kelley School of Business | 343 | ~48 | |
| IU Arts & Humanities Institute | 130 | ~183 | |
| IU Bloomington Libraries | 261 | ~436 | |
| IU Theatre & Dance | 218 | ~20 | |
| IU Asian Culture Center | 314 | ~26 | |
| IU First Nations Center | 275 | ~14 | |
| IU LGBTQ+ Culture Center | 237 | ~4 | |
| IU Black Film Center & Archive | 221 | ~9 | |
| IU Neal-Marshall Black Culture Center | 235 | — | Seasonal |
| IU Hamilton Lugar School | 135 | — | Global & International Studies |
| IU Eskenazi School of Art | 11 | ~94 | Exhibitions, lectures, MFA shows |

Feed URL pattern: `https://events.iu.edu/live/ical/events/group_id/{id}`
Docs: https://documentation.events.iu.edu/feed-and-linked-calendars/ical-feed.html

### University — Other IU Platforms (3 feeds)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| IU Moving Image Archive | LibCal `cid=5914` | ~151 | |
| IU Scholars' Commons | LibCal `cid=1228` | ~26 | |
| IU Athletics | Sidearm | ~82 | `sidearm.py` — v3 Calendar API, home-site games only |

### City & Civic (4 feeds)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| City of Bloomington | Google Calendar | ~374 | |
| City Boards & Commissions | Google Calendar | — | |
| City Department Events | Google Calendar | — | |
| Parks and Recreation | Google Calendar | ~1615 | Concerts, fitness, nature, family events |
| Bloomington Farmers Market | Google Calendar | ~307 | |

### Music & Performing Arts (7 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| The Bluebird | Songkick | ~9 | `songkick.py` venue 78904 |
| Blockhouse Bar | Songkick | ~2 | `songkick.py` venue 3607354 |
| Buskirk-Chumley Theater | Scraper | ~32 | `buskirk_chumley.py` |
| The Bishop | Scraper | ~4 | `the_bishop.py` (SSL verify=False, cert expired 2026-03) |
| The Comedy Attic | Scraper | ~32 | `comedy_attic.py` |
| Constellation Stage & Screen | Scraper | ~45 | Spektrix API — `constellation.py` |
| Brown County Playhouse | ICS | ~12 | WordPress Events Calendar |

### Arts & Culture (8 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Pillar Arts Community Calendar | ICS | ~62 | Tockify API feed; includes Pillar Arts Alliance Center + Pillar Arts By Hand events |
| FAR Center for Contemporary Arts | Scraper | ~4 | `far_center.py` — Craft CMS |
| Cicada Cinema | Scraper | ~6 | Shopify products API — `cicada_cinema.py` |
| Pottery House Studio | Scraper | ~40 | Squarespace — `squarespace.py` workshops |
| Monroe County History Center | Scraper | ~17 | `monroe_county_history_center.py` — EventON WP REST API; behind SiteGround sgcaptcha (plain-Mozilla UA) |
| Gallery at the Vault | Eventbrite scraper | ~5 | Gallery events, 205 N College Ave |
| Keplinger Institute for Wellness and Art | Eventbrite scraper | ~2 | Massage CE classes, Wellness Through Art |
| Bloomington Old-Time Music & Dance | Google Calendar | — | |

### Literary (4 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Writers Guild at Bloomington | Scraper | ~7 | `writers_guild.py` — Sugar Calendar |
| Morgenstern Books | Eventbrite scraper | ~9 | Author events, book clubs |
| Redbud Books | Google Calendar | ~348 | Book clubs, author talks, film, community events |
| Nerd Nite Bloomington | Eventbrite scraper | ~1 | Quarterly science talks at The Bishop |

### Community & Family (8 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Monroe County Public Library | ICS | ~500 | Communico/Stacks partner portal `mcplin.libnet.info/feeds` (was `calendar.mcpl.info`; see 2026-10-09 repair) |
| Boys & Girls Club | Scraper | ~2 | `tribe_rest.py` — Tribe ICS returns empty reply; REST API works (2026-08) |
| First United Church | ICS | ~50+ | WordPress ICS — community hub (DSA, Al-Anon, scouts) |
| Bloomington Community Band | Scraper | ~5 | `tribe_rest.py` — Tribe ICS returns an empty body; REST API works (2026-08) |
| Bloominglabs Makerspace | Google Calendar | ~10+ | |
| Habitat for Humanity Monroe County | Scraper | ~4 | `habitat.py` — fundraisers, 5K, volunteer events |
| Reviving Hope for the Nations | Eventbrite scraper | 0 current | Faith/community events |
| Bloomington Spinners & Weavers Guild | ICS | — | |

### Nature & Outdoors (6 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Sassafras Audubon Society | Scraper | ~31 | Squarespace — `sassafras_audubon.py` |
| Monroe County Master Gardeners | Scraper | ~62 | Squarespace — `master_gardeners.py` |
| Sycamore Land Trust | Scraper | ~131 | WordPress — `sycamore_land_trust.py` |
| McCormick's Creek State Park | Localist scraper | ~88 | `localist.py` — events.in.gov venue 35217665860404 (13 mi) |
| Brown County State Park | Localist scraper | ~47 | `localist.py` — events.in.gov venue 35217662417669 (17 mi) |
| Knobstone Hiking Trail Meetup | ICS | ~10 | Meetup group — regional hiking |

### Interest Groups & Civic (7 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Bloomington Atheists Meetup | ICS | ~10 | Meetup group |
| Bloomington Bicycle Club | Google Calendar | ~5023 | Cycling rides, weekly events |
| Bloomington Velo Club | Google Calendar | — | |
| Hoosier Fly Fishers | ICS | — | |
| Indivisible Central Indiana | Scraper | ~21 | `mobilize.py` — civic/political organizing |
| The Afrobellas At IU | Eventbrite scraper | ~1 | IU student org events |
| Falun Dafa Club at IU | Eventbrite scraper | ~1 | IU student org practice sessions |

### Food & Beverage (9 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Cardinal Spirits | Scraper | ~5 | Squarespace — `cardinal_spirits.py` |
| The Tap | Eventbrite scraper | — | Live music, craft beer events |
| Big Red Liquors | Eventbrite scraper | 0 current | Tastings/events |
| Blueline Bloomington | Eventbrite scraper | 0 current | Restaurant/bar events |
| Martinsville Arts Council | Eventbrite scraper | ~6 | Community theater in Martinsville (20 mi) |
| Story Inn | Eventbrite scraper | — | Seasonal: wine fairs, comedy, music in Story (17 mi) |
| Hard Truth Distilling Co. | Scraper | ~15 | `tribe_rest.py` — TEC site behind SiteGround sgcaptcha (ICS + REST APIs challenged); plain-Mozilla UA; Nashville, IN (16 mi) |
| Upland Brewing | Scraper | 0 current | `tribe_rest.py` — valid REST calendar, dormant/seasonal as of 2026-08 |
| People's Market | Scraper | ~10 | Squarespace — `peoples_market.py` |

### Tourism & Visitor Events (1 source)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Visit Bloomington | Scraper | ~484 | `visit_bloomington.py` — Simpleview REST API (`/includes/rest_v2/plugins_events_events_by_date/find/`). Primary source, deliberately **not** an aggregator (ADR 0011): it outranks the Limestone Post echo in cross-source dedup |

Visit Bloomington is pulled in full over the REST API (token + `skip` paging, Chrome UA, crawl-delay spacing). The sitemap fallback is a **contingency only**, triggered when either the API returns non-200 on **three consecutive nightly runs after** the in-run token re-fetch and retry, or the documented-safe request shape draws a WAF 403. Until then, the REST API is the source.

### Aggregators (11 sources)

These curate or aggregate events from multiple venues:

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| WFHB Community Calendar | Scraper | ~393 | `wfhb_calendar.py` — Events Manager (`lib/em_events.py`), occurrence-expanded; covers Orbit Room, library events, and many venues not otherwise scrapable |
| WFIU Community Calendar | Scraper | ~667 | `wfiu_community_calendar.py` — Brightspot server-rendered HTML; occurrence-expanded regional community calendar (Bloomington + surrounding towns) |
| BloomingtonOnline: Events | Google Calendar | ~224 | Community events |
| BloomingtonOnline: Food & Drink | Google Calendar | ~133 | Restaurant/brewery specials |
| BloomingtonOnline: Shopping | Google Calendar | ~18 | Markets, deals |
| Let's Go! Bloomington | Google Calendar | — | Indie venues, shows, art openings |
| BloomingtonArts.Today | Scraper | ~115 | Hand-curated arts calendar; 88% overlap with authoritative feeds |
| Brown County Events | ICS | ~94 | browncounty.com CVB — aggregates Nashville/Brown County venues |
| B-Square Bulletin (4 feeds) | Google Calendar | ~9162 | Government, misc civic, Critical Mass, BPTC meetings (mostly historical, future-filtered) |
| IU beINvolved Student Orgs | ICS | ~16900 | CampusLabs — all student org events campus-wide |
| Limestone Post | CitySpark scraper | ~488 | Community aggregator; 29% overlap with existing, 344 unique events (sports, trivia, gallery, faith) |

### Ticketmaster Venues (8 sources)

| Source | Venue ID | Events | Notes |
|--------|----------|--------|-------|
| IU Musical Arts Center | KovZpaoDke | ~15 | Opera, ballet, orchestral |
| IU Cinema | KovZpZAI11nA | ~31 | Film screenings |
| Brown County Music Center | KovZ917AOr1 | ~27 | Nashville, IN (17 mi) |
| IU Memorial Stadium | KovZpZAFdInA | ~4 | Football, concerts |
| Ruth N Halls Theatre | KovZpZAdE6aA | ~8 | Theatre, dance |
| Bill Armstrong Stadium | KovZpaoDQe | ~5 | Soccer, events |
| Wells Metz Theatre | KovZpZAF7JFA | ~4 | Theatre |
| Simon Skjodt Assembly Hall | KovZpZAFdItA | ~2 | Basketball, concerts |

### Other (3 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Lotus Festival | ICS | ~7 | WordPress Events Calendar |
| Indiana State Events | ICS | — | `events.in.gov` |
| Utilities Service Board | Google Calendar | — | Board meetings |

---

## Dead Ends & Non-Starters

### Blocked / No Feed

| Source | Platform | Reason |
|--------|----------|--------|
| Amplify Bloomington | WordPress + Cloudflare | Cloudflare blocks all endpoints (ICS, REST API, RSS); request whitelisting of `?ical=1` |
| Winter Farmers' Market | Wix | No ICS export |
| Gallery Walk Bloomington | Wix | No feed; recurring first Friday 5-8pm |
| BARA (runners) | Wix | No ICS export |
| Bloomington PRIDE | Squarespace | No ICS export |
| ~~Bloomington Brewing Co~~ | RESOLVED 2026-08-03: dedicated scraper (`bloomington_brewing.py`) — see Discovered 2026-07-17 |
| Bloomington Yoga Collective | Squarespace + MindBody | Class schedules only |
| Vibe Yoga Studio | Squarespace | Class schedules only |
| Bloomington Volunteer Network | Galaxy Digital | No feed export |
| NAMI Greater Bloomington | The Events Calendar + Cloudflare | Tribe REST API 403s from CI (Cloudflare IP/WAF block on GitHub Actions egress); dropped as a source 2026-09 (#19) |
| WonderLab Museum | The Events Calendar + Cloudflare | Whole host behind Cloudflare bot protection: ICS and Tribe REST API both 403 from CI for every UA; dropped as a source 2026-10 (#186). Events covered by WFIU Community Calendar, Visit Bloomington, Pillar Arts |
| SIREN Solar | Tribe Events Calendar | ICS broken, API returns 0 events — dead calendar |
| ~~Pillar Arts~~ | ~~WordPress + TEC~~ | RESOLVED: events published via Pillar Arts Community Calendar Tockify feed (bloomington.arts.calendar) |
| Monroe County Gov | Indiana state platform | No ICS export |
| MCCSC School Calendar | ParentSquare | Old URL 404 |

### No Calendar / Social Media Only

| Source | Reason |
|--------|--------|
| Juniper Art Gallery | Shopify, no calendar feed; some events covered by WFHB |
| Backspace Gallery | Square site, no events page; some events covered by WFHB |
| Windfall Dancers | WordPress, class schedules as plain text |
| Time & Tide Tattoo | Flash events on Instagram/Facebook only |
| Indiana Dance Company | Class schedules only |
| MotionArts Dance Academy | Class schedules only |
| Yoga Mala | Google Calendar page is 404 |

### Derivative / Duplicate

| Source | Reason |
|--------|--------|
| Bandsintown Bloomington | Derivative, duplicate-heavy |
| Herald-Times Events | Derivative aggregator |
| Indiana Daily Student Events | No ICS feed; derivative |

### Inactive / Suspended

| Source | Reason |
|--------|--------|
| WCLS 97.7 | Site suspended |
| ~~The Back Door (Tockify)~~ | RESOLVED 2026-07-17: ICS export now enabled — see Ready to Add |
| Chamber of Commerce Atlas | No ICS; UPDATE 2026-07-17: WebLink/Atlas JSON API exists (api-internal.weblinkconnect.com) behind auth — needs scraper if wanted |
| Bloomington Board Games Meetup | 403 private |
| Bloomington Remote Workers Meetup | Dormant |

### Low Priority

| Source | Reason |
|--------|--------|
| UU Church of Bloomington | Planning Center (no public API); events mostly internal |
| Friends Meeting | Squarespace; calendar behind member-only page |
| Neighborhood Associations | Sites appear inactive/minimal events |
| Bloomingtonian | Community blog, low volume |
| NUVO | Regional, derivative |
| Do317 | Indy-centric |

---

## Discovered 2026-07-17 — Ready to Add (tested feeds)

Refresh pass, 8 lenses (see Discovery Run Log). All feeds below fetched and verified live on 2026-07-17.

### Direct wins (incl. Phase 4 upstream-authority graduates)

| Source | Events | URL | Notes |
|--------|--------|-----|-------|
| The Back Door | 268 | `https://tockify.com/api/feeds/ics/thebackdoor` | Was "ICS disabled" dead end — now enabled. 32 aggregator-only events graduate to direct. Queer bar: drag, karaoke, line dancing, trivia |
| Brown County Art Guild | 3 now | `https://browncountyartguild.org/events/?ical=1` | WordPress/TEC; ModSecurity requires browser UA (`Mozilla/5.0 ... Chrome`). 87 aggregator-only events — feed sparsely populated at test time, worth adding + watching |
| Brown County Inn | 260 | `https://www.browncountyinn.com/events-2/?ical=1` | WP Events Plugin; Nashville IN |
| Art Sanctuary (Martinsville) | 168 | `https://calendar.google.com/calendar/ical/artsanctuaryindiana%40gmail.com/public/basic.ics` | Google Cal embed on artsanctuaryindiana.com |
| Monroe Lake / Cutright SRA (DNR) | 138 | `https://events.in.gov/monroe_lake_296/calendar.ics` | Localist; covers Cutright + other Monroe Lake SRAs |
| Butler Winery | 35 | `https://butlerwinery.com/?post_type=tribe_events&ical=1&eventDisplay=list` | Tribe iCal; Sunday live music, trivia, yoga |
| Town of Ellettsville (CivicPlus) | 205 | `https://ellettsville.in.us/egov/apps/events/calendar.egov?view=ical` | Gov meetings + parks events |
| Morgan County government (CivicPlus) | 73 | `https://morgancounty.in.gov/egov/apps/events/calendar.egov?view=ical` | Martinsville; county meetings + notices |
| Monroe County Fairgrounds | 344 | `https://calendar.google.com/calendar/ical/mocofairgrounds%40gmail.com/public/basic.ics` | Master calendar: fair, 4-H, year-round venue events (gun shows, markets). Fills the fairgrounds gap; 7 more public sub-calendars exist |
| Monroe County 4-H / Purdue Extension | 386 | `https://calendar.google.com/calendar/ical/mocoin4h%40gmail.com/public/basic.ics` | Club meetings, fair prep, camps; embedded at extension.purdue.edu/county/monroe |

### Faith communities (volume caveat: congregation-wide calendars mix public events with internal meetings/worship — curator judgment on filtering)

| Source | Events | URL | Notes |
|--------|--------|-----|-------|
| First Christian Church (Disciples) | 772 | `https://calendar.google.com/calendar/ical/mjsnm57lcjgbhseu4lj9ee704k%40group.calendar.google.com/public/basic.ics` | Concerts, forums, blood drives |
| Trinity Episcopal | 262 | `https://calendar.google.com/calendar/ical/48ac7e6a73bd950b28dea0eca41b3050858f0c4f00ddfbd78dd23a2a9e5fc51d%40group.calendar.google.com/public/basic.ics` | Country Dance Nights, organ recitals — strong public-interest content |
| First Presbyterian | 4,062 | `https://calendar.google.com/calendar/ical/fpcbloomington.org_soip8veg9uk3hvpo3oj19bc5tg%40group.calendar.google.com/public/basic.ics` | High volume |
| St. Charles Borromeo (Catholic) | 10,924 | `https://calendar.google.com/calendar/ical/calendar%40stcharlesbloomington.org/public/basic.ics` | Very high volume, heavy internal content — filter before adding |
| Sanshin Zen Community | 1,282 | `https://calendar.google.com/calendar/ical/sanshinji.org_3q9maq1gaa99bpu6da81ibrl7g%40group.calendar.google.com/public/basic.ics` | Practice schedule + retreats |
| Ellettsville Church of Christ | 211 | `https://www.ellettsvillechurchofchrist.com/about/calendar/ical` | Native ICS; mostly worship schedule |

### Ticketmaster venues (new IDs; run through the TM key to verify upcoming-event counts before adding — TM keeps pages for defunct venues)

| Venue | ID | Notes |
|-------|-----|-------|
| IU Auditorium | 41148 | Major performing-arts venue, separate from Musical Arts Center |
| Buskirk-Chumley Theatre | 41477 | Already covered by custom scraper — TM feed is a dedupe/complement question |
| IU Studio Theatre | 42040 | May overlap with T300 below — verify |
| T300 Studio Theatre | 41153 | |
| IU Tailgate Field | 41923 | Sporadic special events |
| Little Nashville Opry | 41458 | ⚠️ venue burned down 2009, never rebuilt — likely stale TM page; verify before adding |
| John R. Wooden Gymnasium (Martinsville) | 41902 | |
| CenterBrook Drive-in (Martinsville) | 42223 | Sporadic |

### High-school athletics (existing `scrapers/maxpreps.py` takes these as `--url https://www.maxpreps.com{slug}events/` — no new code)

| School | MaxPreps slug |
|--------|---------------|
| Bloomington North Cougars | `/in/bloomington/bloomington-north-cougars/` |
| Bloomington South Panthers | `/in/bloomington/bloomington-south-panthers/` |
| Edgewood Mustangs (Ellettsville) | `/in/ellettsville/edgewood-mustangs/` | 
| Owen Valley Patriots (Spencer) | `/in/spencer/owen-valley-patriots/` |
| Martinsville Artesians | `/in/martinsville/martinsville-artesians/` |
| Brown County Eagles (Nashville) | `/in/nashville/brown-county-eagles/` |
| Eastern Greene Thunderbirds | `/in/bloomfield/eastern-greene-thunderbirds/` |
| Lighthouse Christian Academy Lions | `/in/bloomington/lighthouse-christian-academy-lions/` |

Edgewood alone shows 84 aggregator-only events today. Also: third-party IU football ICS at `https://ics.calendarlabs.com/2134/a7e56915/Indiana_Hoosiers_Football_Schedule.ics` (valid VCALENDAR; unofficial source — caveat emptor).

## Discovered 2026-07-17 — Needs Scraper

### Bench build results (2026-07-17 evening pass)

**Built and wired (12 scrapers + 4 feeds, ~150 events verified in test runs):**

| Source | How | Events (test) | Notes |
|--------|-----|--------------|-------|
| The Orbit Room | `dice_venue.py` (from Asheville pass) | 8 | Venue's own domain is dead; DICE partner API. B-Square note: `dice_venue.py` requires upstream sync — not in their fork yet |
| Brown County Government | `brown_county_gov.py` (new) | 82 | The simple CivicPlus GET (`?catID=14&feed=calendar`) works — no form POST needed |
| Owen County Public Library | `owen_county_library.py` (new) | 14 | Payload CMS JSON; Lexical rich-text parsed |
| Off Night Productions | `ludus.py` (new, parameterized) | 12 | Ludus needs full browser client-hint headers past Cloudflare; scrape `<sub>.ludus.com/index.php`, not `/` |
| Monroe County Civic Theater | `ludus.py` | 7 | Cyrano Sep 4–13 |
| Bloomington Symphony Orchestra | `bloomington_symphony.py` (new, lib/tribe_events subclass) | 6 | **bloomingtonsymphony.COM** (Tribe REST); the `.org/concert/` from discovery is the Bloomington MINNESOTA symphony. Recovers showtime from all-day titles. 4 of 6 at Buskirk-Chumley — dedup overlap expected |
| Monroe Convention Center | `simpleview.py` (new, parameterized RSS→JSON-LD) | 4 | All-day events with proper multi-day DTEND |
| Visit Morgan County | `simpleview.py` `--towns Martinsville` | 12 | Tourism aggregator (added to source_priority.json); Mooresville/Monrovia filtered out (outside radius) |
| Tibetan Mongolian Buddhist Cultural Center | `tmbcc.py` (new) | 1 | Events as blog-post titles; wp-json bypasses mod_security; precision-first (10/10 posts handled right) |
| Bloomington Brewing Co. | `bloomington_brewing.py` (new) | 0 seasonal | Per-event Squarespace ICS from sitemap (correct domain: bloomingtonbrew.com); populates at next festival |
| Gaden KhachoeShing Monastery | `eventbrite.py` | 0 blocked | Organizer page CAPTCHA-gated locally; wire-and-wait for CI |
| Exodus Refugee Immigration | `eventbrite.py` | 0 expected | Wire-and-wait per plan; re-probe near World Refugee Day |
| Edgewood School District / High School / Junior High | Finalsite direct ICS (calendar_ids 7 / 3 / 11) | 102 / 103 / 499 | The Asheville Finalsite URL pattern works on rbbschools.net; athletics IDs 8/12 skipped (MaxPreps covers) |
| Monroe County Democratic Party | Google Calendar ICS (adopted from B-Square's feeds table) | 204 | The only feed in their table we lacked (Chronically Dave is their curator's my-picks feed — fork-local; Ellettsville Town Gov we already had) |

**Resolved without code:** Waldron Arts Center — `spektrix.py`'s Constellation output is 100% Waldron (65/65 events; `window.eventsListing` is the same Spektrix data re-rendered). Nothing to build.

**Confirmed non-starters this pass:** Friendly Beasts Cidery (no Squarespace events collection — type=10 page; social-media-only). Bloomington Early Music Festival (SQ collection exists but only retrospective 2023–24 posts; re-probe spring 2027).


| Source | Platform / path | Notes |
|--------|-----------------|-------|
| Indivisible South Central Indiana | `mobilize.py` slug `indivisiblesouthcentralindiana` | Confirmed Bloomington + Ellettsville events; distinct from implemented Indivisible Central Indiana |
| Orbit Room | Dice widget (partner `WMJ4RCOX`) → Bandsintown `bandsintown.com/v/10090230-the-orbit-room` | 14 aggregator-only events; WFHB also covers it |
| Waldron Arts Center | Constellation's `window.eventsListing` JSON on seeconstellation.org | Verify whether existing `constellation.py` (Spektrix) already captures Waldron events before writing anything |
| Edgewood HS non-athletic events | Finalsite CMS at rbbschools.net | ICS behind UI interaction; athletics covered via MaxPreps above |
| Tibetan Mongolian Buddhist Cultural Center | WordPress RSS `tmbcc.org/feed/` | Events as blog posts; retreats, LOSAR, Summer Prayer Festival; mod_security blocks ?ical=1 |
| Brown County government | CivicEngage: POST `chkCalendarID=14` to `/iCalendar.aspx` | Button exists; needs form-style request |
| Owen County Public Library (Spencer) | JSON API `https://owenlib.org/api/events` (87 events) | Payload CMS JSON — trivial adapter, not ICS |
| Monroe County Public Library ICS | Communico/Stacks | The iCal export lives on the partner portal `mcplin.libnet.info/feeds?data=...` (the `calendar.mcpl.info` custom-domain endpoint 404'd 2026-09-30; see the 2026-10-09 repair entry) |
| Chamber of Commerce (Atlas) | WebLink JSON `api-internal.weblinkconnect.com` (auth) | Upgraded from dead end |
| Bloomington Symphony Orchestra | WordPress, no TEC; ~6 concerts/yr | bloomingtonsymphony.org/concert/ |
| Monroe County Civic Theater | WordPress/Kubio + Ludus ticketing | mcct.org; Shakespeare in the Park |
| Off Night Productions | Ludus (offnight.ludus.com) | Shows at the Waldron |
| Bloomington Creative Glass Center | Wix, manual posts | Great Glass Pumpkin Patch Oct 10, 2026 |
| Bloomington Early Music Festival | Squarespace; annual May festival | May 26–30, 2026 |
| Friendly Beasts Cidery | Squarespace, manual listings | Thursday trivia 6:30, live music |
| Cosmic Songwriter Club | Mobirise static | Monthly at Orbit Room (1st Wed) + May festival |
| Gaden KhachoeShing Monastery | Eventbrite organizer `10637013504` | Tibetan Buddhist monastery, public ceremonies |
| Monroe Convention Center | Simpleview calendar | bloomingtonconvention.com/calendar/ |
| United Way of South Central IN | Drupal 10, no iCal | ~2 large events/yr |
| Hoosier Hills Food Bank | WordPress behind Incapsula; static events HTML | ~6 events/yr |
| Monroe County Humane Association | Site CDN-flaky; race on RunSignUp | Run for the Animals Oct 4, 2026 |
| IU Health Bloomington classes | Proprietary classes-events system | Low density; phone-register model |
| Morgan County Public Library | Drupal 11 `librarycalendar.com`, no Views iCal | Scrape HTML |
| Visit Morgan County | Simpleview | visitmorgancountyin.com/events |
| Ellettsville Farmers Market | Custom site, no feed | Saturdays May–Sep |
| Bloomington Brewing Co | Squarespace: events collection empty BUT individual festival pages carry per-event `.ics` links | Springfest/Summerfest/Oktoberfest/Winterfest only |
| Exodus Refugee Immigration | Eventbrite organizer `36028304013` | Bloomington office; World Refugee Day; currently 0 upcoming — wire and wait |

## Discovered 2026-07-17 — Manual / seasonal sweep list

Annual events with reliable dates but no feeds — a once-a-season curator sweep keeps them current:

| Event | When (2026 verified) | Where / URL |
|-------|----------------------|-------------|
| Monroe County Fall Festival | Sep 10–12 | Ellettsville — monroecountyfallfestival.com |
| Owen County Apple Butter Festival | Sep 19–20 | Spencer — Facebook @theapplebutterfestival |
| Gosport Lazy Days Festival | Aug 13–16 | gosportlazydaysfestival.com |
| Stinesville Stone Quarry Festival | late Sep | Facebook @stinesvillequarryfest |
| Harrodsburg Heritage Days | May 15–16 | harrodsburgheritagefestival.com |
| Smithville Lake Festival | ~Jun 21 (Father's Day wkend) | smithvillelakefestival.com |
| Morgan County Fair | Jul 10–18 | morgancountyfair.com |
| Owen County Fair / 4-H | Jul 5–10 | Owen Co. Fairgrounds, Spencer (re-source the FB page — discovery URL was misattributed) |
| Bloomington Pridefest | Aug 22 | bloomingtonpride.org |
| 4th Street Festival of the Arts | Labor Day weekend | 4thstreet.org |
| Hilly Hundred | Oct 2–4 | hillyhundred.org |
| Bloomington Music Expo | Oct 3 | Switchyard Park — ftrvinyl.com |
| Monroe County Recovery Summit | Sep 1–2 | Eventbrite organizer `89606403633` |
| Area 10 / Endwright Center (seniors) | monthly PDF calendars | area10agency.org — Ellettsville; Senior Games annual |
| El Centro Comunal Latino | Facebook-primary | elcentrocomunal.com — quarterly sweep; serves Spanish-speaking community |
| Bloomington Refugee Support Network | Facebook-primary | bloomingtonrefugees.org |
| Hoosier Trails Council BSA | scoutingevent.com/145 | Members-priority; public access unclear |

## Dead-end additions (2026-07-17)

| Source | Reason |
|--------|--------|
| Eventlink (BHS North/South, Martinsville athletics) | Public event pages but ICS requires login; no unauthenticated export |
| IHSAA calendar | 403 on all probes |
| fixtur.es | Pro/national leagues only; no Bloomington teams |
| Bloomington Roller Derby / IU Club Rugby / Bloomington Soccer | Active schedules, no ICS anywhere |
| Legistar / Granicus (city) | Not a Legistar client; Granicus is meeting videos + RSS only |
| B-Clear open data | No calendar/events datasets |
| TeamUp / MembershipWorks | No area orgs found on either platform |
| Sleeper's Bar | Wix, calendar page, no feed |
| Max's Place | Webflow, no events section |
| Starlite Drive-In | Showtimes via Veezi, not events |
| Porthole Inn / Hoppy Wobbles | Recurring bar events, Facebook-primary, no dated calendar |
| MCCSC calendar | Gabbart/ParentSquare ICS endpoint exists but login-gated |
| Bloomington Volunteer Network | Galaxy Digital `/ical/` endpoint exists but redirects to login |
| Amplify Bloomington | Re-probed: Cloudflare silently drops everything incl. wp-json — still dead |
| Bloomington PRIDE / Bloomington Brewing (Squarespace JSON) | Events collections exist but empty (0 items) — they post to Facebook / per-event pages |
| FUMC / Beth Shalom / ICOB / St. Thomas ELCA / Sherwood Oaks / St. Paul Catholic / Vine and Branch / St. Agnes / Ellettsville Christian | No embed, Planning Center, Fishhook, Cloudflare, or Wordfence — per-congregation notes in run log |
| Indian Cultural Center | ASP.NET, contact-only event access |
| parkrun | No Bloomington parkrun exists (nearest: Plainfield, ~38 mi) |
| Unionville | Unincorporated; no org website |
| Artie Fest (Martinsville) | Paused as of 2025; recheck 2027 |
| Limestone Comedy Festival | Taking 2026 off |

---

## Platform Scrapers (Reusable)

| Platform | File | Used By (Bloomington) | Notes |
|----------|------|-----------------------|-------|
| Squarespace | `lib/squarespace.py` | Cardinal Spirits, Sassafras Audubon, Master Gardeners, People's Market | JSON API at `?format=json` |
| All-in-One Event Calendar (ai1ec) | `lib/ai1ec.py` | — | WordPress plugin; HTML agenda view (no Bloomington source; WFHB moved to Events Manager) |
| Events Manager (EM) | `lib/em_events.py` | WFHB | WordPress plugin; AJAX listing endpoint |
| Sugar Calendar Lite | `lib/sugar_calendar.py` | Writers Guild | WordPress plugin; list + detail pages |
| Songkick | `lib/songkick.py` | Bluebird, Blockhouse | Venue event pages |
| Eventbrite | `scrapers/eventbrite.py` | Morgenstern Books, Nerd Nite, The Tap, Story Inn, Martinsville Arts Council, Gallery at the Vault, Keplinger Institute, Big Red Liquors, Blueline Bloomington, Falun Dafa Club at IU, The Afrobellas At IU, Reviving Hope for the Nations, Exodus Refugee Immigration, Gaden KhachoeShing Monastery | Organizer page → JSON-LD |
| Mobilize.us | `scrapers/mobilize.py` | Indivisible | Organizer event pages |
| The Events Calendar (Tribe) | `lib/tribe_events.py`, `scrapers/tribe_rest.py` | Bloomington Symphony, Boys & Girls Club, Community Band, Upland, Hard Truth Distilling Co. | WordPress plugin REST API; bypasses blocked or empty ICS exports |
| Localist | `scrapers/localist.py` | McCormick's Creek SP, Brown County SP | events.in.gov JSON API; filter by venue_id |
| JSON-LD | `lib/jsonld.py` | (used by Eventbrite) | Schema.org Event extraction |

---

## Discovery Run Log

### 2026-09-19: WFIU Community Calendar built and registered as an aggregator
- Built `scrapers/wfiu_community_calendar.py` (Pattern A, `name = "WFIU Community Calendar"`): walks the `?f1` date-filtered listing across the Horizon, emits one event per occurrence card, and fetches each unique detail page once for street/city/state/ZIP, ticket link, image, presenting org, and `brightspot.contentId` (the UID). Hard page cap 80 and detail cap 500 both raise rather than truncate; date-drift cards (a month/day that names no real date or has already passed) raise after a small threshold, while the listing's horizon+1 leak drops silently.
- Registered via the standard DB-first path — the `cities/bloomington/pending_feeds.txt` entry (`# WFIU Community Calendar`, `# cmd: python scrapers/wfiu_community_calendar.py --output cities/bloomington/wfiu_community_calendar.ics`). No workflow edit: the nightly pending-feeds processor inserts the active DB row and the DB-first runner executes it. `add_scraper.py`'s live smoke test honors the test-only `SCRAPER_TEST_PAGE_CAP` bound so the 120s registration test validates end to end while the registered command stays unbounded.
- Added `"WFIU Community Calendar"` to `source_priority.json`'s `aggregators` list, so it loses cross-source dedup to primaries and merges with fellow aggregators under the existing single-tier sort (no new ADR). Shared events merge to `Visit Bloomington, WFIU Community Calendar`; fellow-aggregator echoes merge alphabetically.
- Earlier (2026-09-18) surface verification reversed the stale "Indiana Public Media — Brightspot CMS, no ICS/RSS for events" dead end recorded under Inactive / Suspended.
- Calibration (research-time, 93-day window): `?f1` returns **67 pages / 667 occurrence cards / 348 unique detail URLs**. The listing is occurrence-expanded (one card per occurrence; 58–62% carry `data-recurring`), so each card is one emitted occurrence and recurrence is not re-expanded. Future runs compare against these counts through the degradation guard (warn below 50% of the trailing 7-run card median).

### 2026-09-16: Visit Bloomington registered as a primary source
- Registered via the standard DB-first path — `add_scraper.py visit_bloomington bloomington "Visit Bloomington"` wrote the `cities/bloomington/pending_feeds.txt` entry (`# Visit Bloomington`, `# cmd: python scrapers/visit_bloomington.py --output cities/bloomington/visit_bloomington.ics`). No workflow edit: the nightly pending-feeds processor inserts the active DB row and the DB-first runner executes it.
- Verified live at registration: `add_scraper.py --test` produced 484 events (SCRAPE_MONTHS=2).
- Deliberately left out of `source_priority.json`, so it ranks as a primary source and wins cross-source dedup over the Limestone Post CitySpark echo; shared events merge to `Visit Bloomington, Limestone Post` (ADR 0011).
- Sitemap fallback recorded as contingency-only (see Tourism & Visitor Events above).

### 2026-09-15: Visit Bloomington surface verified — dead end reversed
- **Correction:** the earlier "Visit Bloomington — Simpleview CMS — No public API" entry (and the generic "Simpleview is a dead end" claim in `docs/search-pattern-tests.md`/`docs/platforms.md`) was wrong. The `/event/rss/` feed caps at 30 items and detail JSON-LD is date-only, but the same-origin Simpleview **REST API** (`/includes/rest_v2/plugins_events_events_by_date/find/` + `get_simple_token/`) returns clock times, full descriptions, geo, recurrence and `skip` paging over plain HTTP — 34 requests → 1,666 occurrences across 230 recids, empty cookie jar, no browser.
- Also fixed the stale assumption in `scrapers/simpleview.py` reuse: its RSS + JSON-LD path emits all-day events and drops recurring series, so Visit Bloomington needs a dedicated `scrapers/visit_bloomington.py`.
- Nothing built here — the surface decision, coverage bar, API mechanism, registration and dedup/geo contracts are locked in the spec issue #124 (see map #117).

### 2026-10-09: Monroe County Public Library feed repaired (issue #183)
- `Monroe County Public Library` feed 404s: the registered Communico/Stacks feed `https://calendar.mcpl.info/feeds?data=...` returned `Not Found` (broken since 2026-09-30, ~500 events lost). The host migrated the portal: MCPL's own events page now loads its components from `elements.communico.co` and builds the iCal link on the partner portal `https://<keyword>.libnet.info` — keyword `mcplin`, so `https://mcplin.libnet.info/feeds?data=...`.
- Verified 2026-10-09: old host `/feeds?data=...` → 404; `https://mcplin.libnet.info/feeds?data=<same payload>` → 200, `BEGIN:VCALENDAR`, **500 events** (`PRODID:-//Monroe County Public Library//Event Calendar//EN`).
- Fix is a DB update (no scraper code change): migration `supabase/migrations/20261009120000_repair_mcpl_feed_url.sql` repoints the registered row from the dead `calendar.mcpl.info` URL to `mcplin.libnet.info`, keeping the same 90-day, all-filters payload so the source name and filters are unchanged. `feeds.txt` regenerates from the DB on the next build; do not hand-edit it.
- The earlier note that `library_intercept.py --location bloomington` still covered MCPL was wrong: that config points at `bloomingtonlibrary.org` (Bloomington, **Illinois** — see #50), not MCPL. The Communico feed is the ingest.

### 2026-10-10: WonderLab Museum feed dropped (issue #186)
- The `WonderLab Museum` ICS feed (`https://wonderlab.org/events/list/?ical=1`) served HTML, not ICS, with no good build in recorded history (`✅ wonderlab.ics: 0 events` every nightly build). wonderlab.org fronts the whole host with Cloudflare bot protection: from GitHub Actions egress **every** endpoint returns an HTTP 403 Cloudflare challenge page (`<!DOCTYPE html>...<title>Just a moment...</title>`) for **every** User-Agent — the ICS export and the Tribe REST API (`/wp-json/tribe/events/v1/events/`) alike. Verified from CI with a throwaway probe workflow (runner IP, `curl/8.5.0`, `Mozilla/5.0`, and the project `CommunityCalendar` UA all 403).
- This is the documented Cloudflare datacenter-IP block pattern (`docs/discovery-lessons.md`; NAMI Greater Bloomington, #19): no header or User-Agent change fixes it, and converting to `tribe_rest.py` (the #185 Hard Truth move) would only write a valid-empty calendar from CI. Dropped the source instead.
- No coverage is lost: WonderLab events already reach the calendar through `WFIU Community Calendar` (ipm.org), `Visit Bloomington`, and `Pillar Arts Community Calendar` — the recurring programs and the special events both. Confirm on the next build by filtering `rss/bloomington-full.xml` for WonderLab-titled items from each of those sources.
- Fix is a DB update (no scraper code change): migration `supabase/migrations/20261010140000_drop_wonderlab_feed.sql` deletes the registered row and any events it produced. `feeds.txt` regenerates from the DB on the next build; do not hand-edit it.

### 2026-10-10: Hard Truth Distilling Co. feed converted to a Tribe REST scraper (issue #185)
- The `Hard Truth Distilling Co.` ICS feed (`https://hardtruth.com/events/?post_type=tribe_events&ical=1&eventDisplay=list`) served HTML, not ICS, with no good build in recorded history. hardtruth.com is behind SiteGround's `sgcaptcha` bot protection: it returns an HTTP 202 challenge page (`SG-Captcha: challenge`, meta-refresh to `/.well-known/sgcaptcha/`) to non-browser clients and hard-403s the project's default `CommunityCalendar` User-Agent. The downloader treats any non-empty body as a successful download and never falls back to curl, so the challenge page was written to `hardtruth.ics` and reported as `not_ics:html`.
- The Tribe REST API (`/wp-json/tribe/events/v1/events/`) is challenged identically. SiteGround's response is stateful/rate-based, not fixed UA/IP filtering: a plain `curl -A "Mozilla/5.0"` returned 7 events before this machine was rate-flagged, then every client (urllib, requests, curl, a real browser, and a text-proxy on a different IP) hit the challenge.
- Fix follows the documented SiteGround pattern (`docs/discovery-lessons.md`; the 2026-08-07 conversions): migration `supabase/migrations/20261010130000_convert_hardtruth_feed_to_scraper.sql` converts the row from `ics_url` to a `scrapers/tribe_rest.py` scraper with `--user-agent "Mozilla/5.0"`, the UA SiteGround is intermittently permissive to. `feeds.txt` regenerates from the DB on the next build; do not hand-edit it.
- Tradeoff (accepted, as for the earlier conversions): on a blocked day the scraper writes a valid-empty calendar — classified `quiet`, not `broken_feed` — so the source leaves the feed-health problem queue. First real event counts are expected from CI's quieter network path; local probes here hit the challenge.

### 2026-10-10: WFHB Community Calendar registered (issue #189)
- Registered the dormant `scrapers/wfhb_calendar.py` via the standard DB-first path — `add_scraper.py wfhb_calendar bloomington "WFHB Community Calendar"` wrote the `cities/bloomington/pending_feeds.txt` entry (`# WFHB Community Calendar`, `# cmd: python scrapers/wfhb_calendar.py --output cities/bloomington/wfhb_calendar.ics`). No workflow edit: the nightly pending-feeds processor inserts the active DB row and the DB-first runner executes it.
- Verified live at registration, and the verification caught a real defect before merge: the AJAX listing is **occurrence-expanded** (a recurring event returns one row per occurrence with the same URL), but the scraper's URL-based UID collapsed every recurrence to its first occurrence — a full run lost ~149 of 406 occurrences (weekly Trivia Night and People's Co-op Market each fell to a single event). `lib/em_events.py` now keys the UID by occurrence through the shared `generate_uid` (the same occurrence identity WFIU uses) and reads the body from `.em-item-desc` (the old `.em-event-description`/`.em-item-content` selectors matched nothing, so every event shipped with an empty description). The change is library-only; only WFHB uses it. Verified after the fix: a full 6-month run emits **393 events** (13 dropped past the Horizon), unique UIDs, descriptions populated, every one carrying `X-SOURCE:WFHB Community Calendar`. Single-time cards now get a two-hour default end so they are not zero-duration (previously 164 of 393). `add_scraper.py --test` (`SCRAPE_MONTHS=2`) still passes.
- The issue title says "existing ai1ec scraper", but the source had already migrated off ai1ec: #31 (`d45c48bd`) replaced the ai1ec agenda-view scraper with the Events Manager AJAX scraper (`lib/em_events.py`) after wfhb.org changed plugins. `lib/ai1ec.py` remains in the tree but no Bloomington source uses it; the Platform Scrapers table is corrected here.
- WFHB is an aggregator covering venues with no own calendar (Orbit Room, library-hosted events, and outlying town events) and is already in `source_priority.json`'s `aggregators`, so it loses cross-source dedup to primaries.

### 2026-10-10: Monroe County History Center registered (issue #190)
- Registered the dormant `scrapers/monroe_county_history_center.py` via the standard DB-first path — `add_scraper.py monroe_county_history_center bloomington "Monroe County History Center"` wrote the `cities/bloomington/pending_feeds.txt` entry (`# cmd: python scrapers/monroe_county_history_center.py --output cities/bloomington/monroe_county_history_center.ics`). No workflow edit.
- Source is EventON (WP REST API `monroehistory.org/wp-json/wp/v2/ajde_events`); the scraper parses dates from the listing `content` field and only falls back to a detail-page fetch for items with no parseable date.
- monroehistory.org sits behind SiteGround's `sgcaptcha` bot protection (the same WAF as Hard Truth, #185): a challenged request returns an HTTP 202 HTML page. The scraper's UA was changed from the project `CommunityCalendar/1.0` to a plain `Mozilla/5.0` (the documented SiteGround bypass), and a non-200 listing response now logs a warning so a blocked run is visible instead of silently emitting 0 events.
- Verified 2026-10-10: full 6-month run emits **17 events** (55 parsed from 250 listing items across 5 pages, 38 past the Horizon), unique UIDs, descriptions populated, every event carrying `X-SOURCE:Monroe County History Center`. `add_scraper.py --test` (`SCRAPE_MONTHS=2`) produced 7 events.
- Tradeoff (same as Hard Truth): SiteGround's block is stateful/rate-based. A challenge on the first page writes a valid-empty calendar (classified `quiet`, not `broken_feed`); a mid-pagination challenge keeps the pages already fetched rather than discarding them, so a partial refresh deletes fewer events than an empty one would.

### 2026-10-10: FAR Center for Contemporary Arts registered (issue #191)
- Registered the existing `scrapers/far_center.py` via the standard DB-first path — `add_scraper.py far_center bloomington "FAR Center for Contemporary Arts"` wrote the `cities/bloomington/pending_feeds.txt` entry (`# cmd: python scrapers/far_center.py --output cities/bloomington/far_center.ics`). No workflow edit: the nightly pending-feeds processor inserts the active DB row and the DB-first runner executes it.
- Source is Craft CMS (`thefar.org/events/list`); the scraper reads each event card's title, date/time range, description, and detail URL from the listing HTML — no per-event detail fetches.
- UIDs key on the Craft detail-page id (`/events/event/<id>/`) plus the occurrence datetime through the shared `generate_uid` — the same occurrence identity WFIU uses. This replaces a 40-character title slug that could collapse two same-day events into one UID.
- Yearless dates bind to the source-local current date and roll to the next year once they have passed ("January 20" seen in October becomes 2027), and a December–January multi-day range gets the correct end year. Both were latent defects: the six-month Horizon spans New Year, so every January–April card parsed in the November–December window would have landed in the past and been dropped.
- Verified 2026-10-10: `add_scraper.py --test` (`SCRAPE_MONTHS=2`) produced 5 events. A full 6-month run emits **4 events** — "Photo Forward: Fall 2026" started 2026-09-04, rolls to 2027-09-04, and is past the Horizon — all carrying `X-SOURCE:FAR Center for Contemporary Arts`. Feed health is clean (a valid, non-empty calendar).

### 2026-10-10: IU Athletics registered (issue #192)
- Registered the existing `scrapers/sidearm.py` (Sidearm Sports) via the standard DB-first path — `add_scraper.py sidearm bloomington "IU Athletics" --extra-args '--base-url "https://iuhoosiers.com" --name "IU Athletics" --timezone America/Indiana/Indianapolis --home-only' --output-name iu_athletics` wrote the `cities/bloomington/pending_feeds.txt` entry (`# cmd: python scrapers/sidearm.py ... --output cities/bloomington/iu_athletics.ics`). No workflow edit: the nightly pending-feeds processor inserts the active DB row and the DB-first runner executes it. This matches the registration upstream already carries for this source. Reverses the 2026-07-17 dead-end entry (no ICS; the old 2013-15 Google feeds are dead, but the Sidearm v3 API is live).
- Source is the Sidearm v3 Calendar API (`iuhoosiers.com/api/v2/Calendar`), which returns structured game data with a `locationIndicator` of `H` (home site), `A` (away), or `N` (neutral site). `--home-only` previously dropped only `A`, so every neutral-site game — ITA regionals in Ohio, invitationals in Georgia and Arizona, 149 in all — flowed into Bloomington. The combine-time geo-filter does not catch them: it recognises only abbreviated states (`, OH`), and Sidearm writes the full name (`Mason, Ohio`). `--home-only` now drops both `A` and `N` on the v3 API path. The API states a start time only, so each event also gets a two-hour default end.
- The v3 request window now comes from `BaseScraper.horizon_cutoff(now)` — six months is 6 × 31 = 186 days — instead of a hardcoded 180 days, which had dropped the last six days of the Horizon. A fixed-clock test pins the window.
- Verified 2026-10-10: full 6-month run emits **85 events**, all home-site — 79 in Bloomington, 4 at Indianapolis (IU-hosted), 2 with no location — every event carrying `X-SOURCE:IU Athletics`, unique UIDs. `add_scraper.py --test` (`SCRAPE_MONTHS=2`) produced 131 before the fix and 50 after. Feed health is clean.

### 2026-10-10: Eventbrite organizer batch registered (issues #196, #197, #200–#209)
- Registered 12 Eventbrite organizer feeds for Bloomington via the standard DB-first path — `add_scraper.py eventbrite bloomington "<Name>" --extra-args '--url "<organizer>" --name "<Name>"' --output-name eventbrite_<slug>` wrote each `cities/bloomington/pending_feeds.txt` entry (`# cmd: python scrapers/eventbrite.py --url ... --name ... --output cities/bloomington/eventbrite_<slug>.ics`). No workflow edit and no scraper code change: `scrapers/eventbrite.py` (organizer page → per-event JSON-LD) already exists.
- Eleven match the registration upstream already carries (Morgenstern Books, Falun Dafa Club at IU, The Afrobellas At IU, Reviving Hope for the Nations, Big Red Liquors, Blueline Bloomington, Gallery at the Vault, Martinsville Arts Council, Nerd Nite Bloomington, Story Inn, The Tap); Keplinger Institute for Wellness and Art (#197) is new — its organizer URL was not on file and was resolved during this batch (`/o/the-keplinger-institute-for-wellness-and-art-89215506373`). This fills the fork's gap: none of the twelve had been registered in the fork's `feeds` table — five were already listed in the tables above, and this batch documents the other seven for the first time.
- Live `add_scraper.py` smoke runs (2026-10-10, `SCRAPE_MONTHS=2`):

| Issue | Source | Organizer | Events (test) |
|-------|--------|-----------|---------------|
| #196 | Morgenstern Books | `/o/morgenstern-books-34376767621` | 12 |
| #197 | Keplinger Institute for Wellness and Art | `/o/the-keplinger-institute-for-wellness-and-art-89215506373` | 2 |
| #200 | Falun Dafa Club at IU | `/o/102507618371` | 1 |
| #201 | The Afrobellas At IU | `/o/106566049911` | 1 |
| #202 | Reviving Hope for the Nations | `/o/106576693901` | 0 current |
| #203 | Big Red Liquors | `/o/18076093080` | 0 current |
| #204 | Blueline Bloomington | `/o/24897361037` | 0 current |
| #205 | Gallery at the Vault | `/o/31640015525` | 5 |
| #206 | Martinsville Arts Council | `/o/martinsville-arts-council-59689470843` | 8 |
| #207 | Nerd Nite Bloomington | `/o/nerd-nite-bloomington-95199764993` | 0 current |
| #208 | Story Inn | `/o/story-inn-825970603` | 0 current |
| #209 | The Tap | `/o/the-tap-bloomington-69461600243` | 0 current |

- The six sources that produced 0 upcoming events at test time are wire-and-wait, not broken: Eventbrite organizer pages are intermittently CAPTCHA-gated to non-browser clients (the same behaviour recorded for Gaden KhachoeShing and Exodus Refugee Immigration), and several organizers simply have no posted upcoming events. Each writes a valid-empty calendar — classified `quiet`, not `broken_feed` — and repopulates when the organizer posts again.

### 2026-09-07: Master Gardeners URL fix (issue #13)
- `Monroe County Master Gardeners` scraper 404s: DB `feeds` row id=14 still runs `squarespace.py --url "https://www.mcmga.net/events"` (404). Same stale-URL pattern as Sassafras (#8) — the pre-DB-first URL fix never reached the seeded DB row.
- Verified 2026-09-07: `/events` → 404, `/calendar` → 404, `/eventscalendar` → 200 with 76 event links; full scraper run yields 37 events (1 filtered beyond 6 months). Fix is a DB update (no code change): set `scraper_cmd` to `python scrapers/squarespace.py --url "https://www.mcmga.net/eventscalendar" --name "Monroe County Master Gardeners"` for id=14. `feeds.txt` regenerates from the DB on the next build; do not hand-edit it.

### 2026-09-07: Sassafras Audubon URL resurfaced (issue #8)
- `Sassafras Audubon Society` scraper 404s again: DB `feeds` row id=18 still runs `squarespace.py --url "https://www.sassafrasaudubon.org/upcomingevents"` (404, Squarespace 404 page). The May fix (workflow + feeds.txt) was lost in the DB-first migration — the seeded DB row kept the stale URL.
- Verified 2026-09-07: `/upcomingevents` → 404, `/calendar` → 200 with 30 event URLs, all `?format=ical` fetches succeed. Fix is a DB update (no code change): set `scraper_cmd` to `python scrapers/squarespace.py --url "https://www.sassafrasaudubon.org/calendar" --name "Sassafras Audubon Society"` for id=18. `feeds.txt` regenerates from the DB on the next build; do not hand-edit it.
- Note: `Monroe County Master Gardeners` (id=14, `https://www.mcmga.net/events`) looks like the same stale-URL pattern (upstream noted `/eventscalendar` as the working slug 2026-07-17) — verify separately, kept out of scope for #8.

### 2026-02-08: Initial Discovery
- BloomingtonOnline Google Calendars (3 feeds)
- B-Square Bulletin Google Calendars (4 feeds)
- Parks and Recreation Google Calendar
- IU LiveWhale feeds (3 initial, expanded to 17)
- Meetup groups (2 active of 5 probed)

### 2026-02-17: Topical Search
- Bloomington Farmers Market (Google Calendar)
- Searched all curator-guide topics; most independent venues use Squarespace/Wix (no ICS)

### 2026-02-18: Sports & Outdoor
- Bloomington Bicycle Club (Google Calendar, ~5023 events)

### 2026-03-02: Scraper Buildout (51 sources)
- WonderLab, First United Church, Community Band, Brown County Playhouse, Upland (ICS feeds)
- Cardinal Spirits, Sassafras Audubon, Master Gardeners, People's Market (Squarespace scrapers)
- Sycamore Land Trust, Constellation, Cicada Cinema, Indivisible, Morgenstern Books (custom scrapers)
- Bloominglabs, Let's Go! Bloomington, City Boards & Commissions (Google Calendars)
- Lotus Festival (ICS)

### 2026-07-17: Refresh Pass (8 lenses, agent fan-out)
- **Phase 4 upstream authority**: analyzed events.json for aggregator-only venues; graduated The Back Door (Tockify ICS re-enabled, 268), Brown County Art Guild (?ical=1 + browser UA), Brown County Inn (260), Art Sanctuary (168), Monroe Lake DNR (138)
- **Dead-end re-litigation**: 13 dead ends re-probed with newer techniques; 1 resolved (Back Door), 1 upgraded (Chamber Atlas → WebLink API), MCCSC + Volunteer Network ICS endpoints found but login-gated
- **Sports**: 8 MaxPreps school slugs verified (HS athletics was a whole missing category; Edgewood = 84 aggregator events); 8 new Ticketmaster venue IDs; Eventlink/IHSAA/fixtur.es ruled out
- **Faith**: 6 tested feeds (5 Google Cal + 1 native ICS); TMBCC → RSS scraper lead; 11 congregations ruled out with reasons
- **Platform sweeps**: Google Sites (nil), Mobilize (+Indivisible South Central Indiana), Tockify/TeamUp/MembershipWorks (Tockify only), CKAN/Legistar (nil)
- **Surrounding towns**: Ellettsville CivicPlus (205), Morgan County CivicPlus (73), Monroe County Fairgrounds gcal (344), Owen County Library JSON API (87), full festival circuit with 2026 dates
- **Directories**: Visit Bloomington/Gallery Walk/IDS Happenings/volunteer network mined; Butler Winery (35, tested); long Needs-Scraper bench (BSO, MCCT, BCGC, BLEMF, Cosmic Songwriter…)
- **Gap topics**: Monroe County 4-H gcal (386); volunteerism orgs mapped (mostly Needs Scraper/Manual); El Centro + BRSN flagged for quarterly manual sweeps; no parkrun

### 2026-09-04: Writers Guild feed fixed (ai1ec ICS → Sugar Calendar scraper)
- The `writersguildbloomington` ICS feed served HTML, not ICS: the site migrated from All-in-One Event Calendar (ai1ec) to Sugar Calendar, so the old exporter endpoint (`?plugin=all-in-one-event-calendar&controller=ai1ec_exporter_controller...`) returns the HTML page (confirmed across browser UAs; `/events/` shows 123 `sugar-calendar` refs, 0 `ai1ec`).
- Converted the DB feed row from `ics_url` to `scraper`: `python scrapers/writers_guild.py --output cities/bloomington/writersguildbloomington.ics` (same name/slug, no event-history disruption). Verified: 4 events, `X-SOURCE:Writers Guild at Bloomington`.

### 2026-08-07: DB-first cleanup and full local audit
- Reconciled workflow scraper commands against Supabase: no missing rows, metadata updates, or DB-only scraper rows remained after cleanup.
- Replaced the empty Boys & Girls Club Tribe ICS export with `tribe_rest.py` (2 events).
- Replaced the zero-byte Community Band ICS export with `tribe_rest.py` (5 events).
- Replaced Upland's zero-byte seasonal ICS export with `tribe_rest.py`; its REST calendar is healthy but currently has 0 upcoming events.
- Ran every Bloomington source through `scripts/local_build.py`: all scraper commands succeeded, no scraper or live-feed outputs were missing, pipeline validation had no errors, and 6,362 unique future events combined before the final two REST conversions.

### 2026-03-28: Previous Session (59 sources)
- **WFHB Community Calendar** (~349) — ai1ec scraper; aggregator covering many venues. New platform: `lib/ai1ec.py`
- **Writers Guild at Bloomington** (~7) — Sugar Calendar scraper. New platform: `lib/sugar_calendar.py`
- **Nerd Nite Bloomington** (~1) — Eventbrite organizer 95199764993
- **IU Eskenazi School of Art** (~94) — LiveWhale `group_id/11`
- **FAR Center for Contemporary Arts** (~4) — Craft CMS scraper
- **Redbud Books** (~348) — Google Calendar
- **Habitat for Humanity Monroe County** (~4) — WordPress scraper
- **The Bishop** — SSL fix (`verify=False`)
- **Oblique strategy**: WFHB covers Bishop Orbit Room events, library-hosted events, and venues with no own calendar

---

## Notes

### Timezone
Bloomington, IN uses `America/Indiana/Indianapolis` (Eastern, no DST changes since 2006).

### Probe Commands
```bash
# Check for hidden ICS/RSS
curl -sL "<URL>" | grep -i -E "(ical|\.ics|webcal|calendar\.google|rss|xml|feed)"

# Check ICS feed validity
curl -sL "<URL>" | head -5  # Should start with BEGIN:VCALENDAR

# Discover IU LiveWhale group_id from page source
curl -sL "https://events.iu.edu/{group}/" | grep -o '"group_id":"[0-9]*"'
```

### Key Observations
- Most independent arts/culture venues in Bloomington use Squarespace or Wix (no ICS)
- WFHB is the best "oblique strategy" — curated community aggregator covering venues that don't have their own calendars
- BloomingtonOnline calendars capture most community events
- IU LiveWhale feeds capture most university arts/culture events
- Yoga/wellness/fitness is a coverage gap — all studios use MindBody/Squarespace class schedules
- Volunteerism is a coverage gap — Volunteer Network (Galaxy Digital) has no feed export
