# Roanoke VA Sources Checklist

## Currently Implemented (0 sources)

*None yet*

---

## Discovered - Ready to Add

| Source | Feed URL | Events | Notes |
|--------|----------|--------|-------|
| City of Roanoke Special Events | `https://www.roanokeva.gov/common/modules/iCalendar/iCalendar.aspx?catID=39&feed=calendar` | ~130 | CivicPlus; festivals, public events |
| City of Roanoke Public Events | `https://www.roanokeva.gov/common/modules/iCalendar/iCalendar.aspx?catID=25&feed=calendar` | ~7 | CivicPlus; general city events |
| Roanoke Neighborhood Events | `https://www.roanokeva.gov/common/modules/iCalendar/iCalendar.aspx?catID=35&feed=calendar` | ~8 | CivicPlus; neighborhood events |
| Roanoke City Council Meetings | `https://www.roanokeva.gov/common/modules/iCalendar/iCalendar.aspx?catID=28&feed=calendar` | ~89 | CivicPlus; government meetings |
| Council Boards & Commissions | `https://www.roanokeva.gov/common/modules/iCalendar/iCalendar.aspx?catID=38&feed=calendar` | ~238 | CivicPlus; boards/commissions — many recurring meetings |
| Berglund Center | `https://calendar.google.com/calendar/ical/ice.berglundcenter%40gmail.com/public/basic.ics` | ~435 | Google Calendar embed; arena/convention center — concerts, hockey, Broadway, symphony |
| Hollins University | `https://www.hollins.edu/events/?ical=1` | ~24 | WordPress Tribe ICS |
| Taubman Museum of Art | `https://taubmanmuseum.org/events/?ical=1` | ~30 | WordPress Tribe ICS |
| Roanoke Symphony Orchestra | `https://rso.com/events/?ical=1` | ~6 | WordPress Tribe ICS |
| Make Roanoke | `https://www.meetup.com/make-roanoke/events/ical/` | ~10 | Meetup ICS; makerspace events |
| Pathfinders for Greenways | `https://www.meetup.com/pathfinders-for-greenways/events/ical/` | ~9 | Meetup ICS; greenway hikes/outdoors |
| SW VA Toastmasters | `https://www.meetup.com/southwest-va-toastmasters-meetup-group/events/ical/` | ~10 | Meetup ICS; public speaking |
| Roanoke Spiritual Experiences | `https://www.meetup.com/Roanoke-Spiritual-Experiences-Group/events/ical/` | ~4 | Meetup ICS |
| Roanoke Valley .NET Users | `https://www.meetup.com/roanoke-valley-net-user-group/events/ical/` | ~2 | Meetup ICS; tech |
| Shut Up & Write Roanoke | `https://www.meetup.com/shut-up-write-roanoke/events/ical/` | ~3 | Meetup ICS; writing |
| Salem Main Calendar | `https://www.salemva.gov/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar` | ~25 | CivicPlus; general Salem events |
| Salem Civic Center | `https://www.salemva.gov/common/modules/iCalendar/iCalendar.aspx?catID=26&feed=calendar` | ~23 | CivicPlus; civic center events |
| Salem Government Meetings | `https://www.salemva.gov/common/modules/iCalendar/iCalendar.aspx?catID=27&feed=calendar` | ~41 | CivicPlus; government meetings |
| Salem Parks & Rec | `https://www.salemva.gov/common/modules/iCalendar/iCalendar.aspx?catID=23&feed=calendar` | ~2 | CivicPlus |
| Roanoke Higher Education Center | `https://eb-to-ical.daylightpirates.org/eventbrite-organizer-ical?organizer=3245496552` | ~99 | Eventbrite via eb-to-ical; poetry, gaming, workshops, panels |

---

## Discovered - Needs Scraper

| Source | URL | Platform | Notes |
|--------|-----|----------|-------|
| Visit Roanoke VA | `https://www.visitroanokeva.com/events/rss/` | Simpleview (CVB) | RSS feed works (~31 events), no ICS endpoint; has public API token |
| Roanoke Regional Chamber | `https://business.roanokechamber.org/api/events` | GrowthZone XML | ~28 events; use `scrapers/growthzone.py --site roanokechamber` |
| Roanoke Rambler | `https://www.roanokerambler.com/tag/happenings/` | Ghost | Editorial prose, not structured event data — would need NLP extraction |

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Downtown Roanoke (downtownroanoke.org) | 403 on all automated requests; likely Wix; no Eventbrite organizer page found |
| Cardinal News events calendar | JS-rendered regional widget (Eventbrite embed), no static API; organizer page has 0 upcoming events |
| Roanoke College (roanoke.edu/events) | FullCalendar with hardcoded JS events; no ICS or JSON API endpoint |
| Roanoke Library Events CivicPlus (catID=23) | Returns 0 events |
| Virginia Western Community College | WordPress but no Tribe Events; `?ical=1` returns HTML |
| Science Museum of Western Virginia (smwv.org) | WordPress but no Tribe Events; `?ical=1` returns HTML |
| Mill Mountain Theatre | Mod_Security blocks all automated requests |
| Roanoke Valley Chamber (rvchamber.com) | GrowthZone API returns 0 events |
| Eventbrite VA Roanoke science/tech browse | Not city-specific; regional/statewide events mixed in |
| Roanoke Public Libraries | On CivicPlus (catID=23), currently 0 events |

---

## To Investigate

- [ ] Roanoke City Parks & Recreation (separate from CivicPlus?)
- [x] Salem city events (salemva.gov — also CivicPlus?)
- [ ] Roanoke County events
- [ ] Additional Meetup groups: lets-play-chess, star-city-circlesinging, grid-valley-investors
- [ ] Songkick for music venues
- [ ] Virginia Tech / Radford University (if in geo radius)

---

## Research Log

### 2026-03-07: Initial setup

City added. Source discovery in progress.
