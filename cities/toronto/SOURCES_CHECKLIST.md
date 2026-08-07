# Toronto Calendar Source Checklist

## Currently Implemented (132 sources)

### Aggregators
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| ~~NOW Magazine~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: `nowtoronto.com/events/?ical=1` serves a BigScoots WAF interstitial (HTML, 38 KB); re-probe occasionally and re-add if an ICS/REST export returns |
| Toronto Events (torevent) | Tockify ICS | ~2,899 | Music, comedy, film, nightlife — biggest source |

### Venues & Institutions
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Union Station | WordPress Tribe ICS | 18 | Art installations, music |
| Distillery District | Tockify ICS | 5 | Iconic venue programming |
| Gardiner Museum | WordPress Tribe ICS | 30 | Ceramics museum |
| Toronto Botanical Garden | WordPress Tribe ICS | 30 | Garden/nature programs |
| Textile Museum of Canada | WordPress Tribe ICS | 9 | |
| Bata Shoe Museum | WordPress Tribe ICS | 5 | |
| Aga Khan Museum | HTML scraper | 63 at add time | Homepage upcoming cards + detail pages; includes recurring BMO Wednesdays and announced TD Pop-Up performances |
| Japanese Canadian Cultural Centre | HTML scraper | 18 at add time | Drupal event listing + detail pages; expands multi-date programs like SakuraFest workshops into separate instances |
| Buddies in Bad Times Theatre | Tribe REST scraper | 7 via REST at conversion | LGBTQ+ theatre. Converted 2026-08-07: `?ical=1` served an HTML block page; SiteGround-protected — `--user-agent "Mozilla/5.0"` landed same day; local verification still hits the transient sgcaptcha interstitial under probe bursts, expect events from CI's quieter network path |
| ~~Factory Theatre~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: `?ical=1` endpoint dead (empty response locally and in Actions); feed row removed |
| High Park Nature Centre | Tribe REST scraper | 15 via REST at conversion | Outdoor/nature programs. Converted 2026-08-07: `?ical=1` served an HTML block page; SiteGround-protected — `--user-agent "Mozilla/5.0"` landed same day; expect events from CI's quieter network path |

### Ticketmaster Venues (via Discovery API)
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Scotiabank Arena | Ticketmaster scraper | ~631 | Raptors, Leafs, concerts |
| History | Ticketmaster scraper | ~127 | Music venue |
| Danforth Music Hall | Ticketmaster scraper | ~68 | Indie/rock concerts |
| Lee's Palace | Ticketmaster scraper | ~49 | Indie music |
| Massey Hall | Ticketmaster scraper | ~38 | Iconic concert hall |
| Horseshoe Tavern | Ticketmaster scraper | ~19 | Legendary music venue |
| Queen Elizabeth Theatre | Ticketmaster scraper | ~11 | Performing arts |
| Roy Thomson Hall | Ticketmaster scraper | ~8 | TSO home venue |

### Universities
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| University of Toronto | HTML scraper | 176 | Aggregate page + 32 department deep-links |
| UofT Engineering | WordPress Tribe ICS | 17 | |
| UofT Philosophy | WordPress Tribe ICS | 7 | |
| ~~UofT Social Work~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: `?ical=1` endpoint dead (empty response locally and in Actions); feed row removed. UofT Knox College retired the same day for the same reason |
| OCAD University | Listing/detail scraper | 12 at add time | Exhibitions, talks, senate meetings, creative entrepreneurship |
| York University | WordPress MEC ICS | 6,558 | Huge feed, pipeline filters by date |

### Music Venues
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Jazz Bistro | WordPress Tribe ICS | 24 | Live jazz performances |
| Grossman's Tavern | WordPress Tribe ICS | 30 | Live music |

### Community Organizations
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| CultureLink | WordPress Events Manager ICS | 494 | Newcomer/community events |
| Scadding Court Community Centre | Tribe REST scraper | 157 via REST at conversion | Converted 2026-08-07: `?ical=1` served an HTML block page; SiteGround-protected — `--user-agent "Mozilla/5.0"` landed same day; expect events from CI's quieter network path |
| St. Lawrence Neighbourhood Assoc. | Tockify ICS | 82 | Community meetings, markets, kids |
| Bloor West Village BIA | WordPress Tribe ICS | 6 | |
| Councillor Jamaal Myers | Tockify ICS | 27 | Scarborough community, city council |
| Show Up Toronto | iCal feed | TBD | Volunteering, mutual aid, civic organizing |
| Volunteer Toronto | HTML scraper | TBD | Volunteering opportunities and events |
| Toronto Public Library — Preschool | Bibliocommons scraper | 578 at split time | Exclusive audience feed on reusable TPL base |
| Toronto Public Library — School Age | Bibliocommons scraper | 602 at split time | Includes school-age-only plus mixed preschool/school-age events |
| Toronto Public Library — Teens | Bibliocommons scraper | 241 at split time | Exclusive audience feed on reusable TPL base |
| Toronto Public Library — Young Adults | Bibliocommons scraper | 159 at split time | Preferred over broad adult tags when both are present |
| Toronto Public Library — Adults | Bibliocommons scraper | 439 at split time | Adult-only events after young/older-adult routing |
| Toronto Public Library — Older Adults | Bibliocommons scraper | 539 at split time | Includes older-adult + adult combos |

### Crafts & Makers
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Repair Cafe Toronto | WordPress ICS | 82 | Community repair workshops across GTA |
| ~~Toronto Knitters Guild~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: `?ical=1` endpoint dead (empty response locally and in Actions); feed row removed |
| Toronto Tool Library | Shopify product scraper | 22 at sweep time | TTLMakerspace workshops at 192 Spadina; woodworking, sewing, leathercraft, CNC |
| Bistitchual | Shopify product scraper | 3 at sweep time | Yarn shop classes at 266 Jane St; knitting + crochet courses |
| Parkdale Pottery | Shopify product scraper | 2 at sweep time | Pottery workshops at Queen/Campbell studios |
| Site 3 CoLaboratory | WordPress Tribe ICS | 1 | Art/tech makerspace workshops |
| The Devil's Workshop | WordPress Events Manager ICS | 50 | Jewellery, glass fusing, silversmithing, lost wax casting, metal printmaking |
| Jewel Envy | Tribe REST scraper | 18 | Jewellery, enamel, metalwork, kids polymer clay. Converted 2026-08-07: `?ical=1` served HTML; Tribe REST works as-is (18 events on first run) |
| HackLab.TO | Public Google Calendar ICS | 1,104 (pipeline date-filters) | Toronto's hackerspace; open house Tuesdays, workshops, maker events |
| Queen City Stitch and Bitch | Meetup ICS | 10 | Fibre arts — knit, crochet, spin, weave, sew |
| Studio Mooi | Eventbrite organizer scraper | 2 | Pottery/craft workshops (Wix site, no own feed) |
| Open Studio (Printmaking Centre) | Eventbrite organizer scraper | 8 | Toronto's only artist-run printmaking centre (WP but no calendar plugin) |

### Gardening & Horticulture
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Green Neighbours Network of Toronto | WordPress Tribe ICS | 50 | Native plant walks, tree stewardship, community garden events |
| ~~GardenOntario (OHA)~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: `gardenontario.org/events/?ical=1` serves a Cloudflare "Just a moment" challenge; re-probe occasionally and re-add if an export returns |
| Etobicoke Horticultural Society | Squarespace per-event ICS scraper | 4 future | Monthly meetings, garden tours, plant sales |
| Toronto Master Gardeners | WordPress Tribe ICS | 15 | Demos at libraries, advice clinics, TBG presentations |
| Anga's Farm & Nursery | Squarespace per-event ICS scraper | 11 | Workshops: kokedama, pruning, floral design at 89 Bankfield Dr |

### Government & Public Affairs
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| City of Toronto Meetings | CKAN JSON scraper | 162 | Council, community councils, 56 committees |
| City of Toronto Festivals & Events | CKAN JSON scraper | 2,101 | Official city festival/event data, 37 categories |

### Science & Education
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| CITA Local Events | Public Google ICS | 339 | CITA/UofT science talks and local events |
| CITA Seminars | Public Google ICS | 1,089 | CITA seminar series (pipeline date filters apply) |
| CITA Special Events | Public Google ICS | 175 | CITA special event calendar |

### Outdoor & Nature
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| ~~Ontario Nature~~ | WordPress Tribe ICS | 0 | Retired 2026-08-07: Tribe REST route removed (`rest_no_route`) and `?ical=1` serves the 75,193-byte HTML block page; re-probe occasionally and re-add if an export returns |

