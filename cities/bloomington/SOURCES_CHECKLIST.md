# Bloomington Calendar Source Checklist

Prioritized list of potential event sources for the Bloomington, IN community calendar.

## Currently Implemented (76 sources)

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

### University — Other IU Platforms (2 feeds)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| IU Moving Image Archive | LibCal `cid=5914` | ~151 | |
| IU Scholars' Commons | LibCal `cid=1228` | ~26 | |

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

### Arts & Culture (6 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Pillar Arts Community Calendar | ICS | ~62 | Tockify API feed; includes Pillar Arts Alliance Center + Pillar Arts By Hand events |
| FAR Center for Contemporary Arts | Scraper | ~4 | `far_center.py` — Craft CMS |
| Cicada Cinema | Scraper | ~6 | Shopify products API — `cicada_cinema.py` |
| Pottery House Studio | Scraper | ~40 | Squarespace — `squarespace.py` workshops |
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
| Monroe County Public Library | Scraper | ~483 | `library_intercept.py --location bloomington` |
| Boys & Girls Club | ICS | — | WordPress Events Calendar |
| WonderLab Museum | ICS | ~30+ | WordPress ICS — Cloudflare blocks HTML but not ICS |
| First United Church | ICS | ~50+ | WordPress ICS — community hub (DSA, Al-Anon, scouts) |
| Bloomington Community Band | ICS | ~20 | WordPress Events Calendar |
| Bloominglabs Makerspace | Google Calendar | ~10+ | |
| Habitat for Humanity Monroe County | Scraper | ~4 | `habitat.py` — fundraisers, 5K, volunteer events |
| NAMI Greater Bloomington | Scraper | ~31 | `nami_bloomington.py` — Tribe Events API; support groups at library |
| Bloomington Spinners & Weavers Guild | ICS | — | |

### Nature & Outdoors (6 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Sassafras Audubon Society | Scraper | ~31 | Squarespace — `sassafras_audubon.py` |
| Monroe County Master Gardeners | Scraper | ~62 | Squarespace — `master_gardeners.py` |
| Sycamore Land Trust | Scraper | ~131 | WordPress — `sycamore_land_trust.py` |
| McCormick's Creek State Park | Localist scraper | ~44 | `localist.py` — events.in.gov venue 35217665860404 (13 mi) |
| Brown County State Park | Localist scraper | ~13 | `localist.py` — events.in.gov venue 35217662417669 (17 mi) |
| Knobstone Hiking Trail Meetup | ICS | ~10 | Meetup group — regional hiking |

### Interest Groups & Civic (5 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Bloomington Atheists Meetup | ICS | ~10 | Meetup group |
| Bloomington Bicycle Club | Google Calendar | ~5023 | Cycling rides, weekly events |
| Bloomington Velo Club | Google Calendar | — | |
| Hoosier Fly Fishers | ICS | — | |
| Indivisible Central Indiana | Scraper | ~21 | `mobilize.py` — civic/political organizing |

### Food & Beverage (5 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Cardinal Spirits | Scraper | ~5 | Squarespace — `cardinal_spirits.py` |
| The Tap | Eventbrite scraper | — | Live music, craft beer events |
| Martinsville Arts Council | Eventbrite scraper | ~6 | Community theater in Martinsville (20 mi) |
| Story Inn | Eventbrite scraper | — | Seasonal: wine fairs, comedy, music in Story (17 mi) |
| Hard Truth Distilling Co. | ICS | ~15 | TEC feed; Nashville, IN (16 mi) |
| Upland Brewing | ICS | — | WordPress Events Calendar — dormant, populates seasonally |
| People's Market | Scraper | ~10 | Squarespace — `peoples_market.py` |

### Aggregators (10 sources)

These curate or aggregate events from multiple venues:

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| WFHB Community Calendar | Scraper | ~349 | `wfhb_calendar.py` — ai1ec; covers Orbit Room, library events, and many venues not otherwise scrapable |
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
| Visit Bloomington | Simpleview CMS | No public API |
| Winter Farmers' Market | Wix | No ICS export |
| Gallery Walk Bloomington | Wix | No feed; recurring first Friday 5-8pm |
| BARA (runners) | Wix | No ICS export |
| Bloomington PRIDE | Squarespace | No ICS export |
| Bloomington Brewing Co | Squarespace | No ICS export |
| Bloomington Yoga Collective | Squarespace + MindBody | Class schedules only |
| Vibe Yoga Studio | Squarespace | Class schedules only |
| Bloomington Volunteer Network | Galaxy Digital | No feed export |
| ~~NAMI Greater Bloomington~~ | ~~The Events Calendar~~ | RESOLVED: Tribe Events REST API works (2026-03) |
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
| Indiana Public Media | Brightspot CMS, no ICS/RSS for events |
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
| Monroe County Public Library ICS | Communico (`calendar.mcpl.info`) | `showICAL: true` but export is a JS POST to api.communico.co; existing `library_intercept.py` scraper still covers MCPL — this is only an alternative |
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
| IU Athletics composite (iuhoosiers.com) | No ICS; 2013-15 Google feeds dead (iu_athletics.ics feed already implemented remains the source) |
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
| All-in-One Event Calendar (ai1ec) | `lib/ai1ec.py` | WFHB | WordPress plugin; HTML agenda view |
| Sugar Calendar Lite | `lib/sugar_calendar.py` | Writers Guild | WordPress plugin; list + detail pages |
| Songkick | `lib/songkick.py` | Bluebird, Blockhouse | Venue event pages |
| Eventbrite | `scrapers/eventbrite.py` | Morgenstern Books, Nerd Nite | Organizer page → JSON-LD |
| Mobilize.us | `scrapers/mobilize.py` | Indivisible | Organizer event pages |
| The Events Calendar (Tribe) | `lib/tribe_events.py` | NAMI | WordPress plugin REST API; bypasses WAF-blocked ICS |
| Localist | `scrapers/localist.py` | McCormick's Creek SP, Brown County SP | events.in.gov JSON API; filter by venue_id |
| JSON-LD | `lib/jsonld.py` | (used by Eventbrite) | Schema.org Event extraction |

---

## Discovery Run Log

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
