# Santa Rosa Source Analysis

Date: 2026-02-23

## Summary

All 47 Santa Rosa sources now have authoritative URLs configured in `SOURCE_URLS`.

## Source Categories

### Primary Sources (Direct from Venue/Organization)

These sources provide event data directly from the authoritative source:

| Source | URL | Type |
|--------|-----|------|
| Arlene Francis Center | https://arlenefranciscenter.org/calendar/ | Google Calendar |
| Luther Burbank Center | https://lutherburbankcenter.org/events/ | WordPress ICS |
| Schulz Museum | https://schulzmuseum.org/events/ | WordPress ICS |
| Sonoma County Library | https://sonomalibrary.org/events | Custom Scraper |
| Sonoma County Parks | https://parks.sonomacounty.ca.gov/events/ | Custom Scraper |
| Sonoma County Government | https://sonomacounty.ca.gov/calendar/ | Custom Scraper |
| Jack London State Historic Park | https://jacklondonpark.com/events/ | Custom Scraper |
| GoLocal Cooperative | https://golocal.coop/events/ | WordPress ICS |
| Sonoma County AA | https://sonomacountyaa.org/events/ | WordPress ICS |
| Sonoma County DSA | https://dsasonomacounty.org/events/ | Google Calendar |
| Copperfield's Books | https://www.copperfieldsbooks.com/events | Custom Scraper |
| Cal Theatre | https://www.facebook.com/CalTheatrePT/ | Custom Scraper |
| Cafe Frida | https://www.cafefrida.com/ | Wix Scraper |
| Santa Rosa Cycling Club | https://srcc.memberlodge.com/page-1363886 | Custom Scraper |
| Barrel Proof Lounge | https://www.barrelprooflounge.com/live-events | Custom Scraper |
| Sports Basement | https://www.sportsbasement.com/pages/santa-rosa | Elfsight Scraper |
| Sebastopol Center for Arts | https://www.sebarts.org/calendar/ | Custom Scraper |
| Santa Rosa Arts Center | https://santarosaartscenter.org/events/ | Custom Scraper |
| MovingWriting | https://www.movingwriting.com/workshops | Custom Scraper |
| City of Santa Rosa Legistar | https://santa-rosa.legistar.com/Calendar.aspx | Legistar API |
| Spreckels Performing Arts | https://www.spreckelsonline.com/events/ | Custom Scraper |
| Lagunitas Brewing | https://lagunitas.com/taproom/petaluma | Custom Scraper |
| Creative Sonoma | https://creativesonoma.org/events/ | Custom Scraper |
| Cinnabar Theater | https://www.cinnabartheater.org/whats-on/ | Custom Scraper |
| Green Music Center | https://gmc.sonoma.edu/events/ | Custom Scraper |
| Riley Street Art Supply | https://www.rileystreet.com/pages/santa-rosa-classes-events | Tockify |
| Santa Rosa Junior College | https://calendar.santarosa.edu/ | LiveWhale ICS |
| Museum of Sonoma County | https://museumsc.org/events/ | Custom Scraper |
| Sonoma.com | https://www.sonoma.com/events/ | WordPress ICS |

### Aggregators

These sources aggregate events from multiple venues. They are useful for discovery but may have data quality issues:

| Source | URL | Notes |
|--------|-----|-------|
| North Bay Bohemian | https://bohemian.com/events-calendar/ | CitySpark scraper |
| Press Democrat | https://www.pressdemocrat.com/events/ | CitySpark scraper |

**Known Issue:** The Press Democrat aggregator incorrectly converted "9:30 AM" to "9:30 PM" for the Jack London State Historic Park "Beneath the Canopy" event on Feb 22, 2026. This appears to be an input error in their system, not a scraping bug. This validates the approach of preferring primary sources over aggregators.

### High School Athletics (MaxPreps)

| Source | URL |
|--------|-----|
| Santa Rosa High | https://www.maxpreps.com/ca/santa-rosa/santa-rosa-panthers/ |
| Montgomery High | https://www.maxpreps.com/ca/santa-rosa/montgomery-vikings/ |
| Maria Carrillo High | https://www.maxpreps.com/ca/santa-rosa/maria-carrillo-pumas/ |
| Piner High | https://www.maxpreps.com/ca/santa-rosa/piner-prospectors/ |
| Elsie Allen High | https://www.maxpreps.com/ca/santa-rosa/elsie-allen-lobos/ |
| Cardinal Newman High | https://www.maxpreps.com/ca/santa-rosa/cardinal-newman-cardinals/ |

### Meetup Groups

| Source | URL |
|--------|-----|
| Go Wild Hikers | https://www.meetup.com/sonoma-county-go-wild-hikers/ |
| Shut Up & Write Wine Country | https://www.meetup.com/shutupandwritewinecountry/ |
| Scottish Country Dancing | https://www.meetup.com/scottish-country-dancing/ |
| Women's Wine Club | https://www.meetup.com/sonoma-county-womens-wine-club/ |
| Santa Rosa Toastmasters | https://www.meetup.com/santa-rosa-toastmasters-public-speaking-meetup-group/ |
| Nataraja Yoga | https://www.meetup.com/nataraja-school-of-traditional-yoga/ |
| Women's Creativity Collective | https://www.meetup.com/santa-rosa-womens-creativity-collective/ |
| Sonoma County Boomers | https://www.meetup.com/sonoma-county-boomers/ |
| AMORC Santa Rosa | https://www.meetup.com/amorc-santa-rosa-pronaos/ |
| SAROGN | https://www.meetup.com/sarogn/ |

## Lessons Learned

### Aggregator Data Quality

The Jack London Park time error illustrates why we prioritize primary sources:

- **Source (Jack London Park):** "When: Sunday, February 22, 2026, 9:30 am to 12:00 pm"
- **Aggregator (Press Democrat):** `DTSTART:20260222T213000` (9:30 PM) ❌

This is likely an input error in the Press Democrat's event submission system, not a scraping bug. When events are manually entered into aggregator systems, AM/PM mistakes are common.

### Solution: Primary Source Scraping

We added a scraper for Jack London State Historic Park that:
1. Pulls directly from the authoritative source
2. Correctly parses times in multiple formats ("9:30 am", "9:00 a.m.")
3. Handles events with and without time information

This approach ensures accurate event times regardless of aggregator data quality.

## URL Coverage Status

As of this analysis:
- **Santa Rosa:** 47/47 sources have URLs (100%)
- **Other cities:** Still need URL additions (see `docs/source-links.md`)