### Literary & Bookstores
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Another Story Bookshop | Eventbrite organizer scraper | 16 upcoming at sweep time | Roncesvalles social-justice/diversity focus; migrating off eb-to-ical |
| Ben McNally Books | Eventbrite organizer (eb-to-ical) | active | Downtown indie; Fresh Off The Press book club + open mic + launches |
| Glad Day Bookshop | Eventbrite organizer scraper | active | World's oldest LGBTQ+ bookstore; drag brunches, readings, fundraisers; migrating off eb-to-ical |
| Hopeless Romantic Books | Eventbrite organizer (eb-to-ical) | active | Romance specialty; monthly hybrid book club |
| Queen Books | Eventbrite organizer (eb-to-ical) | currently dormant | Leslieville general indie; live source is Bookmanager scraper below |
| Book*hug Press | Eventbrite (filtered) | 7 | Literary press; launches across Toronto venues |
| Coach House Books | Eventbrite (filtered) | 63 | Literary press (60 yrs); launches at Society Clubhouse |
| Cormorant Books | Eventbrite (filtered) | 31 | Literary press; events at Ben McNally, Sleuth, etc. |
| Penguin Random House Canada | Eventbrite (filtered) | 70 | Big-five Canadian arm |
| HarperCollins Canada | Eventbrite (filtered) | 37 | Big-five publisher |
| Simon & Schuster Canada | Eventbrite (filtered) | 13 | Big-five publisher |
| Diaspora Dialogues | Eventbrite (filtered) | 113 | Toronto literary org; reading series, mentorship |
| House of Anansi | Eventbrite (filtered) | 5 | Toronto literary press; Poetry Bash series at Henderson Brewing |
| Bakka Phoenix Books | Bookmanager scraper | 1 | SF/F specialty (since 1972); `scrapers/bookmanager.py --san 1684035` |
| Flying Books | Bookmanager scraper | 12 | College St + Neverland; biggest Bookmanager haul; book clubs + launches |
| Ben McNally Books (Bookmanager) | Bookmanager scraper | 9 | Complements Eventbrite feed: BMB Book Club + publisher launches |
| Queen Books (Bookmanager) | Bookmanager scraper | 8 | Currently the live source for Queen Books events |
| A Different Booklist | Bookmanager scraper | 4 | Black-owned, Annex; covers events not on a Bookstore organizer page |

### Outdoor Recreation Clubs
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Toronto Bicycling Network | Wild Apricot RSS scraper | ~143 in-range | Hiking, cycling, walks, skating, skiing via `scrapers/toronto_bicycling_network.py` |

### Meetup Groups (49 groups)
| Group | Events | Category |
|-------|--------|----------|
| SAI Dham Canada Toronto Volunteer Group | 10 | Volunteering / mutual aid |
| Toronto Dads Group | 10 | Kids / family |
| Little Sunbeams (Parents + Tots) | 10 | Kids / family |
| Mini + Me Meetups | 10 | Kids / family |
| TorontoBabel | 10 | Language exchange |
| Try New Things in Toronto | 10 | Social/activities |
| Toronto Arts & Culture | 10 | Arts outings |
| These Boots Are Made for Hiking | 5 | Hiking |
| Toronto Bike Meetup | 10 | Cycling |
| Board Games and Social | 10 | Board games |
| Salsa/Bachata/Kizomba GTA | 10 | Dance |
| Toronto Photography Group | 3 | Photography |
| A Book Club Downtown | 4 | Book club |
| Improv, Acting, Nature Walks | 4 | Comedy/improv |
| TechTO | 2 | Tech |
| Toronto JavaScript | 1 | Tech |
| Python Toronto | 1 | Tech |
| Founders Running Club Toronto | 10 | Running |
| High Park Yoga | 10 | Outdoor yoga |
| Mindful Movement Toronto | 10 | Outdoor yoga/wellness |
| Toronto Wellness | 10 | Yoga, meditation, wellness |
| Toronto SUP, Kayak & Canoe | seasonal | Water sports |
| Toronto Paddlers | seasonal | Waterfront kayaking |
| Toronto Canoe Trippers | seasonal | Canoe expeditions |
| 20s 30s Toronto Social | 10 | Social |
| Soul City Social Club | 10 | Social |
| Experience Toronto | 7 | Arts/culture |
| Hiking Network | 3 | Hiking |
| GTA Hiking & Stuff | 1 | Hiking |
| Toronto Bruce Trail Club | 1 | Hiking |
| Wilderness Union | 2 | Outdoors |
| Toronto Heavy Boardgamers | 10 | Board games |
| Toronto Movies & Social | 10 | Film |
| Sci Fi Book Club | 6 | Book club |
| Post-Apocalyptic Book Club | 2 | Book club |
| Silent Book Club | 1 | Book club |
| Toronto Japanese English Exchange | 10 | Language |
| Language Exchange Toronto | 10 | Language |
| TILE Language Party | 5 | Language |
| Improv For New Friends | 2 | Improv |
| Toronto AI & ML | 10 | Tech |
| Microsoft Reactor Toronto | 10 | Tech |
| Toronto Tech Stack Exchange | 10 | Tech |
| Toronto Enterprise DevOps | 3 | Tech |
| Toronto Postgres | 2 | Tech |
| Toronto Women in Business | 2 | Business |
| Toronto 20s-50s Singles Social | 2 | Social |
| Toronto 3D Printing | 10 | Makers/3D printing |
| Midtown Arts & Crafts | 1 | General crafts |

## Maintenance Log

### 2026-08-07 clean pass (soak report `reports/toronto-2026-08-07-soak.md`)

- **DB metadata sync** (`backfill_scraper_feeds.py --city toronto --sync-existing`): retired 14 legacy URL-keyed scraper rows that duplicated workflow producers (A Different Booklist, Bakka Phoenix Books, Ben McNally Books, Queen Books, Flying Books, blogTO, and the 8 Eventbrite publishers below). These rows dated from the pending_feeds era, were keyed by website URL instead of output path, and corrupted local audit builds (they exported as bogus live feeds; the blogTO row's HTML download clobbered the real scraper's output). Also normalized 3 display names from output `X-SOURCE`: University of Toronto, City of Toronto Meetings, City of Toronto Festivals & Events.
- **Eventbrite publishers converted off eb-to-ical** (dead since 2026, HTTP 404): `scrapers/eventbrite_filtered.py` now scrapes Eventbrite directly via organizer page + JSON-LD; all 8 workflow lines switched from `--organizer <id>` to `--url "<organizer page>"`; DB `scraper_cmd` synced. See the publisher-feed section update below.
- **Dead live ICS endpoints retired** (empty/failed in both local and Actions runs, 0 events in DB for each): Cecil Community Centre, Factory Theatre, Toronto Knitters Guild, UofT Knox College, UofT Social Work — feed rows removed via `remove_feed`.
- **Aga Khan Museum parser fix**: `scrapers/agakhan_museum.py` now handles decorated date labels ("Doors Open • May 23, 2026"), multi-showtime labels ("August 28 • 8 pm August 29 • 8 pm August 30 • 2 pm"), and year-less dates ("November 18", next-occurrence inference). All three recurring parse warnings gone; 62 events on the verification run (previously 15, with the TD Pop-Up and Ali Sethi pages contributing nothing).
- **Left open for review at soak time**, adjudicated later the same day — see the next entry.

### 2026-08-07 adjudication of the HTML-serving feeds and environment splits

