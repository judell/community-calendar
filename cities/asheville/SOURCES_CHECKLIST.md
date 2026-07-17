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
| Asheville City Schools | Finalsite ICS (IDs 26,27,14,15,17,18) | 220 | `ashevillecityschools.net/fs/calendar-manager/events.ics?calendar_ids[]=...` — district + enrollment calendars. See AGENTS.md Platform-Specific Techniques for the Finalsite URL pattern. |
| Asheville High School | Finalsite ICS (ID 25) | 140 | `ashevillecityschools.net/…?calendar_ids[]=25` |
| SILSA | Finalsite ICS (ID 32) | 13 | `ashevillecityschools.net/…?calendar_ids[]=32` |
| Asheville Middle School | Finalsite ICS (IDs 24,10,6) | 602 | `ashevillecityschools.net/…?calendar_ids[]=24…` |
| Claxton Elementary School | Finalsite ICS (ID 23) | 74 | `ashevillecityschools.net/…?calendar_ids[]=23` |
| Hall Fletcher Elementary | Finalsite ICS (ID 21) | 30 | `ashevillecityschools.net/…?calendar_ids[]=21` |
| Isaac Dickson Elementary | Finalsite ICS (IDs 28,2) | 112 | `ashevillecityschools.net/…?calendar_ids[]=28…` |
| Ira B. Jones Elementary | Finalsite ICS (ID 29) | 0 | `ashevillecityschools.net/…?calendar_ids[]=29` — empty mid-summer, populates for fall term |
| Lucy S. Herring Elementary | Finalsite ICS (ID 20) | 0 | `ashevillecityschools.net/…?calendar_ids[]=20` — empty mid-summer, populates for fall term |
| ECA at William Randolph | Finalsite ICS (ID 22) | 7 | `ashevillecityschools.net/…?calendar_ids[]=22` |
| ACS Career and Technical Education | Finalsite ICS (ID 34) | 91 | `ashevillecityschools.net/…?calendar_ids[]=34` |
| ACS Preschool Program | Finalsite ICS (ID 30) | 2 | `ashevillecityschools.net/…?calendar_ids[]=30` |

| Warren Wilson College | Localist ICS | 97 | `events.warren-wilson.edu/calendar.ics` — added 2026-07-16 |
| Mars Hill University | WordPress Tribe Events | 30 | `mhu.edu/events/?ical=1` — added 2026-07-16 |
| Town of Black Mountain | CivicPlus ICS (catID=14) | 163 | `townofblackmountain.org/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar` — added 2026-07-16; recurrences run to 2032, pipeline date-filters |
| Henderson County Food Distributions | Tockify | 604 future | `tockify.com/api/feeds/ics/fooddistributionhendersoncountync` — added 2026-07-16 |
| UNC Asheville Athletics | Sidearm v2 ICS | 66 | `uncabulldogs.com/api/v2/Calendar/subscribe?type=ics` — added 2026-07-16; do NOT add `locationIndicator=HOME` (returns 0); geo-filter drops away games |
| Montreat College Athletics | Sidearm legacy ICS | 93 | `montreatcavaliers.com/calendar.ashx/calendar.ics` — added 2026-07-16 |
| Buncombe County Government | Trumba ICS | 200 | `trumba.com/calendars/buncombe-county-government.ics` — added 2026-07-16; overlaps the 5 CivicPlus county feeds — verify dedup after first build |
| Buncombe Age-Friendly Senior Centers | Trumba ICS | 200 | `trumba.com/calendars/social-work-services-age-friendly.ics` — added 2026-07-16; Grove St / Burton St / Harvest House senior programs |
| UU Congregation of Asheville | WordPress Tribe Events | 30 | `uuasheville.org/events/?ical=1` — added 2026-07-16 |
| Congregation Beth Israel | WordPress Tribe Events | 50 | `bethisraelnc.org/events/?ical=1` — added 2026-07-16 |
| Grace Covenant Presbyterian Church | Google Calendar ICS | 30 upcoming | `calendar.google.com/calendar/ical/gcpcusa.org_cff3s75sgv2btvjo73j07erbqo%40group.calendar.google.com/public/basic.ics` — added 2026-07-16; feed includes years of history, pipeline date-filters |
| Montford Neighborhood Association | Google Calendar ICS | 9 | `calendar.google.com/calendar/ical/montfordmnaboard%40gmail.com/public/basic.ics` — added 2026-07-16 |
| Literacy Together | Google Calendar ICS | 45 | `calendar.google.com/calendar/ical/c_ee62...%40group.calendar.google.com/public/basic.ics` — added 2026-07-16 |
| Jack of the Wood | WordPress Events Manager ICS | 50 | `jackofthewood.com/events.ics?scope=future` — added 2026-07-16; MUST use `scope=future` (plain `?ical=1` serves stale 2022 events) |
| The Mule at Devils Foot | WordPress Tribe Events | 30 | `devilsfootbrew.com/events/?ical=1` — added 2026-07-16; calendar name "Devil's Foot Beverage Company" |
| Highland Brewing | WordPress Tribe Events | 30 | `highlandbrewing.com/events/?ical=1` — added 2026-07-16 |
| Oklawaha Brewing | WordPress Tribe Events | 22 | `oklawahabrewing.com/events/?ical=1` — added 2026-07-16; Hendersonville |

