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

---

## The Curator Model: How Communities Can Own Their Event Data

Public events are trapped in information silos. The library posts to their website, the YMCA uses Google Calendar, the theater uses Eventbrite, Meetup groups have their own pages. Anyone wanting to know "what's happening this weekend?" must check a dozen different sites.

Existing aggregators expect event producers to "submit" events via web forms. Tedious, error-prone, and changes don't propagate.

This project takes a different approach: **event producers are the authoritative sources for their own events**. They publish once to their own calendar, and the community calendar pulls from those sources. When details change, the change propagates automatically.

The key insight: this requires a new role - the **curator**. Curators don't create events. They discover and connect existing event sources. The goal is a comprehensive, low-maintenance calendar that updates automatically.

Three curator modes:
- **Hands-on**: You enjoy the detective work — searching, testing feeds, wiring up the pipeline
- **Agent-assisted**: You work with an AI agent that handles searching and wiring while you steer
- **Delegating**: You know your community but hand off the technical work ("we need more outdoor recreation sources")

All three produce the same thing: a well-maintained source list and a pipeline that pulls from discovered feeds.

The curator monitors a health dashboard showing which feeds work, which have gone to zero, which categories are underrepresented. When you see a gap, that's your cue to investigate. The dashboard surfaces problems; the curator's judgment about what matters drives fixes.

---

## When a Source Goes Dark, Follow the Events

Sources break. A site adds Cloudflare bot protection, a platform redesigns its API, a domain expires. The health report shows the symptom: a feed drops to 0 events.

**Case study: Volunteer Toronto**

The health report showed `volunteer_toronto` at 0 events. The scraper had targeted `volunteertoronto.ca` directly, but the entire site was now behind Cloudflare, returning 403 on every request.

A curator who cares about volunteerism won't stop there. The investigation:

1. **Search for the same events elsewhere.** "Volunteer toronto events" turned up listings on Toronto Public Library, Eventbrite, Meetup.

2. **Check Eventbrite.** Volunteer Toronto has an organizer page — but 0 future events. Dead end.

3. **Check BiblioCommons.** TPL's events API showed Volunteer Toronto events tagged with a program ID. Same workshops, settlement services, English conversation circles — 182 events with full details.

4. **Reuse existing infrastructure.** We already had a BiblioCommons scraper for TPL. The new scraper is 10 lines — just a subclass with a program ID filter. It replaced 436 lines of Cloudflare-blocked code and immediately produced 82 events.

**The lesson:** Events often exist in multiple places. When the original source becomes inaccessible, search for who else hosts, aggregates, or republishes the same events. Check the organization's presence on Eventbrite, Meetup, Facebook. Check library systems that host their programs. Check municipal calendars listing partner organizations.

Don't give up on a category just because one source is inaccessible. The events are still happening — they're just published somewhere else.

---

## LLM-Assisted Deduplication: What Works and What Doesn't

When you aggregate from 50+ sources, duplicates are inevitable. The same event appears on the venue's site, the local newspaper's calendar, Eventbrite, and two Meetup groups.

### The easy cases

Same-source duplicates (pagination bugs, overlapping date ranges) are trivial — dedupe by UID.

Cross-source duplicates with identical titles are easy — group by (date, normalized_title), keep the primary source version.

### The hard cases

Aggregators mangle titles:
- Venue: "Hands on a Hardbody"
- Aggregator: "Hands on a Hardbody at Spreckels Performing Arts Center"

Solution: prefix matching. If one title is a prefix of another on the same date, and at least one comes from a known aggregator, merge them. Guards prevent false positives: minimum 12 characters, ratio cap (shorter ≤ 75% of longer), aggregator requirement.

### Where LLMs help

For genuinely different titles describing the same event, we experimented with Claude:

```
Events on 2026-02-22. Group any that are the SAME event:
1. Live Jazz Night (Blue Note, 8pm)
2. Jazz at Blue Note featuring Sarah Chen Quartet (Blue Note Jazz Club, 8:00 PM)
3. Comedy Open Mic (Laugh Factory, 9pm)
```

