# Petaluma Calendar Source Checklist

## Currently Implemented (all in CI)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Petaluma Downtown Association | Tockify ICS | 71 | ✅ In CI |
| Aqus Community | MembershipWorks ICS | 87 | ✅ In CI |
| Petaluma Regional Library | Scraper | 155 | ✅ In CI |
| Petaluma Chamber of Commerce | GrowthZone Scraper | 80 | ✅ In CI |
| Mystic Theatre | Scraper | 12 | ✅ In CI |
| ~~Eventbrite Petaluma~~ | ~~Scraper~~ | — | Retired 2026-02-15: scraper broken |
| Petaluma High School Athletics | MaxPreps Scraper | 9 | ✅ In CI |
| Casa Grande High School Athletics | MaxPreps Scraper | 8 | ✅ In CI |
| SRJC Petaluma Campus | LiveWhale Scraper | 17 | ✅ In CI |
| HenHouse Brewing Petaluma | Scraper | 2-3 | ✅ In CI |
| ~~Phoenix Theater~~ | ~~Eventbrite Scraper~~ | — | Retired 2026-02-15: Eventbrite-dependent |
| Mercury Theater | Squarespace JSON Scraper | 12 | ✅ In CI |
| Adobe Road Winery | JSON-LD Scraper | 8 | ✅ In CI |
| The Big Easy | WordPress iCal | ~30 | ✅ In CI |
| Polly Klaas Community Theater | WordPress iCal | ~8 | ✅ In CI |
| Brooks Note Winery | Google Calendar ICS | ~142 | ✅ In CI |
| Petaluma Arts Center | Squarespace Scraper | ~10 | ✅ In CI |
| Brewsters Beer Garden | Squarespace Scraper | ~18 | ✅ In CI |
| Cool Petaluma | Squarespace Scraper | ~6 | ✅ In CI |
| McNear's Saloon | WordPress iCal | ~2 | ✅ In CI |
| Griffo Distillery | Tockify ICS | ~20 | ✅ In CI |
| Petaluma Elks Lodge | Google Calendar ICS | ~568 | ✅ In CI |
| Petaluma Garden Club | Google Calendar ICS | ~131 | ✅ In CI |
| Petaluma Bounty | WordPress iCal | ~19 | ✅ In CI |
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

**Total: ~1440+ events (before deduplication)**

---

## To Investigate

### Needs custom scraper
- Montagne Russe Winery (russewines.com/Events) - WineDirect platform, HTML scraping needed, ~6 events
- Cinnabar Theater (cinnabartheater.org/shows/) - WordPress + Beaver Builder, HTML-only, 5 shows

### Not yet investigated
- Village Network of Petaluma (ClubExpress - check for iCal)
- Blue Zones Project Petaluma (Eventbrite-based, likely no public feed)
- Sonoma County Regional Parks (parks.sonomacounty.ca.gov/play/calendar/hiking)
- Petaluma Cycling Club (Wild Apricot - no native ICS)
- Empire Runners Club (Wild Apricot - no native ICS)
- Petaluma River Park (petalumariverpark.org/calendar - weekly Tuesday walks)
- Petaluma Historical Library & Museum (petalumamuseum.com/events/) - concerts, speakers
- Sonoma-Marin Fairgrounds (sonoma-marinfair.org/calendar) - check closer to summer fair season
- Healthy Petaluma (healthypetaluma.org/calendar-of-events) - Squarespace, 10 upcoming but board meetings only
- Petaluma Wetlands Alliance (petalumawetlands.org/calendar/) - not yet checked

---

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Petaluma website | Cloudflare protection |
| Various Marin-based Meetup groups | Too far from Petaluma |
| Mindful-Monday Meetup | Virtual conference calls, not local |
| Petaluma Wildlife Museum | School tours/private events, not public |
| Youth sports leagues | Member-only platforms, no public calendar exports (see below) |
| WonderStump! | Squarespace but no events collection; Ticket Tailor behind Cloudflare |
| 350 Petaluma | Squarespace events but dead since Oct 2023 |
| Petaluma People Services | Squarespace but hand-curated page, not events collection |
| Rotary Club of Petaluma | ClubRunner site deactivated |

### Youth Sports Research (2026-02-14)

Extensively investigated: Petaluma National/American Little League (BlueSombrero), Leghorns Baseball, AYSO Region 26 (wrong city), Petaluma Youth Soccer (domain dead), Girls Softball (site down), Swim Team (not active), Parks & Rec (Cloudflare), RecDesk (not found). Platforms checked: GameChanger, TeamSnap, SportsEngine, LeagueApps, GotSport, TourneyMachine, ActiveNet, RecDesk. None viable. High school athletics via MaxPreps already covers public-facing school sports.
