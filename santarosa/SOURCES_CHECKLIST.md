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

## TODO: Meetup Discovery

Run the Meetup playbook to find local groups:
```bash
# Find groups near Santa Rosa
curl -sL "https://www.meetup.com/find/?keywords=&location=us--ca--Santa%20Rosa&source=GROUPS" -A "Mozilla/5.0" | grep -o '"urlname":"[^"]*"' | sort -u

# For each group, validate location
curl -sL "https://www.meetup.com/{group-name}/" -A "Mozilla/5.0" | grep -o '"city":"[^"]*"'

# Test ICS feed
curl -sL "https://www.meetup.com/{group-name}/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
```

### Topics to search:
- Hiking / outdoor recreation
- Wine / food
- Tech / maker
- Arts / music
- Sustainability / environment
- Birding / nature

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
