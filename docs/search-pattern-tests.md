# Search Pattern Discovery Tests

**Tested**: February 2026

## Summary of Findings

### What Works Well

| Search Pattern | Effectiveness | Notes |
|----------------|---------------|-------|
| `site:facebook.com/events {city} {state}` | ✅ Excellent | Finds FB events index + individual events |
| `site:meetup.com {city} {state}` | ✅ Excellent | Finds groups (which have ICS feeds) |
| `site:eventbrite.com {city} {state}` | ✅ Excellent | Finds event listings |
| `site:tockify.com {city}` | ✅ Good | Tockify calendars have ICS feeds |
| `{city} {state} inurl:/localist/` | ✅ Good | Finds university/govt calendars |
| `{city} {state} "community calendar"` | ✅ Good | Finds local aggregators |

### What Has Limitations

| Search Pattern | Issue |
|----------------|-------|
| `inurl:/tribe_events/` | May confuse "tribe" with Native American content |
| `"subscribe to calendar" {city}` | Too specific, few results |
| `site:squarespace.com` | Finds sites but no standard feed format |

### Platform Feed Availability

| Platform | Has Feed? | Feed URL Pattern |
|----------|-----------|------------------|
| **Tockify** | ✅ Yes | `https://tockify.com/api/feeds/ics/{calendar_name}` |
| **Meetup** | ✅ Yes | `https://www.meetup.com/{group}/events/ical/` |
| **Facebook Events** | ❌ No | No public API since 2018 |
| **Eventbrite** | ❌ No | Requires scraping |
| **Squarespace** | ❌ No | No standard calendar export |
| **Wix** | ❌ No | No standard calendar export |
| **Simpleview CMS** | ❌ No | Tourism sites, no public feed |
| **Localist** | ✅ Yes | Check `/api/2/events` or ICS export |

---

## Verified Working Feeds

### Tockify Calendars (ICS confirmed)

```bash
# San Diego Parks - 551 events
curl -sL "https://tockify.com/api/feeds/ics/sdparkscalendar" | grep -c "BEGIN:VEVENT"
# Output: 551

# Balboa Park - 2469 events  
curl -sL "https://tockify.com/api/feeds/ics/balboapark" | grep -c "BEGIN:VEVENT"
# Output: 2469
```

### Localist Platforms Found

- `events.in.gov` - Indiana State events (Localist)
- Various university `.enterprise.localist.com` subdomains

---

## Test Results by City

### Santa Rosa, CA

| Search | Results |
|--------|--------|
| Facebook Events | ✅ Found events page + individual events (WinterBlast 2025, etc.) |
| Meetup | ✅ Found groups page |
| Eventbrite | ✅ Found event listings |
| Tockify | ⚠️ Found unrelated events (not SR-specific calendars) |
| Community Calendar | ✅ Found posimages.org (Wix - no feed) |

### Bloomington, IN

| Search | Results |
|--------|--------|
| Facebook Events | ✅ Found events page + Pawtumn Fest, Big Red, etc. |
| Meetup | ✅ Found groups |
| Eventbrite | ✅ Found event listings |
| Tockify | ❌ `bloomington.arts.calendar` is offline |
| Localist | ✅ Found via IU connection |
| beInvolved | ✅ IU student events platform |

### Davis, CA

| Search | Results |
|--------|--------|
| Facebook Events | ✅ Found events (G Street Opening, Oktoberfest, etc.) |
| Meetup | ✅ Found groups |
| Eventbrite | ✅ Found event listings |
| visitdavis.org | ⚠️ Unknown platform, needs investigation |

---

## Recommended Curator Workflow

### Phase 1: Platform Searches

Run these DuckDuckGo searches (Google may block automated queries):

```
{city} {state} events site:facebook.com/events
{city} {state} site:meetup.com  
{city} {state} events site:eventbrite.com
{city} site:tockify.com
```

### Phase 2: Calendar Platform Detection

```
{city} {state} inurl:/localist/
{city} {state} inurl:/tribe_events/
{city} {state} "community calendar"
{city} {state} events calendar
```

### Phase 3: For Each Discovery

1. **Tockify calendar found**: Extract calendar name, test ICS feed
   ```bash
   curl -sL "https://tockify.com/api/feeds/ics/{name}" | grep -c "BEGIN:VEVENT"
   ```

2. **Meetup group found**: Test ICS feed
   ```bash
   curl -sL "https://www.meetup.com/{group}/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
   ```

3. **Localist site found**: Check for API/ICS
   ```bash
   curl -sL "https://{domain}/api/2/events" | head -50
   ```

4. **WordPress site found**: Check for plugins
   ```bash
   curl -sL "{url}" -A "Mozilla/5.0" | grep -o "wp-content/plugins/[^/]*" | sort -u
   ```

### Phase 4: Document Findings

Update city's `SOURCES_CHECKLIST.md` with:
- Working feeds (add to workflow)
- Potential sources (need scraper)
- Non-starters (and why)

---

## DuckDuckGo URL Templates

Copy-paste ready (replace `{city}` and `{state}`):

```
https://duckduckgo.com/?q={city}+{state}+events+site%3Afacebook.com%2Fevents
https://duckduckgo.com/?q={city}+{state}+site%3Ameetup.com
https://duckduckgo.com/?q={city}+{state}+events+site%3Aeventbrite.com
https://duckduckgo.com/?q={city}+site%3Atockify.com
https://duckduckgo.com/?q={city}+{state}+inurl%3A%2Flocalist%2F
https://duckduckgo.com/?q={city}+{state}+%22community+calendar%22
```

---

## Additional Discoveries

### CampusGroups Platform (ICS Available)

Found UC Davis AggieLife uses CampusGroups, which has a master ICS feed:

```bash
# UC Davis AggieLife - 606 events!
curl -sL "https://aggielife.ucdavis.edu/ical/ucdavis/ical_ucdavis.ics" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
```

**Discovery method**: Search `site:ucdavis.edu events calendar`, found `aggielife.ucdavis.edu`, inspected page for ICS links.

### Tockify Calendars Near Target Cities

| Calendar | Events | Location | Relevance |
|----------|--------|----------|----------|
| sdparkscalendar | 551 | San Diego | Example |
| balboapark | 2469 | San Diego | Example |
| anderson.university | 339 | Anderson, IN | 100mi from Bloomington |

### Search Pattern Refinements

- `site:tockify.com {region}` better than `{city} site:tockify.com` for finding nearby calendars
- University searches (`{university} events site:tockify.com`) can find campus calendars
- CampusGroups sites often have ICS feeds - look for `/ical/` in page source

---

## Key Insights

1. **Facebook & Meetup searches are most reliable** - They surface local event activity even if no feed available

2. **Tockify is a goldmine when found** - Real ICS feeds with good event counts

3. **Localist common for universities/government** - Worth searching `site:localist.com` for nearby institutions

4. **Many "community calendars" are Wix/Squarespace** - Look good but no feed export

5. **Tourism sites (Simpleview) are dead ends** - visitbloomington.com, etc. have no public feeds

6. **inurl: searches can have false positives** - `tribe_events` matches Native American content
