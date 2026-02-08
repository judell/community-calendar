# Santa Rosa / Sonoma County Calendar Source Checklist

## Currently Implemented

### Live ICS Feeds
| Source | URL | Notes |
|--------|-----|-------|
| Arlene Francis Theater | Google Calendar | Events at local theater |
| Luther Burbank Center | `lutherburbankcenter.org/events/?ical=1` | Major performing arts venue |
| Schulz Museum | `schulzmuseum.org/events/?ical=1` | Charles Schulz museum events |
| Sonoma.com | `sonoma.com/events/?ical=1` | Regional tourism/events |
| GoLocal Coop | `golocal.coop` Tribe Events | Local business coop |
| Sonoma County AA | `sonomacountyaa.org/events/?ical=1` | Recovery community |
| DSA Sonoma County | Google Calendar | Political org |

### Scraped Sources
| Source | Scraper | Notes |
|--------|---------|-------|
| Monroe County Library (Sonoma) | `library_intercept.py` | Library events |
| North Bay Bohemian | `cityspark/bohemian.py` | Alt-weekly events calendar |
| Press Democrat | `cityspark/pressdemocrat.py` | Newspaper events |
| Sonoma County Parks | `sonoma_parks.py` | Regional parks |
| California Theatre | `cal_theatre.py` | Historic theater |
| Copperfield's Books | `copperfields.py` | Bookstore events |
| Sonoma County Gov | `sonoma_county_gov.py` | Government meetings |
| Cafe Frida | Scraper | Music venue |
| SRCC | `srcc.py` | Santa Rosa Chamber? |
| Museum of Sonoma County | ICS | Local museum |

### City of Santa Rosa Calendars
Multiple ICS feeds from `srcity.org`:
- Main Calendar
- City Offices Closed
- Recreation and Parks
- Events

---

## Meetup Groups (Discovered 2025-02-08)

Ran Meetup discovery playbook. Found 66 groups, 33 with active events.

### Recommended High-Value Groups (Ready to Add)

| Group | ICS URL | Events | Category | Notes |
|-------|---------|--------|----------|-------|
| sonoma-county-go-wild-hikers | `meetup.com/sonoma-county-go-wild-hikers/events/ical/` | 3 | Outdoor | Local hiking group - "Islands in the Sky", "Lake Sonoma Hike" |
| shutupandwritewinecountry | `meetup.com/shutupandwritewinecountry/events/ical/` | 10 | Arts | Writing meetups in Petaluma/Sebastopol |
| scottish-country-dancing | `meetup.com/scottish-country-dancing/events/ical/` | 10 | Dance | Weekly classes at Monroe Hall |
| sonoma-county-womens-wine-club | `meetup.com/sonoma-county-womens-wine-club/events/ical/` | 9 | Social/Wine | Wine club + social events |
| santa-rosa-toastmasters-public-speaking-meetup-group | `meetup.com/santa-rosa-toastmasters-public-speaking-meetup-group/events/ical/` | 10 | Professional | Weekly meetings |
| nataraja-school-of-traditional-yoga | `meetup.com/nataraja-school-of-traditional-yoga/events/ical/` | 7 | Wellness | Yoga/pranayama classes |
| santa-rosa-womens-creativity-collective | `meetup.com/santa-rosa-womens-creativity-collective/events/ical/` | 6 | Arts | Creative workshops at The Arthaus |
| sonoma-county-boomers | `meetup.com/sonoma-county-boomers/events/ical/` | 6 | Social | Social events for boomers |
| The-International-Wanderers | `meetup.com/The-International-Wanderers/events/ical/` | 6 | Travel/Outdoor | Travel trips + local hiking retreats |
| culturelovers | `meetup.com/culturelovers/events/ical/` | 10 | Travel | International travel (may be less local) |

### Other Active Groups (Lower Priority)

| Group | Events | Notes |
|-------|--------|-------|
| Hidden-Backroads-Adventures | 10 | Speed dating / social events |
| PlayYourCourt-Santa-Rosa-Tennis | 10 | Tennis - may be commercial |
| apa-pool-league | 10 | Pool league |
| real-estate-investor-community-santa-rosa | 10 | Real estate networking |
| Alternative-Healing-Exploration | 10 | Healing workshops |
| northern-california-plant-medicine-community | 10 | Plant medicine events |
| the-unstruck-drum-center-for-shamanism-healing | 8 | Shamanism events |
| sarogn | 7 | Unknown category |
| the-santa-rosa-spiritual-experiences-group | 6 | Spiritual events |
| north-bay-social-group-20s-and-30s | 3 | Young adult social |
| bce-before-christian-era | 3 | Historical interest |
| entheogens-in-sonoma | 3 | Entheogens |
| Woodworking-Workshops-for-Women | 2 | Woodworking |
| lets-go-golden-girls | 2 | Women's social |
| full-circle-studio | 2 | Studio events |

### Groups with No Current Events
The following groups exist but had no upcoming events at time of discovery:
ai-northbay, ambgroup, bootstrapped-af-podcast-mastermind-group, happy-over-50, 
kayaking-sonoma-beyond, ladieswithnobabies, localbitcoin-meetup, north-bay-adventures, 
north-bay-hikers-born-1990-2000, santa-rosa-30s-40s-50s-meet-and-hangout-group, 
senior-walkabouters, sonoma-county-millennials, sonoma-county-shenanigans, 
Sonoma-County-Photography-Group, Sonoma-County-Wanderers, womens-wellness-meetup-group

---

## Potential Additional Sources

### Venues to Investigate
| Source | URL | Status |
|--------|-----|--------|
| Raven Performing Arts Theater | `raventheater.org` | PENDING |
| 6th Street Playhouse | `6thstreetplayhouse.com` | PENDING |
| Glaser Center | `glasercenter.com` | PENDING |
| Wells Fargo Center | ? | PENDING |

### Organizations
| Source | URL | Status |
|--------|-----|--------|
| Sonoma County Farm Trails | `farmtrails.org` | PENDING |
| Sonoma Land Trust | `sonomalandtrust.org` | PENDING |
| LandPaths | `landpaths.org` | PENDING - outdoor events |

### Colleges
| Source | URL | Status |
|--------|-----|--------|
| Santa Rosa Junior College | `santarosa.edu/events` | PENDING |
| Sonoma State University | `sonoma.edu/events` | PENDING |

---

## Notes

- Santa Rosa is the largest city in Sonoma County (Wine Country)
- Many events are wine/food related
- Strong outdoor recreation community (hiking, biking)
- Arts scene centered around downtown Santa Rosa