### Platform Scrapers (added 2026-07-16 second pass)

| Source | Scraper | Events (test) | Notes |
|--------|---------|--------------|-------|
| The Grey Eagle | `rhp_events.py` (new, parameterized from sweetwater.py) | 66 | RSS `thegreyeagle.com/calendar/feed/` + JSON-LD per page. Supersedes Songkick interim (5) — remove `grey_eagle_songkick` via Manage Feeds once this lands |
| The Orange Peel | `rhp_events.py` | 37 | RSS `theorangepeel.net/events/feed/`; includes Hellbender (their new 5,000-cap outdoor venue). Supersedes Songkick interim (5) |
| Pisgah Brewing Company | `rhp_events.py` | 16 | RSS `pisgahbrewing.com/events/feed/` — same Rockhouse plugin; Eventbrite organizer is dormant (0 events) |
| Where Y'at AVL Music | `whereyat.py` (new) | 982 | Open JSON API `whereyatavlmusic.com/api/events`; ~50 venues incl. many with no feeds (5 Walnut, Fleetwood's, Double Crown, One World, Sierra Nevada, Asheville Symphony...). AGGREGATOR — listed in source_priority.json |
| Blue Mountain Pizza | `squarespace.py` | 68 | Weaverville; `/events` collection |
| Modelface Comedy | `squarespace.py` | 84 | City's main comedy producer; `/shows` collection |
| Barley's Taproom | `squarespace.py` | 46 | `/new-events-2` collection |
| Shiloh Community Association | `squarespace.py` | 46 | Neighborhood assoc; `/community-events` collection |
| Urban Dharma | `squarespace.py` | 16 | Buddhist center; `/events` collection |
| OTD Black Mountain | `squarespace.py` | 40 | `/events` collection |
| Shamrock Irons | `squarespace.py` | 40 | `/events` collection |
| Black Mountain Center for the Arts | `eventbrite.py` | 1 | Organizer `black-mountain-center-for-the-arts-11374533255` (superOrganizer, 532 lifetime events; low right now) |
| Buncombe County Democratic Party | `mobilize.py` | 67 | `mobilize.us/buncombedems/` |
| Rotary Club of Asheville | `ismyrotaryclub.py` | 79 | club-id 5996, account-id 7670 |
| Asheville Breakfast Rotary Club | `ismyrotaryclub.py` | 51 | club-id 23683, account-id 7670 |
| Harrah's Cherokee Center Asheville | `ticketmaster.py` | untested locally | venue-id `KovZpZAJvnIA` (verified via ticketmaster.com/venue/368913); `TICKETMASTER_API_KEY` is a repo secret used by 5 other cities — verify first CI run produces `tm_harrahs_cherokee.ics`. Supersedes Songkick interim (8) |

