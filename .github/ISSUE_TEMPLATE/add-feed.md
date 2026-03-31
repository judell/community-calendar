---
name: Add an event feed
about: Suggest an ICS/iCal feed to add to a city's calendar
title: "Add feed: SOURCE_NAME (CITY)"
labels: feed-request
---

**City:** (e.g., bloomington, santarosa)

**Source name:** (e.g., "Harmony School Calendar")

**Feed URL:** (the ICS/iCal URL)

**Events page URL:** (the human-readable calendar page — this is used as a fallback link on event cards when the feed doesn't include per-event URLs)

**Notes:** (anything else — what kind of events, how you found it, etc.)

---

### Why we need the events page URL

Many calendar feeds (especially Google Calendar) don't include URLs for individual events. When that happens, we use the **events page URL** as a fallback so that event cards in the calendar link somewhere useful instead of nowhere.

In `feeds.txt`, this looks like:
```
# Harmony School Calendar | https://harmonyschool.org/calendar/
https://calendar.google.com/calendar/ical/...@group.calendar.google.com/public/basic.ics
```

The part after `|` is the fallback URL.
