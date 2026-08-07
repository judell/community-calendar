# Lancaster Calendar Source Checklist

Prioritized list of potential event sources for the Lancaster, PA community calendar.

## Currently Implemented

| Source | Type | Notes |
|--------|------|-------|
| Visit Lancaster City | ICS | `visitlancastercity.com` WordPress/Tribe Events |
| FIG Lancaster | ICS | `figlancaster.com` WordPress/Tribe Events |
| LancasterPA.com | ICS | `lancasterpa.com` **AGGREGATOR** — community events aggregator, low dedup priority |
| Mickey's Black Box | ICS | `mickeysblackbox.com` Lititz venue |
| The Candy Factory | ICS | `candyissweet.com` WordPress/Tribe Events |
| Bird-in-Hand | ICS | `bird-in-hand.com` tourism/artisan events |
| Trust Performing Arts Center | ICS | `lancastertrust.com` WordPress/Tribe Events |
| City of Lancaster | ICS | `cityoflancasterpa.gov` government meetings (~30 events) |
| Saint James Episcopal | ICS | `saintjameslancaster.org` WordPress/Tribe Events |
| Church of the Apostles UCC | ICS | `apostlesucc.org` WordPress/Tribe Events |
| Calvary Church | ICS | `calvarychurch.org` WordPress/Tribe Events |
| Stevens & Smith Center | ICS | `stevensandsmithcenter.org` new venue opening May 2026 |
| North Museum | ICS | `northmuseum.org` science museum, ~39 events |
| American Music Theatre | ICS | `amtshows.com` WordPress/Tribe Events |
| Lancaster Science Factory | ICS | `lancastersciencefactory.org` WordPress/Tribe Events |
| Lancaster County Bird Club | ICS | `lancasterbirdclub.org` WordPress/Tribe Events, 17 events |
| Lancaster County Watersheds | ICS | `lancasterwatersheds.org` WordPress/Tribe Events, 17 events |
| Grandview Vineyard | ICS | `grandviewwines.com` WordPress/Tribe Events, 9 events |
| Zest Cooking School | ICS | `zestchef.com` WordPress/Tribe Events, 30 events (Lititz) |
| School District of Lancaster | ICS | `sdlancaster.org` WordPress/Tribe Events |
| Manheim Township District | ICS | `mtwp.net/ics/MT.ics` 119 events |
| Manheim Township HS | ICS | `mtwp.net/ics/HS.ics` 76 events |
| East Lampeter Township | ICS | `eastlampetertownship.org` WordPress/Tribe Events |
| Lancaster County (all meetings) | ICS | CivicEngage catID=43, 252 government meetings |
| Manheim Township gov | ICS | CivicEngage catID=14, 190 events |
| West Lampeter Township | ICS | CivicEngage catID=14, 56 events |
| Tech Lancaster Meetups | Meetup | tech talks, Open Coffee Club |
| Data Lancaster | Meetup | data community |
| WordPress Lancaster | Meetup | WordPress community |
| Lancaster Linux User Group | Meetup | Linux community |
| Lancaster Elastic User Group | Meetup | tech |
| CPOSC | Meetup | Central PA Open Source Conference |
| Level Up Meetup | Meetup | tech |
| Brews and Biz | Meetup | professional networking |
| Meet People Lancaster | Meetup | social |
| Lancaster Sports & Rec | Meetup | social/sports |
| Lancaster Women's 55+ | Meetup | social |
| Lancaster Freethought Society | Meetup | community |
| Creative House of Lancaster | Meetup | arts |
| Lancaster County Photography | Meetup | photography |
| Lancaster Photography School | Meetup | photography |
| Lancaster Scrapbooking | Meetup | crafts |
| Lancaster Craft Club | Meetup | crafts |
| Lancaster Bicycle Club | Meetup | cycling |
| Lancaster Sierra Club | Meetup | outdoors/conservation |
| ADVENTURE Lancaster | Meetup | board games |
| Central PA Game Club | Meetup | board games |
| Lancaster Guided Meditation | Meetup | wellness |
| Being One Center | Meetup | wellness/spiritual |
| Walking Tails | Meetup | dogs/walking |
| Mental Health America Lancaster | Meetup | wellness |
| Authors in the Making | Meetup | writing group, biweekly |
| Lancaster County Dems | Scraper | `mobilize.py` civic organizing |
| Tellus360 | Scraper | `songkick.py` venue 1614528 |
| Tellus360 - The Temple | Scraper | `songkick.py` venue 3942704 |
| Phantom Power | Scraper | `songkick.py` venue 4369005 |
| Freedom Hall | Scraper | `songkick.py` venue 4420425 |
| The Village | Scraper | `songkick.py` venue 65068 |
| Lancaster Dispensing Co. | Scraper | `songkick.py` venue 778176 |
| Southern Market Lancaster | Scraper | `squarespace.py` events/trivia/music |
| Lancaster Art Vault | Scraper | `squarespace.py` gallery/workshops |
| Creatively Lancaster | Scraper | `squarespace.py` arts community |
| Lancaster Conservancy | Scraper | `eventbrite.py` org 6683570777, nature events |
| Penn Medicine Park | Scraper | `ticketmaster.py` venue ZFr9jZ7FaA (Stormers stadium) |
| Fulton Opera House | Scraper | `ticketmaster.py` venue ZFr9jZe1Fk |
| Freedom Hall (TM) | Scraper | `ticketmaster.py` venue KovZpZAEe6dA |
| Tellus 360 (TM) | Scraper | `ticketmaster.py` venue KovZpZAEeklA |
| Phantom Power (TM) | Scraper | `ticketmaster.py` venue KovZ917AxW7 |
| Lancaster Catholic | Scraper | `maxpreps.py` lancaster-catholic-crusaders |
| Lancaster Mennonite | Scraper | `maxpreps.py` lancaster-mennonite-blazers |
| Manheim Township HS | Scraper | `maxpreps.py` manheim-township-blue-streaks |
| Hempfield HS | Scraper | `maxpreps.py` hempfield-black-knights |
| Penn Manor HS | Scraper | `maxpreps.py` penn-manor-comets |
| Conestoga Valley HS | Scraper | `maxpreps.py` conestoga-valley-buckskins |
| Lampeter-Strasburg HS | Scraper | `maxpreps.py` lampeter-strasburg-pioneers |
| Ephrata HS | Scraper | `maxpreps.py` ephrata-mountaineers |
| Warwick HS | Scraper | `maxpreps.py` warwick-warriors |
| Elizabethtown HS | Scraper | `maxpreps.py` elizabethtown-bears |
| McCaskey HS | Scraper | `maxpreps.py` jp-mccaskey-red-tornado |
| Donegal HS | Scraper | `maxpreps.py` donegal-indians |
| F&M Athletics (26 sports) | Scraper | `sidearm.py` godiplomats.com, ~274 future events |
| Lancaster Libraries | Scraper | `drupal_events.py` calendar.lancasterlibraries.org, ~2566 events |

