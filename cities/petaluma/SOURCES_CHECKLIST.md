# Petaluma Calendar Source Checklist

## Currently Implemented (all in CI)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Petaluma Downtown Association | Tockify ICS | 71 | ✅ In CI |
| Aqus Community | MembershipWorks ICS | 87 | ✅ In CI |
| Petaluma Regional Library | Scraper | 155 | ✅ In CI |
| Petaluma Chamber of Commerce | GrowthZone Scraper | 80 | ✅ In CI |
| Mystic Theatre | Scraper | 12 | ✅ In CI |
| Eventbrite Petaluma | Scraper | 14 | ✅ In CI |
| Petaluma High School Athletics | MaxPreps Scraper | 9 | ✅ In CI |
| Casa Grande High School Athletics | MaxPreps Scraper | 8 | ✅ In CI |
| SRJC Petaluma Campus | LiveWhale Scraper | 17 | ✅ In CI |
| HenHouse Brewing Petaluma | Scraper | 2-3 | ✅ In CI |
| Phoenix Theater | Eventbrite Scraper | 13 | ✅ In CI |
| Mercury Theater | Squarespace JSON Scraper | 12 | ✅ In CI |
| Adobe Road Winery | JSON-LD Scraper | 8 | ✅ In CI |
| The Big Easy | WordPress iCal | ~30 | ✅ In CI |
| Meetup: Mindful Petaluma | ICS | 10 | ✅ In CI |
| Meetup: Candlelight Yoga | ICS | 10 | ✅ In CI |
| Meetup: Rebel Craft Collective | ICS | 6 | ✅ In CI |
| Meetup: Sonoma-Marin Brat Pack | ICS | 2 | ✅ In CI |
| Meetup: Figure Drawing | ICS | 1 | ✅ In CI |
| Meetup: Petaluma Salon | ICS | 1 | ✅ In CI |
| Meetup: Book & Brew Club | ICS | 1 | ✅ In CI |
| Meetup: Active 20-30 | ICS | 2 | ✅ In CI |
| Meetup: Sonoma County Outdoors | ICS | ~10 | ✅ In CI |
| Meetup: North Bay Contra Dance | ICS | ~10 | ✅ In CI |
| Meetup: Sonoma County Boomers | ICS | ~7 | ✅ In CI |
| Meetup: Go Wild Hikers | ICS | ~3 | ✅ In CI |
| Meetup: Meditate with a Monk | ICS | ~10 | ✅ In CI |
| Meetup: North Bay Adventure Club | ICS | ~10 | ✅ In CI |
| Meetup: North Bay Tails and Trails | ICS | ~5 | ✅ In CI |
| Meetup: North Bay 50+ Nature and Outdoors | ICS | ~10 | ✅ In CI |
| Meetup: Senior Walkabouters (SWAG) | ICS | ~5 | ✅ In CI |
| Meetup: Sonoma County Wanderers | ICS | ~10 | ✅ In CI |
| Meetup: Mindfull Hikes | ICS | ~5 | ✅ In CI |
| Meetup: Four Corners Hiking & Beer | ICS | ~5 | ✅ In CI |

**Total: ~515+ events (before deduplication)**

---

## To Investigate

### Squarespace sites (can reuse Mercury Theater `?format=json` pattern)
- Cinnabar Theater (cinnabartheater.org/shows/) - Full theater season
- WonderStump! (wonderstump.art/events) - Immersive art venue
- Polly Klaas Community Theater (pollyklaastheater.org/events/) - StorySlam, jazz
- Petaluma Arts Center (petalumaartscenter.org/events) - Monthly art exchange
- Brewsters Beer Garden (brewstersbeergarden.com/calendar1) - Live music, trivia
- Cool Petaluma (coolpetaluma.org/events) - Climate/sustainability events
- 350 Petaluma (350petaluma.org/events) - Monthly bike rides
- Brooks Note Winery (brooksnotewinery.com/event-calendar/) - Friday music
- Petaluma People Services (petalumapeople.org/events) - Senior programs
- Healthy Petaluma (healthypetaluma.org/calendar-of-events) - Health events

### Live music venues
- McNear's Saloon (mcnears.com/our-events/) - Comedy + live events
- Montagne Russe Winery (russewines.com/Events) - Weekly Saturday music
- Griffo Distillery (griffodistillery.com/pages/calendar) - Weekly Thursday jam

### WordPress/iCal sites (try `?ical=1` endpoint)
- Petaluma Elks Lodge (elks901.org/calendar-of-events/) - Craft faires, dinners
- Petaluma Wetlands Alliance (petalumawetlands.org/calendar/) - Bird walks
- Petaluma Garden Club (petalumagardenclub.org/calendar/) - Monthly meetings
- Petaluma Bounty (petalumabounty.org/events-calendar/) - Farm volunteer hours

### Other platforms
- Rotary Club of Petaluma (ClubRunner - try portal.clubrunner.ca/10088/events/ical)
- Village Network of Petaluma (ClubExpress - check for iCal)
- Blue Zones Project Petaluma (Eventbrite - may already be captured)
- Sonoma County Regional Parks (parks.sonomacounty.ca.gov/play/calendar/hiking)
- Petaluma Cycling Club (Wild Apricot - no native ICS)
- Empire Runners Club (Wild Apricot - no native ICS)
- Petaluma River Park (petalumariverpark.org/calendar - weekly Tuesday walks)
- Petaluma Historical Library & Museum (petalumamuseum.com/events/) - concerts, speakers
- Sonoma-Marin Fairgrounds (sonoma-marinfair.org/calendar) - check closer to summer fair season

---

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Petaluma website | Cloudflare protection |
| Various Marin-based Meetup groups | Too far from Petaluma |
| Mindful-Monday Meetup | Virtual conference calls, not local |
| Petaluma Wildlife Museum | School tours/private events, not public |
| Youth sports leagues | Member-only platforms, no public calendar exports (see below) |

### Youth Sports Research (2026-02-14)

Extensively investigated: Petaluma National/American Little League (BlueSombrero), Leghorns Baseball, AYSO Region 26 (wrong city), Petaluma Youth Soccer (domain dead), Girls Softball (site down), Swim Team (not active), Parks & Rec (Cloudflare), RecDesk (not found). Platforms checked: GameChanger, TeamSnap, SportsEngine, LeagueApps, GotSport, TourneyMachine, ActiveNet, RecDesk. None viable. High school athletics via MaxPreps already covers public-facing school sports.
