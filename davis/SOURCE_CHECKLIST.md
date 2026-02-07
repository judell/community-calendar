# Davis Calendar Source Checklist

Prioritized list of potential event sources for the Davis community calendar.

## ✅ Currently Implemented

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| UC Davis Arts | ICS | ~152 | `arts.ucdavis.edu` monthly ICS feeds |
| UC Davis Library | ICS | ~89 | `events.library.ucdavis.edu/calendar/1.ics` |
| UC Davis CampusGroups | ICS | ~297 | `aggielife.ucdavis.edu` - student orgs |
| Yolo County Library | RSS | ~129 | LibCal RSS, filtered to Davis branches |
| Davis Downtown | ICS | ~5 | WordPress Events Calendar plugin |
| UU Davis | ICS | ~17 | Google Calendar ICS feeds |
| Mondavi Center | Scraper | ~12 | HTML scraper for performing arts |
| Davis Chamber | XML | ~16 | MemberClicks XML API |
| UC Davis Athletics | ICS | ~309 | Sidearm Sports ICS feed |

---

## 🎯 Tier 1: Easy Wins (ICS/RSS Available)

These have machine-readable feeds ready to use.

| Source | URL | Feed Type | Priority | Notes |
|--------|-----|-----------|----------|-------|
| **Pence Gallery** | pencegallery.org/exhibitions-events | RSS | HIGH | Has WordPress RSS feed |
| **UU Church Davis** | uudavis.org/calendar | Google Cal | HIGH | Embedded Google Calendar - can extract ICS |
| **Davis Farmers Market** | davisfarmersmarket.org | Check | MEDIUM | May have hidden ICS |

### Google Calendar ICS URLs (from UU Davis):
```
# UU Davis main calendar
https://calendar.google.com/calendar/ical/uudavis%40gmail.com/public/basic.ics

# Additional UU calendars embedded:
# 0p5ed7hbg4p7b4atf3lgjmgic@group.calendar.google.com
# l7ct33327vaeffd8iu8ij0hjdg@group.calendar.google.com
# da9geoarq2p3o4ukb8vqseat8g@group.calendar.google.com
```

---

## 🔧 Tier 2: Structured HTML (Moderate Effort)

Well-structured pages that would need HTML scrapers.

### HIGH PRIORITY

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| **UC Davis Mondavi Center** | mondaviarts.org/events | Custom | Medium | High-value performing arts |
| **Manetti Shrem Museum** | manettishremmuseum.ucdavis.edu/events | Custom | Medium | Art exhibitions, events |
| **Davis Chamber** | web.davischamber.com/events | MemberClicks | Medium | Business/community events |
| **UC Davis Athletics** | ucdavisaggies.com/calendar | Sidearm | Medium | Sports schedules |

### MEDIUM PRIORITY

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| **Davis Food Co-op** | davisfood.coop/events | Custom | Low | Classes, tastings |
| **Sophia's Thai Kitchen** | sophiastkitchen.com/events | TBD | Low | Live music venue |
| **Woodstock's Pizza** | woodstocksdavis.com/events | TBD | Low | Music nights |
| **UC Davis Extension** | extension.ucdavis.edu/events | Custom | Medium | Workshops, continuing ed |
| **UC Davis Main Events** | ucdavis.edu/events | Drupal | Medium | Campus-wide aggregator |

### LOWER PRIORITY

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| **Hattie Weber Museum** | hattiewebermuseum.org/events | TBD | Low | Small local history |
| **Davis Community Church** | dccpres.org/events | TBD | Low | Community events |
| **Armadillo Music** | armadillomusic.com/pages/events | TBD | Low | Music event links |

---

## 📚 Tier 3: Schools & Government

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| **DJUSD Calendar** | djusd.net/about/calendar | SharpSchool | High | District calendar, complex platform |
| **Davis Senior High** | dshs.djusd.net/activities | SharpSchool | High | Sports, performances |
| **Da Vinci Charter** | davincicharter.org/calendar | TBD | Medium | May have Google Calendar backend |
| **Davis Senior Center** | cityofdavis.org/.../senior-services | Blocked | High | CDN blocking requests |
| **City of Davis** | cityofdavis.org/city-hall/city-calendar | Blocked | N/A | Akamai CDN access denied |

---

## 🚴 Tier 4: Recreation & Clubs

| Source | URL | Type | Notes |
|--------|-----|------|-------|
| **Davis Bike Club** | davisbikeclub.org/rides-events | HTML | Timeout issues, may need retry |
| **Whole Earth Festival** | wholeearthfestival.org | Seasonal | Annual event, check when active |

---

## ❌ Non-Starters

| Source | Reason |
|--------|--------|
| Visit Davis | Domain for sale |
| Facebook Groups | Not publicly exportable |
| Instagram-only venues | No structured data |
| Eventbrite (general) | No clean public feed |
| City of Davis | CDN blocking |

---

## 📋 Implementation Roadmap

### Phase 1 (Quick wins)
1. [x] UU Davis Google Calendar ICS extraction
2. [~] Pence Gallery - BLOCKED: RSS empty, My Calendar API disabled. Needs HTML scraper.

### Phase 2 (High-value HTML scrapers)
3. [x] Mondavi Center scraper
4. [~] Manetti Shrem Museum - BLOCKED: Cloudflare Turnstile. Also currently shows "no events".
5. [x] Davis Chamber - MemberClicks XML API works!

### Phase 3 (Sports & Recreation)
6. [x] UC Davis Athletics - Sidearm ICS feed works!
7. [~] Davis Food Co-op - BLOCKED: Captcha redirect

### Phase 4 (Music Venues)
8. [ ] Sophia's Thai Kitchen scraper
9. [ ] Woodstock's Pizza scraper

### Phase 5 (Schools - if needed)
10. [ ] DJUSD calendar (complex)

---

## Notes

### Probe Commands
```bash
# Check for hidden ICS/RSS
curl -sL "<URL>" | grep -i -E "(ical|\\.ics|webcal|calendar\\.google|rss|xml|feed)"

# Extract Google Calendar ICS from embed
# Look for: src="https://calendar.google.com/calendar/embed?..."
# Convert calendar ID to: https://calendar.google.com/calendar/ical/<ID>/public/basic.ics
```

### Platform Notes
- **MemberClicks**: Used by Davis Chamber, no standard feed
- **SharpSchool**: Used by DJUSD, complex CMS
- **Sidearm Sports**: Used by UC Davis Athletics, may have ICS per team
- **Localist**: Used by UC Davis Library, has ICS feeds
- **CampusGroups**: Used by Aggie Life, has master ICS feed