## Needs Scraper

| Source | Platform | URL | Notes |
|--------|----------|-----|-------|
| Lancaster Chamber | GrowthZone App | lancasterchamber.growthzoneapp.com | Uses growthzoneapp.com, not standard /api/events |
| F&M College events | CampusGroups JSON API | ampersand.fandm.edu/mobile_ws/v17/mobile_events_list | ~376 events but ~90% have "Private Location" — low yield |
| Millersville University | CampusLabs | engage.millersville.edu | College events |
| Elizabethtown College | 25Live | -- | College events |
| Pathways Institute | WordPress/Tribe API | thepathwaysinstitute.org | Lifelong learning, 40+ courses/term |
| LancasterHistory | WordPress | lancasterhistory.org | FullCalendar, no ICS |
| Lancaster Improv Players | Custom | lancasterimprovplayers.org | Sells via Eventbrite |
| Nissley Vineyards | Squarespace | nissleywine.com | Music in the Vineyard series |
| Gretna Music | Squarespace | gretnamusic.org | Seasonal chamber/jazz |
| PA Guild of Craftsmen | WordPress | pacrafts.org | 250+ workshops/year, no TEC |
| Zoetropolis | WordPress | zoetropolis.com | Cinema/music/comedy, no TEC |
| Humane Pennsylvania | WordPress | humanepa.org | Walk for Animals, Pints for Pups |
| Lancaster Township | Revize | twp.lancaster.pa.us | JS-rendered calendar, no ICS |
| Tellus360 (direct) | WordPress/MEC | tellus360.com | Modern Events Calendar, no ICS export |

## Potential Future Sources

| Source | Notes |
|--------|-------|
| Dutch Apple Dinner Theatre | Covered indirectly via lancasterpa.com aggregate |
| Sight & Sound Theatres | Custom platform, Bible-themed productions |
| Long's Park Amphitheater | Wix, seasonal summer concerts |
| Lancaster Roots & Blues Festival | Annual September festival |
| Lancaster Farmland Trust | WordPress, no TEC — farm events |
| CNP Trivia | Custom site, trivia every night at various bars |
| Discover Lancaster | Tourism aggregator, useful for phase 4 upstream authority |
| Lancaster Bible College | Ticketmaster venue Z7r9jZadtj, check for campus calendar |
| Demuth Museum | Squarespace brochure site, no events feature — needs custom scraper or RSS |