- **Converted to `scrapers/tribe_rest.py`** (old `?ical=1` rows removed via `remove_feed`, all four had 0 events in the DB): Buddies in Bad Times Theatre (REST total 7), High Park Nature Centre (15), Scadding Court Community Centre (157), Jewel Envy (18). Jewel Envy produced 18 events immediately. The other three are SiteGround-hosted: their REST APIs hard-403 tribe_rest.py's default UA (and a full fake-Chrome UA) but accept a plain `Mozilla/5.0`, with a transient `/.well-known/sgcaptcha/` interstitial under bursts. The `--user-agent` override landed in `scrapers/tribe_rest.py` the same day and the three workflow lines (plus DB commands) now pass `--user-agent "Mozilla/5.0"`; local verification afterward still hit the sgcaptcha interstitial (this network had been probing in bursts), so first real event counts are expected from CI's quieter network path — check the next GitHub run.
- **Retired** (feed rows removed via `remove_feed`, 0 events each; re-probe occasionally and re-add if a machine-readable export returns): Toronto Dance and Ontario Nature (Tribe REST route removed — `rest_no_route` — and `?ical=1` serves the shared 75,193-byte HTML block page), NOW Toronto (BigScoots WAF interstitial), GardenOntario (Cloudflare challenge).
- **Accepted environment splits — policy, no mechanical change (2026-08-07)**:
  - blogTO: 403 from GitHub Actions IPs; works locally (1016 events on 2026-08-07). Keep the producer; CI contribution is 0 until the block lifts or a proxy decision is made.
  - York University feed (`events.yorku.ca` MEC ICS): failed upstream on 2026-08-07 while yielding 6,958 raw events locally. Keep; watch upstream runs.
  - UofT sub-calendars: 7 sub-calendars 403 in CI vs 1 locally; the aggregate scraper still produced 74 events upstream. Keep as-is.
  - Trinity College (within UofT scraper): SSL verification broken in both environments — stays an **open review item**.
- **Quiet-source queue (A008)**: the ~30 valid-but-quiet zero-event sources (16 Meetup feeds, 9 Eventbrite organizers, 4 Luma collections, TCDSB Meetings, City Planning Consultations) stay **keep-watching** by default; no retirements without evidence of upstream death.

## Needs Further Assessment