Results from a real run:
- API calls: 847 (one per date with 2+ events)
- Tokens: 412K input, 89K output
- Fuzzy matches found: 23 additional duplicates
- Cost: ~$0.50

### What we learned

1. **Haiku is sufficient** — Claude 3.5 Haiku handles this well; no need for Sonnet
2. **Batch by date** — grouping events by date keeps context windows small
3. **Diminishing returns** — exact title matching catches 95%+ of duplicates; LLM catches the long tail
4. **Location matters** — events at different locations should never merge, even with similar titles

The token-set similarity algorithm (threshold 0.85) catches most fuzzy matches without API calls. LLM dedup is a refinement, not a replacement.

---

## Phase 4: When Aggregators Are Infrastructure vs. Intermediaries (2026-02-23)

Phase 4 of source discovery analyzes which venues appear *only* via aggregators, then checks if they have their own feeds we could use directly. The results revealed two distinct patterns:

### Santa Rosa: Aggregator as Intermediary

The North Bay Bohemian and Press Democrat scrape or receive submissions from venues that maintain their own calendar infrastructure. Phase 4 found Uptown Theatre Napa with a perfectly good WordPress Tribe feed (30 events) that we were only getting through the newspaper aggregators. Adding it directly means fresher data and independence from the aggregator.

We also discovered a dead feed — Sonoma Community Center was in our feeds.txt but returning Cloudflare 403s. The 106 events we saw via aggregators weren't coming from our "direct" feed at all.

### Toronto: Aggregator as Infrastructure

Toronto's music venue scene uses Tockify (torevent) differently. When I checked the top venues appearing only via the aggregator:

- Comedy Bar (277 events): ASP.NET custom site, no calendar
- Tranzac (146 events): Nuxt/Netlify static site  
- Horseshoe Tavern (49 events): Cloudflare-protected, no ICS
- The Garrison, Mod Club, Cameron House: Simple websites with ticket links

These venues don't have their own calendar systems. They submit events directly to Tockify as their primary publishing platform. The aggregator isn't an intermediary we can bypass — it IS the infrastructure.

### Four Aggregator Patterns

Analyzing all six cities revealed four distinct patterns:

**1. Media Aggregator (Santa Rosa, Petaluma)**
- Aggregators: North Bay Bohemian, Press Democrat (newspapers)
- Pattern: Newspapers scrape/receive submissions from venues with their own calendars
- Phase 4 yield: HIGH — found Uptown Theatre Napa, identified dead Sonoma CC feed

**2. Platform Infrastructure (Toronto)**
- Aggregator: Toronto Events (Tockify)
- Pattern: Venues submit to Tockify as their primary publishing platform
- Phase 4 yield: Lower for venues using the platform as infrastructure

**3. Government Aggregator (Raleigh-Durham)**
- Aggregator: NC Cultural Resources (873 events)
- Pattern: State cultural agency aggregates state parks, museums, historic sites
- Phase 4 yield: LOW — these are government-run sites that report to the state system rather than maintaining their own feeds

**4. Direct Sources (Bloomington, Davis)**
- No major aggregator — calendar built from direct institutional feeds
- Sources: Universities, libraries, arts councils
- Phase 4 yield: N/A — already operating at upstream authority level

### The Long Tail Opportunity

The project's philosophy is long-tail inclusive. Smaller organizations — community centers, churches, arts collectives, cultural associations — often maintain their own WordPress or Google Calendar infrastructure even when big venues outsource to aggregators.

The Tockify aggregator captures Toronto's music scene well, but probably misses the Korean seniors' association, the neighborhood chess club, the community garden workdays. Phase 4 should probe venues across the volume spectrum. The long tail is where independent feeds are most likely to exist, regardless of what pattern the high-volume venues follow.

### Tactical Guidance

Before running Phase 4 on a new city:

1. **Identify the aggregator's role.** Media scraping venues? Platform venues publish to? Government system? Or no aggregator at all?

2. **Check everything, but expect different yields.** Media aggregator cities yield upstream feeds. Platform/government aggregator cities yield more on the long tail. Direct-source cities don't need Phase 4.

3. **Dead feed detection:** If a venue appears only via aggregators but is already in your feeds.txt, that feed is probably broken.