## 2026-08-07 Audit Findings

Source: `reports/lancaster-2026-08-07-soak.md` (local Python 3.10 audit against
`scripts/local_build.py`, `--sync-existing --dry-run` comparison against the
`feeds` table, and a same-day upstream `generate-calendar.yml` run comparison).
Local run: `0` scraper failures, `0` missing outputs, `0` validation errors.
Same 10 zero-event scrapers appeared in both the local run and the upstream
run, and no DB-only or workflow-only scraper rows existed (`0` missing,
`0` to retire).

### Resolved: workflow/DB metadata drift (command/name-drift class)

Applied via `scripts/backfill_scraper_feeds.py --city lancaster --sync-existing`
(no `--dry-run`), `3` updated, `0` inserted, `0` retired, `0` errors:

- **Penn Medicine Park** (`ticketmaster.py` venue ZFr9jZ7FaA) — DB display
  name was the generic `"Ticketmaster"`; synced to `"Penn Medicine Park"` to
  match the workflow.
- **F&M Athletics** (`sidearm.py`) — the DB-stored command used `--url`,
  which `scrapers/sidearm.py` does not accept (`--base-url` is the required
  flag); the stored command would have failed with `--base-url: required` if
  ever executed, and it silently dropped the workflow's `--home-only` scope
  flag. Synced to the workflow's exact command: `python scrapers/sidearm.py
  --base-url "https://godiplomats.com" --name "F&M Athletics" --home-only -o
  cities/lancaster/fandm_athletics.ics`.
- **Lancaster Catholic** (`maxpreps.py`) — DB display name was the generic
  `"High school athletics (MaxPreps)"`; synced to `"Lancaster Catholic"`.

### Investigated: Fulton Opera House Ticketmaster zero-event output

`ticketmaster.py --venue-id ZFr9jZe1Fk --name "Fulton Opera House"` logs
`Ticketmaster: 0 events across 0 pages` in both the local and upstream runs,
with no scraper error. Direct read-only Ticketmaster Discovery API probes
(2026-08-07, using `TICKETMASTER_API_KEY`, no key value logged) confirm:

- `GET /discovery/v2/venues.json?keyword=Fulton+Opera+House&stateCode=PA`
  returns exactly one venue: `id=ZFr9jZe1Fk, name="Fulton Opera House",
  city=Lancaster, state=PA` — **the workflow's venue ID is correct**, not
  stale or mismatched.
- `GET /discovery/v2/events.json?venueId=ZFr9jZe1Fk` returns
  `totalElements: 0, totalPages: 0` directly from Ticketmaster's own catalog
  — independent of the repo's scraper code.

Conclusion: this is not a broken venue ID or a scraper bug. Ticketmaster's
own catalog currently has no listed events for this venue (Fulton Opera
House's public season likely isn't sold through Ticketmaster comprehensively,
or is between listed runs). No corrected command exists to propose. Classify
as **valid but quiet** — leave as-is, re-check periodically rather than
retiring.

### Adjudicated 2026-08-07 (duplicate-producer decisions)

- **Chameleon Club — retired, both producers.** The venue closed permanently
  in 2020 and the 223 N. Water St. building was sold to the Pennsylvania
  College of Art & Design (lancasteronline.com coverage; Yelp lists the
  venue as CLOSED). Both workflow lines removed and both DB scraper rows
  marked removed on 2026-08-07.
- **Freedom Hall — keep both.** Active venue at the Lancaster Convention
  Center; Ticketmaster lists shows in Dec 2026 (beyond the 3-month scrape
  horizon, which explains today's zeros). Both producers retained by
  decision; dedup reconciles any future overlap.
- **Tellus 360 — keep both.** Active venue with overlapping-but-different
  Songkick (4) and Ticketmaster (5) coverage; both retained by decision to
  preserve long-tail coverage, dedup reconciles the overlap.
- **Phantom Power — keep both.** Songkick (5) currently finds more than
  Ticketmaster (3); both retained by decision, dedup reconciles.

### Still open (not changed this pass)

- **Eight other zero-event scraper outputs** (Tellus360 - The Temple,
  Freedom Hall via Songkick, The Village, Lancaster Dispensing Co., Penn
  Medicine Park via Ticketmaster, Freedom Hall via Ticketmaster,
  Lampeter-Strasburg) and **eighteen zero-event live feeds** still need
  individual review; see `reports/lancaster-2026-08-07-soak.md` F005 for
  the full list. None were retired this pass.