- ~~**Toronto Public Library**~~ — split into six audience-specific scrapers on 2026-04-16 so library events stay findable by audience without duplicating multi-tagged programs across feeds.
- ~~**BlogTO**~~ — Implemented as `scrapers/blogto.py`. Uses public `/api/v2/events/?date=YYYY-MM-DD&bundle_type=medium` listing endpoint (no per-event fetch). Walks day-by-day, dedupes by event id, stops after 7 empty days.
- **Explore Kids Ontario Adventures** — Tockify feed (`ekoad`) has 822 events but covers broader GTA/Ontario, not just Toronto. May need geo-filtering.
- ~~**Toronto Bicycling Network**~~ — Implemented as `scrapers/toronto_bicycling_network.py`. Wild Apricot RSS source with strong outdoor recreation coverage.
- ~~**Cecil Community Centre**~~ — AI1EC export feed was confirmed live on 2026-04-15, but by 2026-08-07 the endpoint no longer downloads (fails locally and in Actions). Feed row removed 2026-08-07.
- **Lula Lounge** — Eventbrite organizer `19825205758`; staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **The Rosedale Centre** — Eventbrite organizer `83757475743`; staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Hand Eye Society** — Eventbrite organizer `15539055266`; staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Forest Bathing Club** — Eventbrite organizer `68086018103`; staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Book Club Toronto** — Eventbrite organizer `113996803611`; staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Toronto's First Post Office** — Eventbrite organizer `7903835251`; public-history lectures/tours, staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Fuzzy Lab Toronto** — Eventbrite organizer `102501807981`; tufting/craft workshop source, staged as `scrapers/eventbrite.py` entry in workflow + `pending_feeds.txt` on 2026-04-15.
- **Ghost Rocket** — promising makerspace/community workshops; needs direct site/platform assessment.
- **Mischief Makers** — promising family maker/craft programming; likely Amilia-backed and worth a separate pass.
- **The Pottery** — promising pottery-workshop schedule pages at `thepottery.ca`; likely scrapeable but not yet wired.
- **Clay Design** — promising pottery classes/workshops at `claydesign.ca`; schedule exists, needs site-level inspection.
- **City Planning Consultations** — implemented locally as `scrapers/toronto_planning_consultations.py` on reusable `scrapers/lib/social_pinpoint.py`. Validated at 13 future meetings and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **City of Toronto Public Consultations** — wrapper implemented locally as `scrapers/toronto_public_consultations.py`, but not staged because the current `/events` page is a 1:1 duplicate of the planning feed (same 13 upcoming titles/times) and would create redundant raw events.
- **Toronto Catholic District School Board Meetings** — implemented locally as `scrapers/tcdsb_meetings.py` on reusable `scrapers/lib/escribe.py`. Validated at 1 future meeting and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Toronto District School Board Meetings** — implemented locally as `scrapers/tdsb_meetings.py` on reusable `scrapers/lib/escribe.py`, but not staged because the public calendar currently returns 0 future meetings while regular Board meetings are paused.
- **Metrolinx Board** — implemented locally as `scrapers/metrolinx_board.py`. Uses the published upcoming meeting dates on the official board page and stages them as all-day board meetings. Validated at 2 in-range future meetings with the default six-month horizon and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Waterfront Toronto** — implemented locally as `scrapers/waterfront_toronto.py`. Parses the embedded Drupal calendar payload on `/events` and captures future board meetings and public consultations. Validated at 13 in-range future events and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Toronto Community Housing** — implemented locally as `scrapers/toronto_community_housing.py`. Scrapes the official Drupal event listing for board/committee meetings and tenant events. Validated at 5 current/future events and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **The Annex Residents' Association** — implemented locally as `scrapers/the_annex_residents_association.py`. Synthesizes monthly board meetings from the association’s published recurring schedule (“second Thursday of every month, excluding July and August, at 7:00 p.m.”). Validated at 4 in-range future meetings and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Harbord Village Residents' Association** — implemented locally as `scrapers/harbord_village.py`. Parses the published `Calendar of HVRA events for 2026` page for board meetings, general meetings, and major neighborhood events with explicit dates/times. Validated at 7 in-range future events and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Bathurst Quay Neighbourhood Association** — strong next candidate. The public event page publishes exact 2026 board-meeting dates plus recurring neighborhood programming, but current HTML does not expose a meeting time cleanly enough to wire tonight without guesswork.
- **Waterfront BIA** — implemented locally as `scrapers/waterfront_bia.py`. Uses the public sitemap to enumerate `/events/*` pages, then parses each detail page’s visible Date/Time/Location blocks. Validated at 11 in-range future events and staged in workflow + `pending_feeds.txt` on 2026-04-16.
- **Cabbagetown Preservation Association** — strong next candidate. The Squarespace `events/` section clearly advertises recurring tours/talks, but needs a proper listing/detail scrape rather than a quick feed probe.
- **Church-Wellesley Neighbourhood Association** — plausible next candidate. The board page states that monthly meetings are open to the public, but the cadence is “second or third Saturday” and would need either a live calendar scrape or a deliberately synthetic rule.
- **Luma Toronto Discover** — public citywide ICS feed confirmed from [luma.com/toronto](https://luma.com/toronto) via `https://api2.luma.com/ics/get?entity=discover&id=discplace-Cx3JMS6vXKAbhV5`. Switched from raw-feed staging to a dedicated `scrapers/luma.py` adapter on 2026-04-18 so the pipeline can lift per-event Luma links out of `DESCRIPTION` and write them into the ICS `URL` field before generic ingestion. Validated at 49 current VEVENTs and staged in workflow + `pending_feeds.txt`.
- **Pluto Toronto** — implemented on 2026-04-19 as the first Luma collection-page source via `scrapers/luma_collection.py` against `https://luma.com/plutotoronto`. The initial JSON-LD teaser only exposed 4 near-term events, but the scraper now derives Luma's public `calendar_api_id` from the collection page and walks the paginated `calendar/get-items` endpoint instead. Current validation yields 24 future events with explicit per-event `URL` fields, including `Celestial Night Prom`, and 0 URL overlap with the current Toronto Discover feed.
- **Toronto Social Mixer** — staged on 2026-04-19 as the second Luma collection-page source via `scrapers/luma_collection.py` against `https://luma.com/TorontoSocialMixer`. Current validation yields 1 future event with an explicit per-event `URL` field and 0 URL overlap with both Toronto Discover and Pluto Toronto.
- **Japanese Canadian Cultural Centre** — implemented on 2026-04-19 as `scrapers/jccc.py`. The public Drupal listing at `/visit/events` already exposes date blocks for each occurrence, while detail pages provide descriptions, taxonomy labels, and an embedded iCal data URI for location. Current validation yields 18 current/future event instances, including both dates for the two-part SakuraFest field-recording workshop, and stages cleanly in workflow + `pending_feeds.txt`.
- **TechTO Events** — staged on 2026-04-19 as the third Luma collection-page source via `scrapers/luma_collection.py` against `https://luma.com/TechTO-Events`. Current validation yields 10 future events, 6 net-new URLs versus Toronto Discover + Pluto + Toronto Social Mixer, and 8 Toronto-local-looking locations. This source still carries some Vancouver spillover and overlaps the existing TechTO Meetup source, so it is useful but not as clean as Pluto.
- **Uplift Collective** — staged on 2026-04-19 from the Yelp/venue discovery pass via `scrapers/luma_collection.py` against `https://luma.com/upliftcollective`. Current validation yields 7 future events after the six-month cutoff, all 7 net new versus Toronto Discover + Pluto + Toronto Social Mixer + TechTO Events, with all current locations Toronto-local-looking.
- **again again** — staged on 2026-04-19 via `scrapers/luma_collection.py` against `https://luma.com/againagain`. Current validation yields 3 future events, 1 net-new URL versus the staged Toronto Luma set, and all current locations Toronto-local-looking.
- **airess** — staged on 2026-04-19 via `scrapers/luma_collection.py` against `https://luma.com/airess`. Current validation yields 2 future events, 1 net-new URL versus the staged Toronto Luma set, and both current locations Toronto-local-looking.
- **UTE** — staged on 2026-04-19 via `scrapers/luma_collection.py` against `https://luma.com/ute`. Current validation yields 3 future events, 1 net-new URL versus the staged Toronto Luma set, and 2 clearly Toronto-local locations.
- **Luma sub-calendars (validated, mostly not staged separately yet)** — several Toronto-local calendars expose working ICS feeds, but they substantially overlap the citywide discover feed, so they are better treated as follow-on additions only if we want more depth from specific communities. Best validated calendars: University of Toronto Entrepreneurship (`18`), again again (`21`), KNIGHTCAP Toronto (`15`), airess (`8`), Cursor Toronto (`9`), Threat Modeling Connect Toronto (`5`). TechTO also has a working Luma feed (`63`) but includes out-of-city events like Vancouver and already overlaps an implemented Meetup source. Toronto Tech Week has a working Luma feed too, but it is seasonal and very noisy (`423` VEVENTs).
- **Luma collection-page inventory** — candidate Toronto Luma hosts now live in [LUMA_HOSTS.md](./LUMA_HOSTS.md). `luma.com/plutotoronto`, `luma.com/TorontoSocialMixer`, `luma.com/TechTO-Events`, `luma.com/upliftcollective`, `luma.com/againagain`, `luma.com/airess`, and `luma.com/ute` are now staged via the reusable collection scraper. Broader/noisier follow-ons include `CloudCanada`, `genai-collective`, and `torontotechweek`.
- **Toronto Tech Week** — staged on 2026-04-21 via `scrapers/luma_collection.py` against `https://luma.com/torontotechweek`. Current validation yields 186 future events (April 23 – May 30, concentrated around Tech Week May 25-30). Seasonal and large but users can filter or turn off the feed. Previously flagged as noisy in LUMA_HOSTS.md but added for completeness.
- **Yelp-derived Luma follow-ons (assessed 2026-04-19)** — the venue-led pass through Yelp-surfaced brands found `Uplift Collective` as the strongest new collection add. `Saute Sundays Toronto Cookbook Club` is real but only adds 1 net-new event right now, while `THAT SLOW JAM PARTY` and `LevelUp Society` currently have 0 future events on their collection pages.

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Facebook Events | No public API since 2018 |
| Bandsintown | 403 errors, no public feed |
| Destination Toronto | Uses Cruncho widget, no feeds |
| Toronto.com RSS | Rate limited (429) |
| Eventbrite | No public feeds; API requires OAuth key |
| Exclaim! | Events section returns 404 |
| AllEvents.in | No feeds, web-only |
| AGO | Cloudflare protected (403) |
| ROM | 404 on events page |
| TIFF | No ICS/RSS found |
| Mirvish | No feed found |
| Harbourfront Centre | RSS feed exists but empty |
| ~~Massey Hall / Roy Thomson Hall~~ | ~~404~~ **Implemented** via Ticketmaster Discovery API |
| Canadian Opera Company | 526 error |
| do416.to | No feed |
| To Do Canada | 403 Forbidden |
| Songkick Toronto | No public feeds |
| Dice.fm | No Toronto page |
| Resident Advisor | 403 |
| The Rex | Squarespace but not events collection type |
| ~~Horseshoe Tavern~~ | ~~Webflow, no feed~~ **Implemented** via Ticketmaster Discovery API |
| ~~Lee's Palace~~ | ~~Custom app, no feed~~ **Implemented** via Ticketmaster Discovery API |
| ~~Danforth Music Hall~~ | ~~Custom Chakra UI app, no feed~~ **Implemented** via Ticketmaster Discovery API |
| TSO | No feed found |
| Canadian Stage | No WordPress Tribe ICS |
| Tarragon Theatre | No WordPress Tribe ICS |
| Hot Docs | No WordPress Tribe ICS |
| ~~Aga Khan Museum~~ | ~~No WordPress Tribe ICS~~ **Implemented** via `scrapers/agakhan_museum.py` |
| Power Plant Gallery | No WordPress Tribe ICS |
| MOCA Toronto | No WordPress Tribe ICS |
| The 519 | WordPress but no Tribe Events plugin |
| ~~Lula Lounge~~ | ~~No feed~~ **Eventbrite organizer found; staged as `scrapers/eventbrite.py` source** |
| Tranzac | No feed |
| 918 Bathurst | No feed |
| Luminato Festival | No feed |
| Music Gallery | No feed |
| Small World Music | No feed |
| Scarborough Arts | No feed |
| TMU | No ICS feed (custom CMS, likely scrapeable but needs a scoped source decision) |
| TRCA | Events on Eventbrite only; no ICS/RSS for events |
| Tommy Thompson Park | Links to TRCA calendar; no own event feed |
| Rouge National Urban Park | No calendar; page says "check back soon" |
| Ontario Place | WordPress Tribe installed but ICS returns empty |
| Evergreen Brick Works | WordPress but no Tribe/MEC; no feeds |
| Toronto Outdoor Club | Custom ASP.NET, no feeds |
| Bruce Trail Conservancy (Toronto) | ECWD calendar plugin, no ICS endpoint |
| Toronto Field Naturalists | Members-only content, no public feed |
| Dragon Boat Canada | MEC installed but ICS returns HTML |
| Cycle Toronto | NationBuilder, no feeds |
| Downsview Park | Drupal, no feeds (30+ events but would need scraper) |
| City of Toronto (toronto.ca) | No Legistar; TMMIS behind Akamai WAF (403). Meeting data available via CKAN instead |
| Ontario Legislature | 403 on calendar page; no ICS/RSS |
| Toronto Police Services Board | Joomla, no feeds (~9 meetings/year) |
| TTC Board | Moved to TMMIS; likely scrapeable via TTC index + `report.do` pages, but not yet implemented |
| ~~Metrolinx Board~~ | ~~No feed, but official board page is a viable static HTML scrape candidate~~ **Implemented** as `scrapers/metrolinx_board.py` |
| TDSB | Public eScribe JSON exists, but current future calendar is effectively empty while regular Board meetings are paused |
| ~~Waterfront Toronto~~ | ~~No feed, but `/events` is a viable HTML scrape candidate~~ **Implemented** as `scrapers/waterfront_toronto.py` |

---

## Research Log

### 2026-02-14: Initial research + full discovery pass

**Discovery methods used:**
- DuckDuckGo platform searches (Tockify, Localist, WordPress Tribe)
- Direct WordPress `?ical=1` probing on Toronto venue/org sites
- Meetup group discovery across 13+ categories
- Aggregator assessment (BlogTO, NOW, City of Toronto, etc.)
- Topical searches: outdoor activities, government/public affairs, crafts/makers
- City of Toronto open data portal (CKAN API)

**Key finds:**
- **torevent** Tockify calendar: ~2,900 Toronto events — single biggest source
- **CultureLink**: 494 community/newcomer events via WordPress Events Manager
- **York University**: 6,558 events via WordPress MEC
- **University of Toronto**: 176 events via custom scraper + 3 department ICS feeds
- **Ontario Nature**: 11 events via WordPress Tribe
- **City of Toronto CKAN**: meeting schedule (162 future meetings) + festivals/events (2,101 future) via new CKAN base scraper
- **Repair Cafe Toronto**: 82 community repair workshops
- **49 Meetup groups** with active ICS feeds across social, arts, hiking, cycling, dance, games, books, comedy, tech, language, yoga, water sports, running, film, improv, business, makers, crafts, and kids/family

**Total: 80 sources, ~9,200+ events**

**Infrastructure built:**
- `scrapers/lib/ckan.py` — reusable CKAN datastore API base scraper (pagination, filters)
- `scrapers/lib/bibliocommons.py` — reusable Bibliocommons events API base scraper (entity mapping + filter hooks)
- `scrapers/lib/tpl_audiences.py` — TPL audience router on top of Bibliocommons so six audience feeds stay exclusive
- `scrapers/toronto_meetings.py` — City of Toronto meetings via CKAN
- `scrapers/toronto_festivals.py` — City of Toronto festivals via CKAN JSON
- `scrapers/uoft_events.py` — UofT aggregate page + 32 department deep-links
- `scrapers/toronto_public_library.py` — aggregate TPL scraper kept for ad hoc checks
- `scrapers/toronto_public_library_{preschool,school_age,teens,young_adults,adults,older_adults}.py` — audience-specific TPL wrappers

---

## Topical Searches

Track progress on topical searches to find long-tail community sources.

### Completed

| Topic | Date | Sources Added | Notes |
|-------|------|---------------|-------|
| Outdoor activities | 2025-02-14 | (included in initial Meetup sweep) | Hiking, cycling, water sports |
| Government/public affairs | 2025-02-14 | toronto_meetings.py, toronto_festivals.py | CKAN open data |
| Crafts/makers | 2025-02-14 | Repair Cafe, Knitters Guild, Site 3, 3D printing | Initial sweep |
| Crafts/makers (expansion) | 2026-04-16 | Devil's Workshop, Jewel Envy, HackLab.TO, Queen City Stitch & Bitch, Studio Mooi, Open Studio | Meetup + Eventbrite + venue probe; see dedicated section below |
| Volunteering/mutual aid | 2025-02-15 | Show Up Toronto, SAI Dham Volunteer, Volunteer Toronto scraper | |
| Kids/family | 2025-02-15 | Toronto Dads, Little Sunbeams, Mini+Me Meetups, TPL preschool/school-age/teens feeds | Bibliocommons base |
| History/heritage | 2025-02-15 | Ontario Historical Society, Toronto History Walks, Medieval SCA | 25 events |
| Science/education | 2026-02-15 | CITA Local Events, CITA Seminars, CITA Special Events | 3 public Google ICS feeds from CITA calendar page |
| Literary / bookstores | 2026-04-11 | 5 store organizers (Another Story, Ben McNally, Glad Day, Hopeless Romantic, Queen Books) + 4 publisher organizers (Coach House, Cormorant, Book*hug, Penguin Random House Canada) | Deep-dive into Toronto's indie bookstore scene; see dedicated section below |
| Gardening / horticulture | 2026-04-16 | GNN, GardenOntario, Etobicoke Hort Society | See dedicated section below |
| Comedy / improv | 2026-04-16 | (assessed, not wired) | Venues inventoried; mostly Eventbrite-only. See dedicated section below |
| Food / drink | 2026-04-16 | (assessed, low yield) | Farmers markets + cooking studios inventoried; mostly Shopify/custom. See dedicated section below |

### Not Yet Done

- Faith / spiritual
- Seniors
- LGBTQ+ community
- Music participation (choirs, jam sessions, open mics)

---

## Topical Search: Volunteering / Mutual Aid (2025-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| Show Up Toronto | ICS feed | `showuptoronto.ca/static/showupto.ics` |
| SAI Dham Canada Toronto Volunteer | Meetup ICS | Volunteer group |
| Volunteer Toronto | Scraper | `scrapers/volunteer_toronto.py` |

### Screened Out

| Source | Reason |
|--------|--------|
| Volunteer MBC | Regional beyond Toronto |
| VolunteerConnector | Ontario-wide, too broad |

---

## Topical Search: Kids / Family (2025-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| Toronto Dads Group | Meetup ICS | `meetup.com/torontodadsgroup/events/ical/` |
| Little Sunbeams | Meetup ICS | Parents + Tots meetup |
| Mini + Me Meetups | Meetup ICS | `meetup.com/mini-me-meetups/events/ical/` |
| Toronto Public Library — Preschool | Scraper | `scrapers/toronto_public_library_preschool.py` on TPL audience base |
| Toronto Public Library — School Age | Scraper | `scrapers/toronto_public_library_school_age.py` on TPL audience base |
| Toronto Public Library — Teens | Scraper | `scrapers/toronto_public_library_teens.py` on TPL audience base |
| Toronto Public Library — Young Adults | Scraper | `scrapers/toronto_public_library_young_adults.py` on TPL audience base |
| Toronto Public Library — Adults | Scraper | `scrapers/toronto_public_library_adults.py` on TPL audience base |
| Toronto Public Library — Older Adults | Scraper | `scrapers/toronto_public_library_older_adults.py` on TPL audience base |

### Promising (Needs Work)

| Source | Notes |
|--------|-------|
| Jane/Finch Centre | Has per-event iCal links, not clean single feed |

### Screened Out

| Source | Reason |
|--------|--------|
| Kids Out and About Toronto | Promotional listing site, not producer-authoritative |

---

## Topical Search: History / Heritage (2025-02-15)

### Added

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Ontario Historical Society | `ontariohistoricalsociety.ca/events/?ical=1` | 5 | WordPress Tribe; province-wide, includes Toronto Postcard Club, Canada Black Music Archives |
| Toronto History Walks | `meetup.com/the-history-of-parkdale/events/ical/` | 10 | Walking tours: cemeteries, neighborhoods, interactive games |
| Medieval Renaissance Toronto SCA | `meetup.com/Medieval-Renaissance-Toronto-Royal-Citie-of-Eoforwic-SCA/events/ical/` | 10 | Medieval arts, science, dancing |

### Meetup Groups Assessed

| Group | Members | Events | Status |
|-------|---------|--------|--------|
| Toronto History Walks | 8,781 | 10 | ✅ Added |
| Medieval Renaissance Toronto SCA | 172 | 10 | ✅ Added |
| Hidden History Toronto! Walking Tours | 9,597 | n/a | Feed/group slug now returns 404 `Group not found` (checked 2026-02-15) |
| History Discussion Group | 3,586 | 0 | No current events |
| Eglinton History Salon | 266 | 0 | No current events |
| Toronto African Diaspora History Walking Tours | 63 | 0 | No current events |
| The Long Conversation | 16 | 0 | Philosophy/history |

### Organizations Assessed

| Organization | Feed Status | Notes |
|--------------|-------------|-------|
| Ontario Historical Society | ✅ ICS works | Province-wide heritage org |
| Heritage Toronto | No feed | Tours seasonal (June-Nov) |
| ACO Toronto | No feed | Annual symposiums |
| City of Toronto History Museums | No feed | 61 events on website |
| Toronto Historical Association | Inactive | Last events 2016 |

### Non-Starters

| Source | Reason |
|--------|--------|
| Toronto Family History (OGS) | Cloudflare protected |
| Casa Loma | Static site, RSS empty since 2018 |
| Fort York tickets | 404 error |
| Heritage Toronto tours | Seasonal only (June-Nov) |

---

## Topical Search: Science / Education (2026-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| CITA Local Events | Public Google ICS | `calendar.google.com/.../qfg129sn6k25ah00ioakus0gds.../public/basic.ics` |
| CITA Seminars | Public Google ICS | `calendar.google.com/.../4h7dspldpuviiv4o1slj9o5p5c.../public/basic.ics` |
| CITA Special Events | Public Google ICS | `calendar.google.com/.../d7muv9fjli72io6q1a7hkdpf04.../public/basic.ics` |

### Organizations Assessed

| Organization | Feed Status | Notes |
|--------------|-------------|-------|
| Canadian Institute for Theoretical Astrophysics (CITA) | ✅ 3 ICS feeds | Feed links available on event calendar page |
| RASC Toronto Centre | No feed found | Site does not expose ICS endpoint |
| Ontario Science Centre | No feed found | Event pages, no ICS/RSS endpoint identified |
| UofT Physics | No feed found | No working `?ical=1` endpoint |

### Meetup Groups Assessed

| Group | Events | Status |
|-------|--------|--------|
| Cognitive Toronto | 0 | Valid ICS, no upcoming events |
| Toronto Data Workshop | n/a | 404 `Group not found` |
| RASC Toronto Centre (Meetup slug) | n/a | 404 `Group not found` |

---

## Topical Search: Broad Web Scan (2026-02-23)

### New ICS Feeds Found

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Sunshine Centres for Seniors | `sunshinecentres.com/events/?ical=1` | 15 | Senior programs across multiple Toronto locations |
| GO Latin Dance | `golatindance.com/events/?ical=1` | 30 | Salsa, bachata, kizomba events (Dovercourt House) |
| Boulderz Climbing | `boulderzclimbing.com/events/?ical=1` | 6 | Climbing gym events |
| ~~Toronto Dance~~ | `torontodance.com/events/?ical=1` | 0 | Retired 2026-08-07: Tribe REST route removed (`rest_no_route`) and `?ical=1` serves the 75,193-byte HTML block page; re-probe occasionally and re-add if an export returns |
| Toronto Choir | `torontochoir.org/events/?ical=1` | 1 | Community choir (small feed) |

### RSS Feeds (needs RSS-to-ICS conversion)

| Source | RSS URL | Events | Notes |
|--------|---------|--------|-------|
| Toronto Bicycling Network | `tbn.ca/events/RSS` | 50+ | Wild Apricot RSS; hiking, cycling, walks, skating, skiing. Previously identified in Needs Further Assessment, now confirmed 50+ events. |

### Promising Scraping Opportunities

| Source | URL | Notes |
|--------|-----|-------|
| YOHOMO | `yohomo.ca/events` | LGBTQ+ events aggregator - calendar page, would need scraper |
| Harbourfront Centre | `harbourfrontcentre.com/whats-on/` | Major venue, WP Engine site, likely has JSON API |
| Toronto Zoo Events | `torontozoo.com/events/` | Custom site, would need scraper |
| ROM Events | `rom.on.ca/whats-on/events` | Drupal site, may have JSON endpoint |
| Toronto Arts Council | `torontoartscouncil.org/events/` | WordPress, grant deadlines and arts events |
| Centre for Social Innovation | `socialinnovation.org/where-change-happens/events/` | Community/coworking/social enterprise events |
| TRCA Events | `trca.ca/events-calendar/` | Conservation authority nature events |
| The 519 | `the519.org/events/` | LGBTQ+ community centre (already in Non-Starters but worth re-checking) |

### Assessed - Non-Starters

| Source | Reason |
|--------|--------|
| Toronto Junction BIA | WordPress but not Tribe calendar plugin |
| Chinatown BIA | 404 on ICS endpoint |
| Toronto Dance Salsa | Cloudflare protected (403) |
| Jazz Near You Toronto | 403 Forbidden |
| 365 Etobicoke | WordPress but no ICS |
| Toronto Shambhala Meditation | Cloudflare challenge |
| Toronto Running Club | Custom site, 404 on events |
| Amadeus Choir | WordPress but no ICS |
| Annex Singers | 404 on ICS |
| Echo Women's Choir | 404 on ICS |
| Fire Mics (open mics) | Custom site, no ICS |
| Archdiocese of Toronto | 404 on ICS |
| Diocese of Toronto (Anglican) | HTML only |
| MCC Toronto | HTML only |
| Toronto Mass Choir | HTML only |
| Toronto Urban Growers | 404 on ICS |
| Museum of Toronto | HTML only |
| TRSL (Rec Sports) | 404 on events |
| XTSC | 404 on events |
| Community Living Toronto | HTML only |
| The Disability Collective | Wix site |

### Categories Explored

- Seniors (✅ Sunshine Centres)
- LGBTQ+ (scraper opportunity: YOHOMO, The 519)
- Dance (✅ GO Latin Dance, Toronto Dance)
- Climbing/Outdoor (✅ Boulderz)
- Cycling (RSS: TBN)
- Faith/Spiritual (no good feeds found)
- Music/Choir (small: Toronto Choir)
- Food & Drink (no feeds found - mostly Eventbrite)
- Comedy/Open Mic (no feeds found - mostly Facebook/Eventbrite)
- Gardening/Urban Farming (no feeds found)
- Literary/Poetry (✅ deep dive 2026-04-11; see "Topical Search: Literary / Bookstores" section)
- Startup/Tech (mostly Meetup already covered)
- Museums (scraper opportunities: ROM, Toronto Zoo)

---

## Topical Search: Literary / Bookstores (2026-04-11)

Vertical deep-dive into Toronto's indie bookstore scene. Goal: capture author readings, book launches, signings, book clubs.

### Aggregator-based discovery

Three independent sources cross-referenced to build a complete venue inventory:

| Aggregator | URL | Toronto stores found | Method |
|------------|-----|----------------------|--------|
| indiebookstores.ca (CIBA public face) | `indiebookstores.ca/locations/` | 30 | WordPress paginated; Cloudflare 403 on default UA, works with browser UA. 28 pages × ~12 stores each = 332 Canada-wide |
| NewPages Ontario | `newpages.com/independent-bookstores/ontario-independent-bookstores/` | 33 | Plain HTML directory, structured by `City:` field |
| Bookmanager `nearbyStores/get` API | `api.bookmanager.com/customer/nearbyStores/get` | 30 (deduped) | **🎯 Free public API** — see API section below. Returns lat/long + per-store URL |

**Combined unique Toronto bookstore inventory: ~50 stores** (overlap is heavy; each aggregator catches some the others miss).

### Eventbrite organizer sweep

Per-store Eventbrite searches across all 50 stores looking for `/o/{name}-{ID}/` organizer pages.

#### ✅ Confirmed organizer pages → wired into pipeline

| Store | Organizer ID | Notes |
|---|---|---|
| Another Story Bookshop | `32458688399` | 16 upcoming events at sweep time |
| Ben McNally Books | `13414493715` | Active book club + open mic + launches |
| Glad Day Bookshop | `12026081388` | Active; not in indiebookstores.ca, found via Eventbrite browse |
| Hopeless Romantic Books | `98641543971` | Monthly hybrid book club |
| Queen Books | `64558396403` | Currently dormant (0 upcoming, 26 past) |

#### ✅ Publisher organizer pages → wired into pipeline

Discovery: many bookstore events are hosted by **publishers**, not the venues themselves. Wiring publisher organizers captures events at multiple stores in one feed.

| Publisher | Organizer ID | Events in feed | Toronto venues used |
|---|---|---|---|
| Coach House Books | `6007837525` | 74 | Society Clubhouse, Coach House HQ |
| Cormorant Books | `31280011011` | 38 | Ben McNally, Sleuth of Baker Street |
| Book*hug Press | `30975200167` | 8 | Another Story, Type Books |
| Penguin Random House Canada | `13112142972` | 96 | Various; geo-filter trims to Toronto |

Pipeline geo-filter (`city.conf`) drops non-Toronto events from publisher feeds automatically.

#### ⚠️ Has Eventbrite events as venue, no own organizer page

These stores host events on Eventbrite but don't maintain a store organizer profile. Events route through individual authors or publisher organizer pages instead. Already partially captured via the publisher feeds above.

- **A Different Booklist** — events organized by authors / co-presenting orgs
- **Caversham Booksellers** — psych/social-science specialty; events co-hosted with publishers
- **Flying Books / Flying Books at Neverland** — Neverland Book Club series; event-by-event organizers
- **Little Ghosts Books** — author-organized launches (e.g., Mark Sampson `109211559751` for Lowfield Launch)
- **Manifest Bookstore** — past Black Literacy Book Fair (one-off organizers)
- **Swipe Design \| Books + Objects** — design book launches
- **The Beguiling Books & Art** — comics; main programming is via TCAF (Toronto Comic Arts Festival), separate organization
- **Type Books** (3 locations: Forest Hill, Junction, Queen West) — launches hosted by publishers (Book*hug, PRH already captured)

#### ❌ No Eventbrite presence at all

Bookmanager-hosted, used/rare, university, or specialty stores that don't use Eventbrite. Mostly captured at the venue level via publisher feeds when authors visit.

- **Bakka Phoenix Books** — sci-fi/fantasy specialty; manual-curation venue (see below)
- **BMV Books** (3 locations) — used + remainder chain
- **Book City** (4 locations: Bloor West, Danforth, Yonge & St. Clair, In the Beach)
- **Anansi Bookshop** — House of Anansi storefront; events on Henderson Brewing not Eventbrite
- **Spacing Store** — urban-themed, runs own programming off-platform
- **Inhabit Books** — Inuit publishing storefront
- **Sleuth of Baker Street** — mystery specialty; Cormorant publisher events captured
- **Book Bar** (Bookmanager-hosted) — events-friendly venue; possibly own platform
- **A Good Read**, **Acadia Art & Rare Books**, **Balfour Books**, **Contact Editions**, **David Mason Books**, **Doug Miller Books**, **Re: Reading**, **The Monkey's Paw**, **Seekers Books**, **Thunderstruck Bookstore**, **Zoinks Music & Books**, **Cornerstone Bookshop** (Christian), **Fa Yuan Bookstore** (Chinese), **Multilingual / Mosaique**, **Tyndale Campus Store**, **UofT Bookstore**, **Ella Minnow**, **Mabel's Fables**, **Good Egg**

### Discovered via publisher-feed triangulation (after the original 50-store walk)

While building the publisher-feed venue filter (`scrapers/eventbrite_filtered.py`), the Penguin Random House Canada feed surfaced a Toronto bookstore that wasn't in indiebookstores.ca, NewPages, or the Bookmanager nearby API:

- **Moonbeam Books** — 335 Jane Street (Bloor West Village). Children's & YA indie founded 2017. Squarespace-hosted (DNS 198.185.159.144). Listed on blogTO and NewPages but not in CIBA's directory and not on Bookmanager. Site blocks `curl` (likely Squarespace bot detection); has some Eventbrite venue presence ("Holiday Happy Hour @ Moonbeam Books") but no organizer page. Status: in inventory, no event source wired yet — needs Squarespace `?format=json` probe via WebFetch and manual organizer ID lookup.

This is the triangulation working as intended: publisher feeds are filtered for known venues *and* surface new ones.

### Publisher-feed venue filter (`scrapers/eventbrite_filtered.py`)

The 8 publisher organizer feeds (Coach House, Cormorant, Book*hug, PRH Canada, HarperCollins Canada, Simon & Schuster Canada, Diaspora Dialogues, House of Anansi) used to be wired as raw `eb-to-ical` URLs. That dumped Vancouver, Montreal, Halifax, and Calgary launches into the Toronto feed. Replaced with a parameterized filter scraper that applies two rules:

> **Update 2026-08-07:** the eb-to-ical.daylightpirates.org service died (HTTP 404 on every organizer), which zeroed all 8 publisher feeds. `eventbrite_filtered.py` was rewritten to scrape Eventbrite directly (organizer page + per-event JSON-LD, the `scrapers/eventbrite.py` mechanism) while keeping the same denylist + geo-allowlist filters; workflow lines now pass `--url "<organizer page>"` instead of `--organizer <id>`. First run after conversion: PRH Canada 2 events, Coach House 2, the other six organizers currently list no upcoming events (valid empty calendars — the April counts below reflect pre-outage volumes and should recover as publishers post fall seasons).

- **Denylist** (`cities/toronto/bookstore_venue_denylist.txt`) — drop events at Indigo / Chapters chain stores. Currently catches 0 events; serves as a safeguard for the future.
- **Geo allowlist** (`cities/toronto/geo_allowlist.txt`) — require LOCATION to contain "Toronto" or one of the 5 inner boroughs (North York, Scarborough, Etobicoke, East York, York). Events with no location at all pass (online events from Toronto orgs).

Filtered counts (April 2026):

| Publisher | Raw | Toronto-only | Trimmed |
|---|---|---|---|
| Penguin Random House Canada | 96 | 70 | 26 |
| HarperCollins Canada | 47 | 37 | 10 |
| Simon & Schuster Canada | 19 | 13 | 6 |
| Diaspora Dialogues | 136 | 113 | 23 |
| House of Anansi | 5 | 5 | 0 |
| Coach House Books | 74 | 63 | 11 |
| Cormorant Books | 38 | 31 | 7 |
| Book*hug Press | 8 | 7 | 1 |
| **Total** | **423** | **339** | **84 (~20%)** |

The `--report` flag prints the denied + out-of-area + passed venue lists, which is useful both for tuning the filters and for discovering new Toronto literary-event venues we might want to investigate (Henderson Brewing, Society Clubhouse, MaRS Discovery District, Heliconian Hall, MOCA Toronto, etc.).

### Bookmanager platform investigation → reusable scraper

13 of the 50 Toronto indies are hosted on Bookmanager's React SPA platform (URL pattern: `{store}.com/item/_Qr...`). Reverse-engineered the platform's free public API:

```
POST https://api.bookmanager.com/customer/{endpoint}?_cb={san}
Origin: https://{store-domain}
FormData: store_id, session_id, webstore_name=<san>, ...
```

**Bootstrap sequence:** `store/getSettings` → `session/get` → `event/v2/list`.

**Useful endpoints found:**
- `nearbyStores/get` — list all Bookmanager stores near lat/long (used for the inventory walk above; reusable for any city)
- `event/v2/list` — store's events feed; rows include id, title, description, date/time, location_text, category, image_url, books[], tickets[]
- `store/getSettings` — store metadata including `san`, `id`, `address`, `lat/long`
- `event/v2/getRsvpInfo` — RSVP/waitlist counts per event

**Cautionary tale.** Initial survey hit `event/getList` (a v1 endpoint found in the JS bundle) and got 0 rows from all 7 stores I tested, leading to the **false** conclusion that "Bookmanager events feature is not used by any Toronto store" and that Bakka Phoenix should be parked as manual-curation. Verifying with playwright (rendering the actual /events page and capturing API calls) revealed the SPA calls **`event/v2/list`** instead — and several stores have populated event databases. The lesson: when an API call returns empty, render the actual UI to verify before concluding the feature is unused.

**Confirmed via v2 endpoint** (5 of 13 Toronto Bookmanager stores actively use events):

| Store | Events | Notes |
|---|---|---|
| Flying Books | 12 | Biggest haul; book clubs + launches at Neverland |
| Ben McNally Books | 9 | Complements Eventbrite feed (different event series) |
| Queen Books | 8 | Bookmanager is the live source; Eventbrite dormant |
| A Different Booklist | 4 | Closes "ambiguous bucket" gap |
| Bakka Phoenix Books | 1 | Unparks from manual-curation status |
| Another Story, Book Bar, Book City, Ella Minnow, Mabel's Fables, Sleuth, The Beguiling | 0 | On platform but don't populate events; route through Eventbrite or social |

**Implementation:**
- `scrapers/lib/bookmanager.py` — `BookmanagerEventsScraper` reusable base class (parallel to `BibliocommonsEventsScraper`)
- `scrapers/bookmanager.py` — parameterized CLI: `--san --domain --name`
- 5 workflow invocations in `.github/workflows/generate-calendar.yml`
- Each store's SAN is extracted from `var san="..."` in the store's `/events` page HTML

**Bakka Phoenix:** No longer parked as manual-curation. Now wired via the Bookmanager scraper. The earlier "manual curation" verdict was based on the v1-endpoint mistake.

### Aggregators not used (but worth noting)

| Aggregator | Status | Notes |
|---|---|---|
| CIBA `cibabooks.ca/member-directory` | JS-rendered, no data on initial fetch | Public face is indiebookstores.ca |
| All Lit Up (`alllitup.ca`) | Has bookstore map on the site but not at the URL searched | Literary Press Group; could re-check |
| Penguin Random House Canada `/canadian-independent-bookstores` | Returned page chrome only, no list visible in initial fetch | Could be JS-rendered |
| Retail Council bookstore map | 403 (Cloudflare) | Skipped |

### eb-to-ical infrastructure note

All 9 wired feeds use the third-party `eb-to-ical.daylightpirates.org` service to convert Eventbrite organizer pages to ICS. **Single point of failure** — if it goes dark, all 9 feeds break simultaneously. Documented in `discovery-lessons.md:467`. Fallback: scrape Eventbrite JSON-LD via existing `scrapers/lib/jsonld.py`.

---

## Topical Search: Crafts / Makers Expansion (2026-04-16)

Second pass on craft/maker sources. Strategy: Meetup topical search + Eventbrite organizer discovery + venue website probing for authoritative ICS feeds.

### Added

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| The Devil's Workshop | WordPress Events Manager ICS | 50 | `thedevilsworkshop.ca/events/?ical=1` — jewellery, glass fusing, silversmithing, lost wax casting |
| Jewel Envy | WordPress Tribe ICS | 5 | `jewelenvy.ca/events/?ical=1` — jewellery, enamel, metalwork, kids polymer clay |
| HackLab.TO | Public Google Calendar ICS | 1,104 | Calendar ID `3oo6s709gu7d31cg1419cfrbuc@group.calendar.google.com` — hackerspace open house Tuesdays + workshops |
| Queen City Stitch and Bitch | Meetup ICS | 10 | Fibre arts — knit, crochet, spin, weave, sew |
| Studio Mooi | Eventbrite organizer scraper | 2 | Organizer `59841950783` — pottery/craft workshops at 926 Kingston Rd |
| Open Studio (Printmaking Centre) | Eventbrite organizer scraper | 8 | Organizer `19932715092` — printmaking at 401 Richmond St W |

### Venues Assessed — No Feed Available

| Venue | Platform | Notes |
|-------|----------|-------|
| Harbourfront Centre | WordPress (custom, no calendar plugin) | Major craft/design workshop program but no ICS; scraper opportunity |
| Craft Ontario | Shopify | Event listings page is static HTML; provincial craft org |
| The Knit Cafe | Shopify | Classes sold as products, no calendar |
| The Maker Bean | Shopify | Makerspace cafe; camps + workshops as products |
| The Potter's Studio | Shopify | Pottery classes as products |
| TTL Makerspace | Shopify | Training sold as products (sibling of Toronto Tool Library, already captured) |
| DesignTO | WordPress/Elementor | No calendar plugin; annual festival org |
| Knit Social | Squarespace | 64 events in collection but `?format=json` returns 0 (pagination quirk); per-event ICS possible |
| Studio Mooi (own site) | Wix | No feed; Eventbrite organizer used instead |

### Meetup Groups Assessed

| Group | Events | Status |
|-------|--------|--------|
| Queen City Stitch and Bitch | 10 | ✅ Added |
| Toronto Makers Society | 0 | Valid feed, no upcoming events |
| Stitches 'n Steins | 0 | Valid feed, no upcoming events |
| Stitch and Bitch Downtown Toronto | 0 | Valid feed, no upcoming events |
| Orkid Gallery | n/a | WordPress but no calendar plugin; ?ical=1 returns HTML |

### Key Pattern Observed

Most Toronto craft studios sell classes through **Shopify** — they treat workshops as products, not calendar events. This means no ICS feeds are possible. The authoritative wins (Devil's Workshop, Jewel Envy) are WordPress sites with calendar plugins. HackLab.TO uses an embedded Google Calendar. For Shopify-based studios, the only route is Eventbrite (if they cross-post) or a custom Shopify product scraper (already built for Bistitchual, Parkdale Pottery, Toronto Tool Library).

---

## Topical Search: Gardening / Horticulture (2026-04-16)

### Added

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Green Neighbours Network of Toronto | WordPress Tribe ICS | 50 | `gnntoronto.ca/events/?ical=1` — native plant walks, tree plantings, stewardship events |
| GardenOntario (OHA) | WordPress Tribe ICS | 30 | `gardenontario.org/events/?ical=1` — province-wide hort society events; geo-filter trims to Toronto |
| Etobicoke Horticultural Society | Squarespace per-event ICS scraper | 4 future | `etobicokehort.ca/monthly-meetings-1` — 47 events in collection, 36 per-event ICS links, 4 future after date filter |
| Toronto Master Gardeners | WordPress Tribe ICS | 15 | `torontomastergardeners.ca/events/?ical=1` — demos at libraries, advice clinics, TBG presentations |
| Anga's Farm & Nursery | Squarespace per-event ICS scraper | 11 | `angasfarm.ca/events-2` — workshops (kokedama, pruning, floral) at 89 Bankfield Dr, Toronto |

### Organizations Assessed — No Feed Available

| Organization | Platform | Notes |
|-------------|----------|-------|
| Toronto Community Garden Network (TCGN) | WordPress (BuddyPress) | Member network, no calendar plugin |
| Toronto Urban Agriculture Week | WordPress.com | Annual event, blog-format posts |
| Garden Club of Toronto | ClubExpress | Member org, no public feed |
| gardeningcalendar.ca | WordPress | Tribe API headers present but events route 404s; ICS returns HTML |
| Parkdale & Toronto Horticultural Society | gardentoronto.ca down (ECONNREFUSED) | Meets last Monday of month at Bonar-Parkdale Presbyterian Church |
| FoodShare Toronto | WordPress | Tribe API 404; ICS returns HTML. Community gardens program but no events feed |
| NANPS (North American Native Plant Society) | WordPress | `google-calendar-events` plugin but no public embed found; `simple_events` CPT, no ICS. Has EB organizer `14961310163` (1 event). HQ'd in Toronto |
| Seeds of Diversity | WordPress | Seedy Saturday aggregator; no Tribe/MEC. Events page has no calendar plugin |
| Etobicoke Master Gardeners | Weebly | No feed; static events page |
| MGOI (Master Gardeners of Ontario) | WordPress | No calendar plugin |
| Sheridan Nurseries | Custom/unknown | Events page exists but no detectable platform |
| Black Creek Community Farm | WordPress | `?ical=1` returns HTML; no Tribe plugin |
| Toronto Seed Library | WordPress | No calendar plugin |
| Toronto Bonsai Society | WordPress | `?ical=1` returns HTML; no Tribe. Monthly meetings 2nd Monday at 7pm |

### Meetup Groups Assessed

| Group | Events | Status |
|-------|--------|--------|
| Toronto Permaculture | 0 | No upcoming events |
| Gardening with Indigenous Plants | 0 | No upcoming events |
| Forage & Feast | 0 | Burlington area; no upcoming events |

### Notes

- Toronto Botanical Garden is already in feeds (WordPress Tribe ICS)
- Ontario Nature is already in feeds (WordPress Tribe ICS)
- High Park Nature Centre is already in feeds (WordPress Tribe ICS)
- GardenOntario events are province-wide (Batawa, Gananoque, Cambridge, etc.) — pipeline geo-filter will trim to Toronto-area events
- Anga's Farm is in Rexdale (89 Bankfield Dr, M9V) — confirmed Toronto

---

## Topical Search: Comedy / Improv (2026-04-16)

Assessed but not wired. Inventoried for future triangulation.

### Venues Assessed

| Venue | Platform | Eventbrite Organizer | Events | Notes |
|-------|----------|---------------------|--------|-------|
| Keys Toronto Comedy Club | Unknown | `29571417999` | 21 | Biggest EB comedy organizer |
| Backroom Comedy Club | Unknown | `37924243333` | 23 EB + 10 Meetup | Both platforms active |
| Bad Dog Theatre | Squarespace | `38696894293` | Unknown | Improv since 1982; per-event ICS possible (pagination quirk) |
| Social Capital Theatre (SoCap) | Next.js | `34755939373` | 4 | Improv/sketch/standup on Danforth |
| Second City Toronto | Wix | `106289245751` | 1 | Iconic improv; low EB presence |
| Comedy Bar | Shopify | Not found | n/a | 2 locations (Bloor + Danforth); sells tix as products |
| Yuk Yuk's | Custom | No organizer page | n/a | Legacy club; individual show listings only |
| The Comedy Lab | Unknown | Collection page | Unknown | Black/Queer-owned; newer venue |

### Action Items (parked)

- Wire Keys (21 events), Backroom (23 events), Bad Dog, SoCap as Eventbrite scrapers
- Add Backroom Comedy Club Meetup ICS feed (10 events)
- Bad Dog: try Squarespace per-event ICS aggregation pattern

---

## Topical Search: Food / Drink (2026-04-16)

Assessed; low yield for machine-readable feeds. The community food space is dominated by Shopify (classes as products) and custom sites.

### Venues Assessed — No Feed Available

| Venue / Org | Platform | Notes |
|-------------|----------|-------|
| St. Lawrence Market | Custom | Events page exists but no calendar plugin |
| Evergreen Brick Works | WordPress | `?ical=1` returns HTML; no Tribe/MEC |
| Friends of Allan Gardens | Squarespace | Saturday Farmers Market; `?format=json` returns 0 |
| Dish Cooking Studio | Squarespace | Calendar managed via FareHarbor (external booking) |
| The Depanneur | Shopify | Community kitchen; events as products |
| The Stop Community Food Centre | WordPress | No Tribe plugin; runs Saturday farmers market at Wychwood Barns |
| Wychwood Barns | Duda | Monthly calendar as blog posts |
| TFMN (Toronto Farmers Market Network) | WordPress | Articles not events |
| Farmers' Markets Ontario | WordPress | Provincial org, no calendar plugin |
| To Do Canada | WordPress | Festival aggregator; `?ical=1` returns HTML |

### Notes

- Green Neighbours Network (added under Gardening) overlaps: community food growing, food forests
- Farmers markets are largely seasonal and don't publish machine-readable calendars
- Cooking studios universally use booking platforms (FareHarbor, Shopify) rather than event calendars
- Food festivals are one-off events mostly on Eventbrite; no persistent organizer pages worth wiring
