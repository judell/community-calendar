# Notes for Blog Posts

Interesting findings and stories from the community calendar project.

---

## Why Primary Sources Beat Aggregators (2026-02-23)

Discovered a time error in an event listing:

- **Event:** "Beneath the Canopy" at Jack London State Historic Park, Feb 22, 2026
- **Press Democrat (aggregator):** Listed as 9:30 PM
- **Jack London Park (source):** Actually 9:30 AM to 12:00 PM

### Root Cause

This wasn't a scraping bug. The Press Democrat doesn't scrape Jack London Park - they have an event submission system where venues manually enter their events. Someone made an AM/PM input error.

### The Fix

We added a scraper that pulls directly from `jacklondonpark.com/events/`. Now we get the correct time regardless of what aggregators publish.

### The Lesson

Aggregators introduce a human-in-the-loop where input errors can occur. Primary sources are authoritative. When you can scrape the source directly, do it.

This validates the project's philosophy: push toward authoritative sources rather than relying on aggregators that may have stale or incorrect data.
