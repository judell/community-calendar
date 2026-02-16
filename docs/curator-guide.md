# Community Calendar Curator Guide

## Overview

Public events are trapped in information silos. The library posts to their website, the YMCA uses Google Calendar, the theater uses Eventbrite, Meetup groups have their own pages. Anyone wanting to know "what's happening this weekend?" must check a dozen different sites.

Existing local aggregators typically expect event producers to "submit" events via a web form. This means producers must submit to several aggregators to reach their audience—tedious and error-prone. Worse, if event details change, producers must update each aggregator separately.

This project takes a different approach: **event producers are the authoritative sources for their own events**. They publish once to their own calendar, and individuals and aggregators pull from those sources. When details change, the change propagates automatically. This is how RSS transformed blogging, and iCalendar can do the same for events.

The gold standard is **iCalendar (ICS) feeds**—a format that machines can read, merge, and republish. If you're an event producer and your platform can publish a ICS feed, that's great. But ICS isn't the only way. The real requirement is to **embrace the open web**. A clean HTML page with well-structured event data works. What doesn't work: events locked in Facebook or behind login walls.

## The Curator Role

A **curator** builds and maintains the calendar for their community. You don't create events — you discover and connect existing event sources. The goal is a comprehensive, low-maintenance calendar that updates automatically as source organizations post their events.

### How you work is up to you

**Hands-on curator.** You enjoy the detective work — searching, testing feeds, wiring up the pipeline. Everything you need is in this guide, from discovery techniques to pipeline setup.

**Agent-assisted curator.** You work with an AI agent that handles the searching, testing, and wiring while you steer. The topical searches especially benefit from this — an agent can fan out across dozens of topics in parallel. Point your agent at [AGENTS.md](../AGENTS.md) and this guide.

**Delegating curator.** You know your community but prefer to hand off the technical work. You describe what matters — "we need more outdoor recreation sources" or "the Durham food scene is underrepresented" — and a hands-on or agent-assisted collaborator executes.

All three approaches produce the same thing: a well-maintained `SOURCES_CHECKLIST.md` and a pipeline that pulls from discovered feeds.

## What Makes a Good Source

**Best**: Native ICS feeds (Meetup groups, Tockify calendars, Google Calendar public links). These "just work" and stay current automatically. 

**Fallback 1 — Platform APIs**: Some platforms (Eventbrite, LibCal) offer APIs or structured data that scrapers can convert to ICS. The project includes scrapers for common platforms.

**Fallback 2 — Custom scrapers**: For sites with no feed or API, an LLM can help write a scraper. Describe the calendar page structure to Claude or ChatGPT, and it can generate BeautifulSoup or Puppeteer code to extract events.

**Fallback 3 — Event posters**: For events promoted only via images (posters, flyers), an LLM can extract event details from a photo. Point your phone at a poster, and the system can parse it into calendar data.

https://github.com/judell/community-calendar/raw/main/video/event-poster-capture.mp4

**Skip**: Facebook events (API restrictions), Cloudflare-protected sites.

When you find a source that needs a scraper, document it in the city's `SOURCES_CHECKLIST.md` with the URL and any notes about the page structure. A developer (or you, with LLM assistance) can then build the scraper.

---

## Playbook for Launching a New Citywide Calendar

### Phase 1: Platform searches (grab the easy wins)
Search for feeds by platform — Tockify, Meetup ICS, WordPress `?ical=1`, Localist, Google Calendar embeds. These reliably turn up dozens of ready-to-use ICS feeds in a single pass.

### Phase 2: Topical searches (find venues by category)
Search by topic to find venues and organizations, then probe their websites for feeds (try `?ical=1`, check for Squarespace `?format=json`, look for Google Calendar embeds). This is where you find the Jazz Bistros and Grossman's Taverns that don't show up in platform searches.

This is a conversation with your agent. The topics below are a starting point — add, remove, or adjust based on what makes your city distinctive. A beach town needs "surfing, sailing, tide pools." A college town needs "alumni, Greek life." You know your community best.

**Topics to search:**

| Category | Topics |
|----------|--------|
| Arts & Culture | music, theater, comedy, dance, film, art, crafts, literature |
| Ideas & Learning | poetry, book clubs, writing, history, genealogy, philosophy, talks |
| Outdoors & Nature | hiking, walking, running, cycling, gardening, birding, conservation |
| Health & Well-Being | yoga, fitness, mindfulness, mental health, wellness |
| Food & Drink | beer, wine, food, cooking, farmers markets |
| Play & Games | trivia, board games, puzzles, casual gaming |
| Animals & Environment | pets, wildlife, animal care, sustainability |
| Community & Life Stages | kids, families, seniors, caregivers, newcomers |
| Identity & Belonging | faith, LGBTQ+, cultural heritage |
| Civic & Social Good | volunteering, mutual aid, civic engagement |
| Technology & Work | tech, digital skills, careers |

### Phase 3: Custom scrapers (last resort for high-value sources)
Only after exhausting phases 1 and 2, build scrapers for important sources that have no feeds. Prioritize by event volume and community relevance.

### Throughout all phases:

1. **Search** for feeds (see [Procedures](procedures.md))
2. **Test** each discovered feed to verify it works and has events
3. **Document** findings in `cities/{city}/SOURCES_CHECKLIST.md`
4. **Add** working feeds to the pipeline
5. **Configure geo-filtering** if feeds include events outside your area
6. **Register the city** in the app

Steps 1-3 are the core discovery loop. Steps 4-6 are pipeline setup. All the details are in the [Procedures](procedures.md) doc.

---

## Duplicates

Don't worry about the same event appearing in multiple sources. The calendar deduplicates events that are identical, but when the same event comes from different sources it preserves the event and lists all the sources. For example, a concert might show sources: `Bohemian, GoLocal, Eventbrite`. This is a feature, not a bug — it reveals provenance and syndication patterns, showing how events flow through the local information ecosystem.

---

## Long-Running Events

Some sources (particularly CitySpark-powered calendars like North Bay Bohemian and Press Democrat) return multi-day events as separate daily occurrences. For example, an art exhibition like "The Unknown Wayne Thiebaud: Passionate Printmaker" at Sebastopol Center for the Arts might run for two months — and would appear as 60+ separate events, one for each day the gallery is open.

The calendar automatically collapses these long-running events to **show once per week**. This keeps exhibitions, recurring library programs, and ongoing classes visible without cluttering every single day.

**How it works:**
- Events with the same title + location + time-of-day that appear 5+ times are identified as "long-running"
- Only the first occurrence in each calendar week is displayed
- The event remains visible throughout its run, just not every day

This reduces event count significantly (typically 10-15% fewer displayed events) while maintaining weekly visibility of ongoing attractions. Curators don't need to do anything — this happens automatically in the display layer.

---

## See Also

- [Procedures](procedures.md) — Step-by-step how-tos for searching, testing, adding feeds, geo-filtering, and city registration
- [Discovery Lessons](discovery-lessons.md) — Real-world lessons and gotchas from source discovery
- [AGENTS.md](../AGENTS.md) — Technical reference for scrapers and automation
