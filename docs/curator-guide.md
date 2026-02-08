# Community Calendar Curator Guide

This guide helps curators discover and add event sources for new cities.

## Quick Start

1. **Search for existing feeds** using platform searches
2. **Test discovered feeds** to verify they work
3. **Document findings** in the city's `SOURCES_CHECKLIST.md`
4. **Add working feeds** to the GitHub Actions workflow

---

## Step 1: Platform Searches

Use DuckDuckGo (Google may block automated queries). Replace `{city}` and `{state}` with your target location.

### High-Value Searches (do these first)

| Search | What You'll Find |
|--------|------------------|
| `{city} {state} site:meetup.com` | Meetup groups with ICS feeds |
| `{city} site:tockify.com` | Tockify calendars with ICS feeds |
| `{city} {state} inurl:/localist/` | University/govt Localist calendars |

### Discovery Searches (find potential sources)

| Search | What You'll Find |
|--------|------------------|
| `{city} {state} events site:facebook.com/events` | Active local events (no feed, but shows what exists) |
| `{city} {state} events site:eventbrite.com` | Eventbrite events (requires scraper) |
| `{city} {state} "community calendar"` | Local event aggregators |
| `{city} {state} events calendar` | General discovery |

### Ready-to-Use URLs

Copy these and replace `CITY` and `STATE`:

```
https://duckduckgo.com/?q=CITY+STATE+site%3Ameetup.com
https://duckduckgo.com/?q=CITY+site%3Atockify.com
https://duckduckgo.com/?q=CITY+STATE+inurl%3A%2Flocalist%2F
https://duckduckgo.com/?q=CITY+STATE+events+site%3Afacebook.com%2Fevents
https://duckduckgo.com/?q=CITY+STATE+events+site%3Aeventbrite.com
https://duckduckgo.com/?q=CITY+STATE+%22community+calendar%22
```

---

## Step 2: Test Discovered Feeds

### Tockify Calendar

If you find a Tockify calendar (URL like `tockify.com/calendarname/...`):

```bash
# Extract calendar name from URL and test
curl -sL "https://tockify.com/api/feeds/ics/CALENDAR_NAME" | grep -c "BEGIN:VEVENT"
```

If it returns a number > 0, the feed works!

### Meetup Group

If you find a Meetup group (URL like `meetup.com/groupname/`):

```bash
# Test ICS feed
curl -sL "https://www.meetup.com/GROUP_NAME/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
```

**Important**: Also verify the group's events are actually in your target city:
```bash
curl -sL "https://www.meetup.com/GROUP_NAME/" -A "Mozilla/5.0" | grep -oP '"city"\s*:\s*"\K[^"]+'
```

### Localist Site

If you find a Localist calendar:

```bash
# Check for API
curl -sL "https://DOMAIN/api/2/events" | head -50

# Or look for ICS export option on the site
```

### WordPress Site

If you find a WordPress events page:

```bash
# Check what plugins they use
curl -sL "URL" -A "Mozilla/5.0" | grep -o "wp-content/plugins/[^/]*" | sort -u

# Try common feed endpoints
curl -sL "URL/?ical=1" | head -20
curl -sL "URL/feed/" | head -20
```

---

## Step 3: Document Findings

Create or update `{city}/SOURCES_CHECKLIST.md`:

```markdown
# {City} Sources Checklist

## Currently Implemented
- [ ] Source 1 - feed URL
- [ ] Source 2 - feed URL

## Discovered - Ready to Add
- [ ] Tockify: calendar_name (X events)
- [ ] Meetup: group_name (verified in-city)

## Discovered - Needs Scraper
- [ ] Site name - platform (Eventbrite, etc.)

## Non-Starters
- Site name - reason (Wix - no feed, Cloudflare blocked, etc.)

## To Investigate
- Site name - URL - notes
```

---

## Step 4: Add Working Feeds

### Tockify Feed

Add to `.github/workflows/generate-calendar.yml`:

```yaml
- name: Download {city} Tockify feeds
  run: |
    curl -sL "https://tockify.com/api/feeds/ics/CALENDAR_NAME" -o {city}/tockify_name.ics || true
```

Add to `combine_ics.py` SOURCE_NAMES:
```python
'tockify_name': 'Calendar Display Name',
```

### Meetup Feed

Add to workflow:
```yaml
- name: Download {city} Meetup feeds  
  run: |
    curl -sL -A "Mozilla/5.0" "https://www.meetup.com/GROUP_NAME/events/ical/" -o {city}/meetup_name.ics || true
```

Add to `combine_ics.py`:
```python
'meetup_name': 'Meetup: Group Display Name',
```

---

## Platform Reference

| Platform | Has Feed? | How to Get It |
|----------|-----------|---------------|
| **Tockify** | ✅ Yes | `tockify.com/api/feeds/ics/{name}` |
| **Meetup** | ✅ Yes | `meetup.com/{group}/events/ical/` |
| **Localist** | ✅ Usually | Check `/api/2/events` or site UI |
| **Google Calendar** | ✅ Yes | Extract calendar ID from embed |
| **The Events Calendar (WordPress)** | ✅ Usually | Try `?ical=1` on events page |
| **Facebook Events** | ❌ No | No public API since 2018 |
| **Eventbrite** | ❌ No | Use `eventbrite_scraper.py` |
| **Wix** | ❌ No | No calendar export |
| **Squarespace** | ❌ No | No standard export |
| **Simpleview (tourism sites)** | ❌ No | No public feed |

---

## Tips

1. **Start with Meetup** - Most groups have working ICS feeds

2. **Tockify is a goldmine** - When you find one, it usually has lots of events

3. **University calendars often use Localist** - Search for nearby colleges

4. **Tourism/visitor bureau sites rarely have feeds** - Don't spend time on these

5. **Facebook shows activity but no feeds** - Use it to discover what events exist, then find alternate sources

6. **Test feeds before adding** - Some groups are inactive or have travel events

7. **Check event locations** - Meetup groups may have events outside your target city
