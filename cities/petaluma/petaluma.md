# Petaluma, CA - City Discovery Progress

**Started:** 2025-02-12

## Overview
Petaluma is a city in Sonoma County, CA, about 40 miles north of San Francisco. Population ~60,000.

## Discovery Status

### Phase 1: Meetup Discovery ✅
- [x] Browse Meetup groups for Petaluma area - Found 73 groups
- [x] Test ICS feeds - 26 groups have active events
- [x] Verify locations are in Petaluma - 10 groups are actually in Petaluma

**Petaluma-based groups with events:**
| Group | Events | Description |
|-------|--------|-------------|
| petaluma-salon | 1 | Book Club (Infinite Jest) |
| sonoma-marin-brat-pack | 2 | Social events |
| mindfulnesspetaluma | 10 | Meditation/mindfulness |
| the-rebel-craft-collective | 6 | Happy Hour Crafts |
| meetup-group-bwkyqavs | 10 | Candlelight Yoga @ Hotel Petaluma |
| petaluma-book-and-brew-club | 1 | Book club |
| Mindful-Monday | 10 | Meditation conference calls (virtual?) |
| petaluma-figure-drawing-meetup-group | 1 | Figure Drawing at Suite G Studio |
| petaluma-active-20-30 | 2 | Business meetings |
| aligned-profitable-business-growth-for-women | 1 | Women's business |

### Phase 2: Eventbrite Scraping ✅
- [x] Run Eventbrite scraper for Petaluma
- [x] Identify key venues

**Results:** 14 local events from 20 scraped

**Key venues discovered:**
- Lagunitas Brewing Company (multiple events)
- Della Fattoria Downtown Café
- Petaluma Veterans Building
- Brooks Note Winery

### Phase 3: Local Sources ✅

#### Petaluma Downtown Association Calendar (Tockify)
- **URL:** https://tockify.com/api/feeds/ics/pdaevents
- **Events:** 71 events!
- **Content:** Downtown events, live music, art openings, festivals

#### City of Petaluma
- **Status:** Cloudflare protected - cannot scrape directly
- **Alternative:** Many city events appear on Downtown Association calendar

#### Sonoma County Library
- **Status:** Already covered by existing `library_intercept.py` scraper for Santa Rosa
- **Note:** Should work for Petaluma branch events too

#### Mystic Theatre
- **Status:** No ICS feed available (WordPress/SeeTickets)
- **Events:** Comedy, concerts (Jackie Kashian, etc.)
- **Potential:** Could build scraper, but may duplicate Eventbrite

#### Petaluma Arts Center
- **Status:** Squarespace site, no easy feed access
- **Potential:** Would need custom scraper

### Phase 4: Integration
- [ ] Add to workflow
- [ ] Add to combine_ics.py  
- [ ] Add to index.html

### Phase 5: Additional Discovery
- [x] Search for other Tockify calendars - Found Petaluma Wildlife Museum (81 events but mostly private)
- [x] Check Petaluma Historical Museum - No feed available
- [x] Check Petaluma Wetlands Alliance - No feed available

---

## Recommended Sources to Implement

### High Priority (Ready Now)
1. **Petaluma Downtown Association** - Tockify feed with 71 events
2. **Eventbrite Petaluma** - Scraper already exists
3. **Select Meetup groups** - Focus on local in-person events

### Meetup Groups to Add
| Group | Short Name | Events | Recommendation |
|-------|------------|--------|----------------|
| mindfulnesspetaluma | mindfulpetaluma | 10 | ✅ Add |
| the-rebel-craft-collective | rebelcraft | 6 | ✅ Add |
| meetup-group-bwkyqavs | yogapetaluma | 10 | ✅ Add |
| petaluma-figure-drawing-meetup-group | figuredrawing | 1 | ✅ Add |
| sonoma-marin-brat-pack | bratpack | 2 | ✅ Add |

### Excluded Sources
- **Mindful-Monday** - Virtual conference calls, not local
- **petaluma-active-20-30** - Business meetings, not public events
- **petaluma-salon** - Book club with 1 event, low volume

---

## Discovery Log

### 2025-02-12 - Initial Discovery

1. **Meetup Discovery**
   - Searched Meetup for groups near Petaluma, CA
   - Found 73 groups total
   - 26 groups have active events
   - 10 groups are actually based in Petaluma

2. **Eventbrite Scraping**
   - Ran scraper for ca--petaluma
   - Found 14 local events
   - Key venues: Lagunitas, Della Fattoria, Veterans Building

3. **Local Source Research**
   - Found Tockify calendar on Petaluma Downtown Association (71 events!)
   - City of Petaluma is Cloudflare protected
   - Mystic Theatre has no feed (would need scraper)
   - Petaluma Arts Center is Squarespace (no easy feed)

4. **Overlap with Santa Rosa**
   - Some Meetup groups serve both cities
   - Sonoma County Library already scraped for Santa Rosa
   - Consider sharing sources vs dedicated Petaluma city

5. **Additional Source Search**
   - Petaluma Wildlife Museum has 81 events but mostly school tours/private
   - Petaluma Historical Museum has events but no feed
   - Petaluma Wetlands Alliance does regular walks but no feed

---

## Summary - Ready to Implement

### High-Value Sources (98+ events total)

| Source | Type | Events | Priority |
|--------|------|--------|----------|
| Petaluma Downtown Association | Tockify | 71 | HIGH |
| Eventbrite Petaluma | Scraper | 14 | HIGH |
| mindfulnesspetaluma | Meetup | 10 | MEDIUM |
| meetup-group-bwkyqavs (Yoga) | Meetup | 10 | MEDIUM |
| the-rebel-craft-collective | Meetup | 6 | MEDIUM |
| sonoma-marin-brat-pack | Meetup | 2 | LOW |
| petaluma-figure-drawing | Meetup | 1 | LOW |

### Next Steps
1. Add Tockify feed to workflow
2. Add Eventbrite scraper command
3. Add 5 Meetup ICS feeds
4. Add SOURCE_NAMES to combine_ics.py
5. Add Petaluma to index.html city picker
