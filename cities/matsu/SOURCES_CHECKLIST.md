# MatSu (Matanuska-Susitna) Community Calendar Sources

## Area Coverage
- Matanuska-Susitna Borough (Mat-Su Borough)
- Wasilla, AK
- Palmer, AK

## Currently Implemented
- **Wasilla Library Events** — CivicPlus catID=23
- **Wasilla Menard Center Events** — CivicPlus catID=25 (Outdoorsman Show, hockey tournaments, trade shows)
- **Wasilla City Council Meetings** — CivicPlus catID=26
- **Wasilla Airport Advisory Commission** — CivicPlus catID=27
- **Wasilla Planning Commission** — CivicPlus catID=28
- **Wasilla Parks & Recreation Commission** — CivicPlus catID=29
- **Connect Mat-Su** — WordPress ICS (health, training, recreation, job expos)
- **Visit Palmer** — WordPress ICS (Colony Days, Friday Flings, WinterRomp, Garden & Art Festival)
- **Skeetawk / Hatcher Pass** — WordPress ICS (Hatcherpalooza, Recycle Revival, Hatcher Romp!, races)
- **Mat-Su Borough Assembly** — Legistar scraper (client: `matanuska`)
- **Mat-Su School District** — Finalsite calendar-manager ICS (~5,117 events: all district schools, athletics, events)
- **Mat-Su CVB (alaskavisit.com)** — custom scraper: RSS → JSON-LD per event page (~20 future events: hikes, community events, Iditarod, outdoor recreation)

---

## Confirmed Working Feeds

### City of Wasilla (CivicPlus)
- [x] **Wasilla Library Events** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=23` (~36 events: storytime, book sales, programs)
- [x] **Menard Center Events** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=25` (~6 events: Mat-Su Outdoorsman Show, hockey tournaments, trade shows)
- [x] **City Council Meetings** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=26` (~23 events)
- [x] **Planning Commission** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=28` (~20 events)
- [x] **Parks & Recreation Commission** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=29` (~5 events)
- [x] **Airport Advisory Commission** — `https://www.cityofwasilla.gov/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=27` (~10 events)
  - Note: city redirects `cityofwasilla.com` → `cityofwasilla.gov`, use `-L` flag

### Community Calendars (WordPress ICS)
- [x] **Connect Mat-Su** — `https://www.connectmatsu.org/events/list/?ical=1` (~30–42 events: health, skills training, recreation, job expos across the valley)
- [x] **Visit Palmer** — `https://visitpalmer.com/?post_type=tribe_events&ical=1&eventDisplay=list` (~26 events: Colony Days, Friday Flings, WinterRomp, Garden & Art Festival)

### Outdoor / Recreation
- [x] **Skeetawk / Hatcher Pass** — `https://skeetawk.com/?post_type=tribe_events&ical=1&eventDisplay=list` (~30 events: Hatcherpalooza, Recycle Revival music fest, Hatcher Romp!, Skeetawk Scramble mountain race, Death by a Mile)

### Government Meetings (Legistar)
- [x] **Mat-Su Borough Assembly** — Legistar client slug: `matanuska` (~8 meetings/year: Regular, Special, Work Session, Joint meetings)

### School District (Finalsite)
- [x] **Mat-Su School District** — `https://www.matsuk12.us/fs/calendar-manager/events.ics?calendar_ids[]=134&...` (~5,117 events across all district schools)

---

## Potential Sources (need scraper or investigation)

- [x] **Mat-Su CVB (alaskavisit.com)** — `scrapers/alaskavisit.py` implemented (RSS → per-page JSON-LD)
- [ ] **Wasilla Chamber (wasillachamber.org)** — GrowthZone platform confirmed. Public ICS may need chamber contact. Events: monthly luncheons, Mat-Su Spring Economic Summit, Lunch & Learn series.
- [ ] **Palmer Chamber (palmerchamber.org)** — GrowthZone platform. Cloudflare blocking direct access. Colony Days, Friday Flings, Colony Christmas.
- [ ] **Alaska State Fair (alaskastatefair.org)** — WordPress + Event Espresso plugin (no `?ical=1`). Fairgrounds year-round events; main fair Aug 21–Sep 7. Concert series (AJR, CAKE, etc.). Scraper against Event Espresso AJAX endpoint may work.
- [ ] **Mat-Su College / UAA (matsu.alaska.edu)** — Trumba calendar platform, but production slug unknown ("msc-test-campus-events" is a dev slug). Contact UAA Mat-Su for subscribe link.
- [ ] **Mat-Su Trails & Parks Foundation (matsutrails.org)** — WordPress, no ICS. ~4–6 events/month: speaker series, Winter Discovery Day at Government Peak. Scrape from https://matsutrails.org/news-and-events/feed/ ? 
- [ ] **Iditarod (iditarod.com)** — WordPress + Simple Calendar (Simcal). Underlying Google Calendar source may be extractable from page source — would give direct ICS. Ceremonial restart in Willow (Mat-Su).
- [ ] **Palmer Public Library (palmerpublic-ak.whofi.com)** — WhoFi platform, no public ICS. ~10–15 events/month: Baby Lap Sit, Storytime, book clubs, painting classes, Friends book sales.
- [ ] **WACO / Willow Area Community Org (waco-ak.org)** — WordPress + AI1EC plugin. ICS export may be disabled. Willow Winter Carnival (Jan), community events.
- [ ] **Frontiersman newspaper (frontiersman.com)** — BLOX CMS. "Local Events Calendar for the Mat-Su Valley" with community submissions. Check if ICS export exists.
- [ ] **Talkeetna Alaskan Lodge events** — https://www.alaskacollection.com/lodging/talkeetna-alaskan-lodge/events/

---

## Meetup Groups
- **Mat-Su Valley Hikers** — ICS works but 0 upcoming events as of Mar 2026. Group appears inactive (107 members, last event Jul 2025). Monitor.
- [ ] Search for other active Meetup groups in Wasilla/Palmer/Mat-Su

---

## Non-Starters
- **Legistar for "wasilla", "palmer", "matsu"** — Only `matanuska` slug works; others return "connection not set up"
- **Mat-Su Borough main site (matsu.gov)** — Custom Next.js/React, no CivicPlus, no ICS calendar. Meetings are in Legistar.
- **City of Palmer (palmerak.org)** — Cloudflare blocks all automated access. Tested `/calendar/rss`, `/calendar/ical/calendar.ics`, `/calendar/json` — all return Cloudflare challenge. Worth a manual browser check for CivicPlus feeds at `https://www.palmerak.org/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=N`
- **Mat-Su Library Network (libraries.matsugov.us)** — Borough branch libraries (Big Lake, Sutton, Talkeetna, Trapper Creek, Willow) have static pages only, no event calendar system.
- **BiblioCommons** — No Mat-Su library is on BiblioCommons.
- **Tockify** — No Mat-Su/Wasilla/Palmer orgs found on Tockify.
- **Palmer Library via WhoFi** — No ICS export supported by WhoFi platform.
- **Trumba for Mat-Su College** — "msc-test-campus-events" slug returns "page removed." Dev artifact.
- **Iditarod Simcal ICS** — No direct feed; individual Google Calendar event links only.
- **Alaska State Fair ?ical=1** — Event Espresso plugin does not expose standard WordPress tribe ICS.
- **alaskavisit.com (CVB) ICS** — SimpleView API requires authenticated session token. RSS exists (see Potential Sources above) but no ICS endpoint.
- **WACO AI1EC ICS** — Export appears disabled on their install.
- **Mat-Su Chamber (matsuchamber.org)** — Connection refused / site down for automated access.