### Songkick Scrapers

> 2026-07-16: The Grey Eagle, The Orange Peel, and Harrah's Cherokee Center Songkick interims are superseded by `rhp_events.py` / `ticketmaster.py` sources above. After the new sources land in a build, remove the three Songkick feeds via the Manage Feeds dialog.

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

### Meetup Groups (55 groups)

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
| Asheville Comedy Fans | asheville-comedy-fans | 10 | ✅ 2026-07-16 |
| Misfit Improv & Acting School | misfit-improv-acting-school | 3 | ✅ 2026-07-16 |
| Queers to the Front! | queers-to-the-front | 9 | ✅ 2026-07-16 |
| Happily Ever Chapter | happily-ever-chapter | 6 | ✅ 2026-07-16 |
| Black Cat Book Club | black-cat-book-club | 2 | ✅ 2026-07-16 |
| AVL Writers | asheville-writers | 10 | ✅ 2026-07-16 |
| Books That Age Like Wine | asheville-classic-books-meetup-group | 2 | ✅ 2026-07-16 |
| Asheville's Fantasy/Sci-Fi Books and Beer Club | ashevilles-fantasy-sci-fi-books-and-beer-club | 1 | ✅ 2026-07-16 |
| Asheville's Bored Game Geeks | ashevilles-bored-game-geeks | 10 | ✅ 2026-07-16 |
| Asheville Filmmakers and Actors Group | asheville-filmmakers-and-actors-group | 1 | ✅ 2026-07-16 |
| Asheville Meditation Group | asheville-meditation-meetup-group | 10 | ✅ 2026-07-16 |
| Meditation in Asheville | meditationinasheville | 6 | ✅ 2026-07-16 |
| Center for Spiritual Living Asheville | center-for-spiritual-living-asheville | 6 | ✅ 2026-07-16 (their website's TEC has 0 events; Meetup is the live surface) |
| Star Sounds Asheville | asheville-mountain-star-sounds | 2 | ✅ 2026-07-16 |
| Senseful Soul's Asheville Healing Community | senseful-soul-s-asheville-healing-community-%EF%B8%8F-%EF%B8%8F | 10 | ✅ 2026-07-16 (slug contains URL-encoded emoji — keep encoded form verbatim) |
| Dances of Universal Peace WNC | dances-of-universal-peace-circles-of-nw-nc-se-tn | 10 | ✅ 2026-07-16 (regional; geo-filter drops E-TN circles) |
| Atheists of WNC | atheistsofwnc | 1 | ✅ 2026-07-16 |
| Not Dead Yet Asheville | not-dead-yet-ashevilles-women-in-their-50s | 1 | ✅ 2026-07-16 |
| Senior Singles Fun Bunch | seniorsinglesfunbunch | 10 | ✅ 2026-07-16 (Hendersonville) |
| Hendo Fun Friends | hendo-fun-friends | 10 | ✅ 2026-07-16 (alias `hendersonville-fun-friends` serves identical feed — one slug only) |
| Asheville Young Professionals | asheville-young-professionals | 2 | ✅ 2026-07-16 |
| Asheville Community Mom's Group | asheville-community-moms-group | 1 | ✅ 2026-07-16 |
| Sierra Club WENOCA | wenoca-sierra-club-wnc | 2 | ✅ 2026-07-16 |
| BANG Broker Alliance Networking Group | bang-broker-alliance-networking-group | 0 | ❌ No events |

---

## Needs Scraper (buildable)

| Source | URL | Approach | Notes |
|--------|-----|----------|-------|
| Hendersonville.com | hendersonville.com | MainStreet REST API | **Open API on the same MainStreet Online platform that blocks asheville.com**: `/wp-json/ms-events/v1/agenda?start=YYYY-MM-DD&end=YYYY-MM-DD` returned 435 events/month (structured `start_utc`, `venue_name`, `venue_address`). Covers the whole Hendersonville side of the radius. AGGREGATOR — classify in source_priority.json. Re-test this endpoint pattern on other MainStreet sites (incl. asheville.com). |
| Asheville Theater Alliance | ashevilletheateralliance.org | WP REST + HTML | JetEngine CPT `events` open at `/wp-json/wp/v2/events` (159 items) but dates NOT in REST; single event pages server-render full performance schedules ("Thu - Jul 30, 2026 7:30 pm" rows). Discovery via REST or the 16 links on `/asheville-performance-calendar/`. High value: covers NC Stage, SART, HART, Attic Salt, improv. AGGREGATOR. |
| Asheville Community Theatre | ashevilletheatre.org | WP REST + HTML | `mc_event` CPT exposed via REST but no date fields; event pages server-render run info ("August 21-30, 2026 — Location: 35below — Fridays and Saturdays at 8:00 PM"). Parse pattern like `scrapers/turtle_back_zoo.py`. Ticketing is PatronManager (Salesforce SPA, CSRF-gated — not scrapable). No Eventbrite presence. ~27 shows/season. |
| Third Room | thirdroom.art/calendar/ | SeeTickets | `seetickets-list-event-container` markup + WP REST `seetickets-event` CPT (41 events) — exact match for `scrapers/lib/seetickets.py`. |
| DICE venues (Eulogy, Static Age, AyurPrana, Burial Forestry Camp) | events-api.dice.fm | DICE partner API | `filter[cities][]=Asheville` returns 86 events: Eulogy 42, Static Age 21 (vs Songkick interims 8 and 5 — upgrade path), AyurPrana Listening Room 20, Burial Forestry Camp 3. Partner apiKey is embedded in ayurpranalisteningroom.com page source. Repo `lib/dice.py` uses link.dice.fm; this API is cleaner. |
| White Horse Black Mountain | whitehorseblackmountain.org | EventON WP REST | `wp-json/wp/v2/ajde_events?per_page=100` (64 posts, dates in content) — pattern per `scrapers/monroe_county_history_center.py`. Note **.org** (the .com is a separate weddings site). Established listening room. |
| Town of Weaverville | weavervillenc.org | Tribe REST | `?ical=1` → 410 Gone; `wp-json/tribe/events/v1/events/` works. `lib/tribe_events.py` subclass (pattern: `scrapers/nami_bloomington.py`). Recurring meetings inflate counts. |
| Town of Fletcher | fletchernc.org | Tribe REST | Same as Weaverville; 16 future events. |
| MountainTrue | mountaintrue.org | WP REST event CPT | `wp-json/wp/v2/event` works, dates in acf/meta; events span all WNC (incl. Brevard) — needs radius filter. Medium effort. |
| French Broad River Brewery | frenchbroadbrewery.com/events/ | Events Manager HTML | EM plugin but ICS/REST all empty/hang. 27 events/30d via LiveMusicAsheville; Where Y'at carries 59 — aggregators cover it for now. |
| Feed & Seed | feedandseednc.com/music/ | MF Gig Calendar HTML | Structured HTML rows, 5 future gigs. Fletcher. Small scraper. |
| Haw Creek Community Association | hawcreekavl.com/events | Wild Apricot | Per-event pages; adapt `scrapers/toronto_bicycling_network.py` pattern. 10+ events. |
| Hotel Eve Jazz | hotel-eve-jazz.turntabletickets.com | Turntable Tickets HTML | Server-rendered (~8 dates); venue_id 173; API endpoints 404. Where Y'at carries 18 — aggregator covers it for now. |
| Congregation Beth HaTephila | bethhatephila.org/cbht-calendar.html | Weebly HTML | Server-rendered "Upcoming 10 events" list; site 406s curl (WebFetch got through) — scraper needs header tuning. |
| Wortham Center for the Performing Arts | worthamarts.org | HTML scraper | WordPress with Toolset Blocks (custom CPT). No Tribe/MEC plugin, no ICS. RSS pubDate is season-announcement date. JSON-LD is `WebPage` with no `startDate`. ~10 shows per season. |
| NC Stage Company | ncstage.org | TBD | Professional equity theatre, 125-seat. WordPress; no feed detected. Small event count. Also covered by Asheville Theater Alliance scraper when built. |
| Southern Highland Craft Guild / Folk Art Center | southernhighlandguild.org/calendar/ | TBD | WordPress; `?ical=1` returns HTML (JS-loaded). Try Tribe REST API. |
| Mountain Xpress | mountainx.com/events/ | TBD | Local alt-weekly; Tribe Events but Cloudflare-protected (`?ical=1` blocked). High-value aggregator. Contact web admin for WAF exception (User-Agent `CommunityCalendar/1.0`, see curator-guide). |
| asheville.com/calendar-events | asheville.com | MainStreet API? | Cloudflare blocks fetches, but hendersonville.com (same MainStreet Online platform) has an open `/wp-json/ms-events/v1/agenda` API — try that exact endpoint here before writing off. Otherwise contact MainStreet Online (based in Asheville) for a partnership. |
| Asheville Tourists (MiLB) | milb.com/asheville/schedule | Custom scraper | 76 home + away games Apr–Sep 2026. No ICS anywhere. Lower community value. |

---

## To Investigate

- [ ] **Retire Songkick interims** — after the next build lands, remove `grey_eagle_songkick`, `orange_peel_songkick`, and `harrahs_cherokee_songkick` via the Manage Feeds dialog (superseded by `rhp_events.py` and `ticketmaster.py` sources, 2026-07-16).
- [ ] **Harrah's first CI run** — confirm `tm_harrahs_cherokee.ics` is produced (assumes `TICKETMASTER_API_KEY` secret is populated; 5 other cities use it).
- [ ] **Buncombe County Government (Trumba) overlap** — verify dedup against the 5 CivicPlus county feeds after first build; drop whichever side loses.
- [ ] **UA-gated feeds** — `ncarboretum.org` (existing feed, now 0 events) and `coabc.org` (Council on Aging, 1 event) return 403 to `Mozilla/5.0 (compatible; CommunityCalendar/1.0)` but 200 to a browser UA. Per curator-guide policy, ask each org's web admin for a WAF exception rather than spoofing.
- [ ] **River Arts District feed dead** — `riverartsdistrict.com/events/?ical=1` 403s ALL UAs (was 30 events). Contact or remove.
- [ ] **UNCA Music Dept feed** — currently 100% duplicative of main UNCA feed (2/2 events overlap, mid-summer). Recheck in fall; add only if it diverges.
- [ ] **Buncombe County Schools** — Apptegy/Thrillshare SPA (~45 school subdomains); every route serves a JS shell. Needs a browser session to extract the Thrillshare org ID, then probe `api.thrillshare.com`.
- [ ] **Empty Meetup feeds to recheck** (valid ICS, 0 events on 2026-07-16): art-circles, asheville-makers-pottery-clay-ceramic-arts, asheville-pastel-artists-meetup, whole-creative-living-collective, the-lobby-asheville-design-salon, asheville-rei-workshops-events, social-dance-club-swing-and-social-ballroom, open-heart-meditation-asheville, spirituality-asheville, carolinaactivechristians, asheville-gay-professionals-meetup-group, asheville-dining-out-meetup-group, asheville-short-story-club, vagabond-photo-walks, prime-focus-wnc-photography-community, asheville-language-exchange-english-spanish, asheville-travel-and-adventure-club.
- [ ] **Sly Grog Lounge** — Eventbrite organizer valid but 0 events now; recheck.
- [ ] **Little Jumbo** — `littlejumbobar.com/events?format=json` returns a clean bespoke JSON list (12 future) that squarespace.py doesn't parse; tiny custom scraper if wanted.
- [ ] **Warren Wilson Athletics** — Sidearm ICS valid but empty mid-summer; recheck in fall. **Mars Hill Athletics** (mhulions.com) — DNS failure during sweep; retry.
- [ ] **OLLI at UNC Asheville** — unca.edu/olliasheville TEC mini-calendar has 0 tagged events; course catalog is a Flipsnack PDF. Revisit if they publish structured events.

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
| One World Brewing | Cloudflare challenge blocks all fetches (32 events/30d via Where Y'at — covered) |
| Wicked Weed | Custom bot script; covered via Where Y'at |
| Trailside Brewing (Hendersonville) | Cloudflare |
| visithendersonvillenc.org | Simpleview, JS challenge; hendersonville.com MainStreet API is the better regional source |
| Asheville Symphony | Custom "Atlas" CMS, no structured data; 27 events via Where Y'at |
| Small bars with no calendar tech (Fleetwood's, 5 Walnut, Double Crown, Town Pump, The Crowbar, Off the Wagon, The Social, Lobster Trap, Banks Ave, Bush Farmhouse, Battery Park Book Exchange) | Social-media-only or static pages; all except Salvation Station covered via Where Y'at aggregator |
| Salvation Station | Website dead, no Songkick, not in Where Y'at |
| Wix JS-only venues (JuneBug, Sovereign Kava, Crow and Quill, Asheville Gallery of Art, Downtown AVL Arts, Kenilworth Residents Assoc, Trinity Episcopal, South Asheville Rotary) | Wix events widgets are client-rendered, no feed |
| Omni Grove Park Inn | Hotel entertainment schedule, no feed; covered via LiveMusicAsheville |
| Flat Rock Playhouse | Custom CMS, no JSON-LD |
| Black Mountain College Museum | WP Divi, no events plugin |
| Sierra Nevada Mills River | Custom site; 17 events via Where Y'at |
| Archetype / Hi-Wire breweries | No feeds found |
| 185 King Street (Brevard) | ~27 mi — outside 25 mi radius |
| LEAF Global Arts | Squarespace but no events collection found |
| Q-Hall Event Hub | Google Sites + GCal but calendar not public (404) |
| First Baptist Asheville | Events are unstructured blog posts, no dates in markup |
| Central UMC | Subsplash platform, JS calendar block, no public ICS |
| Jubilee! Community | MEC installed but ICS/REST disabled; calendar renders "no-events" server-side |
| Asheville Insight Meditation | TEC installed, 0 events (programs in a registration system) |
| Asheville Friends Meeting | Hand-built static HTML |
| Islamic Center of Asheville | Prayer-times widget only |
| Oakley / East West Asheville / North Asheville neighborhoods | Facebook/Nextdoor only |
| West Asheville Business Association | Vite JS SPA, client-rendered |
| League of Women Voters Asheville-Buncombe | 403 to curl and WebFetch (Cloudflare-class) |
| Asheville Area Habitat for Humanity | TEC present but feed/REST blocked; site refuses connections mid-probe (note: scrapers/habitat.py is Monroe County-specific) |
| United Way of Asheville-Buncombe | Drupal calendar essentially empty |
| Kiwanis / Lions clubs | Prose-only meeting info, no feeds |
| BeLoved Asheville | WP, no event listings |
| City of Hendersonville & Henderson County | Drupal, no ICS/RSS/JSON (hendersonville.com MainStreet API covers the area) |
| Town of Woodfin | Revize platform, proprietary calendar, no feed |
| Buncombe County Schools | Apptegy/Thrillshare JS shell (see To Investigate) |
| LibCal / TeamUp / guild.host / CampusLabs | Area sweeps 2026-07-16: zero viable calendars |
