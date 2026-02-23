# Community Calendar Curator Guide

## Table of Contents

- [Overview](#overview)
- [The Curator Role](#the-curator-role)
  - [How you work is up to you](#how-you-work-is-up-to-you)
  - [Monitor the dashboard, act on what matters to you](#monitor-the-dashboard-act-on-what-matters-to-you)
- [What Makes a Good Source](#what-makes-a-good-source)
- [About Aggregators](#about-aggregators)
- [Playbook for Launching a New Citywide Calendar](#playbook-for-launching-a-new-citywide-calendar)
  - [Phase 1: Platform searches (grab the easy wins)](#phase-1-platform-searches-grab-the-easy-wins)
  - [Phase 2: Topical searches (find venues by category)](#phase-2-topical-searches-find-venues-by-category)
  - [Phase 3: Custom scrapers (last resort for high-value sources)](#phase-3-custom-scrapers-last-resort-for-high-value-sources)
  - [Phase 4: Upstream authority (find direct feeds for aggregated venues)](#phase-4-upstream-authority-find-direct-feeds-for-aggregated-venues)
  - [Throughout all phases](#throughout-all-phases)
- [Duplicates and Event Ordering](#duplicates-and-event-ordering)
- [Long-Running Events](#long-running-events)
- [Working with an AI Agent](#working-with-an-ai-agent)
  - [Getting started with a cloud workspace](#getting-started-with-a-cloud-workspace)
  - [What about Git and the command line?](#what-about-git-and-the-command-line)
  - [What if something goes wrong?](#what-if-something-goes-wrong)
- [See Also](#see-also)

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

### Monitor the dashboard, act on what matters to you

The [health report](https://judell.github.io/community-calendar/report.html) is a curator's primary ongoing tool. It shows which feeds are working, which have gone to zero, and how URL quality is trending across sources. When you see a gap — a feed dropping to 0 events, a category you care about underrepresented — that's your cue to investigate.

**Example:** The health report showed `volunteer_toronto` at 0 events. A curator who cares about volunteerism noticed the gap, asked an agent to investigate, and discovered that Volunteer Toronto's events had migrated to Toronto Public Library's BiblioCommons platform. Ten lines of code replaced a broken 436-line scraper and restored 82 events. The dashboard surfaced the problem; the curator's judgment about what matters drove the fix. See [When a Source Goes Dark](discovery-lessons.md#when-a-source-goes-dark-follow-the-events) for the full story.

## What Makes a Good Source

**Best**: Native ICS feeds (Meetup groups, Tockify calendars, Google Calendar public links). These "just work" and stay current automatically.

**Fallback 1 — Platform APIs**: Some platforms (Eventbrite, LibCal) offer APIs or structured data that scrapers can convert to ICS. The project includes scrapers for common platforms.

**Fallback 2 — Custom scrapers**: For sites with no feed or API, an LLM can help write a scraper. Describe the calendar page structure to Claude or ChatGPT, and it can generate BeautifulSoup or Puppeteer code to extract events.

**Fallback 3 — Event posters**: For events promoted only via images (posters, flyers), an LLM can extract event details from a photo. Point your phone at a poster, and the system can parse it into calendar data.

https://github.com/judell/community-calendar/raw/main/video/event-poster-capture.mp4

**Skip**: Facebook events (API restrictions), Cloudflare-protected sites.

When you find a source that needs a scraper, document it in the city's `SOURCES_CHECKLIST.md` with the URL and any notes about the page structure. A developer (or you, with LLM assistance) can then build the scraper.

## About Aggregators

While we source events from aggregators like the North Bay Bohemian and NOW Toronto, we don't aim to compete with them. Our goal is to expand their reach. Aggregators can value by providing context that a raw event listing doesn't.

When an event card shows a source like "North Bay Bohemian," the title links to the venue's own page (the authoritative source), but the Bohemian attribution links to the Bohemian's page for that event. A reader who clicks through to the Bohemian may discover related events, editorial coverage, or other context that the venue's page alone doesn't provide.

The principle: **we could disintermediate aggregators and only link directly to primary sources, but we choose not to**. If we got an event via an aggregator, we provide a link to their event page. This respects the work aggregators do and gives readers a richer experience.

**For developers adding a new aggregator to a city:**

1. Add the aggregator's friendly name to the `AGGREGATORS` set in `scripts/combine_ics.py` so deduplication correctly prefers primary sources over the aggregator's copies.

2. Ensure the fetcher emits per-event URLs whenever possible. If the aggregator's platform supports deep links to individual events (as CitySpark does for Bohemian), construct those URLs in the fetcher if possible. A ink to `bohemian.com/events-calendar/#/details/thee-sinseers/17654647/2026-02-22T19` is far more valuable than a link to `bohemian.com/events-calendar/`. If unavailable, add the aggregator's calendar page to `SOURCE_URLS` in `combine_ics.py` as a fallback. Even a link to the right calendar page is better than no link.

---

## Playbook for Launching a New Citywide Calendar

### Phase 1: Platform searches (grab the easy wins)
Search for feeds by platform — Tockify, Meetup ICS, WordPress `?ical=1` (a URL suffix you can append to WordPress event pages to get an ICS feed), Localist, Google Calendar embeds. These reliably turn up dozens of ready-to-use ICS feeds in a single pass.

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

### Phase 4: Upstream authority (find direct feeds for aggregated venues)
Once your calendar has aggregator sources (newspapers, regional platforms), analyze which venues appear *only* via aggregators. These are candidates for direct sourcing — getting events straight from the venue rather than through an intermediary.

**The process:**
1. Query your `events.json` to find locations that appear only in aggregator-sourced events
2. For each venue, check if they have their own ICS feed (`?ical=1`)
3. Add any working feeds — this improves data freshness and reduces aggregator dependency
4. Document venues with no feeds as potential scraper candidates

**Why this matters:** Aggregators may lag behind venues, miss events, or eventually go away. Direct feeds are more reliable and often have richer event details. This phase also reveals dead feeds in your pipeline — if a venue appears only via aggregators but is already in your feeds.txt, that feed may be broken.

**Four patterns emerge:**

*Media aggregator* (Santa Rosa, Petaluma): Newspapers and media sites scrape or receive submissions from venues that have their own calendar infrastructure. Phase 4 finds these upstream feeds — we found Uptown Theatre Napa with a working WordPress feed the aggregators were capturing.

*Platform infrastructure* (Toronto): Venues submit directly to a shared platform (like Tockify) as their primary publishing mechanism. They don't maintain their own calendars. Phase 4 is less productive here for venues using the platform, but the long tail — community centers, churches, small arts organizations — may still have independent feeds the aggregator doesn't capture.

*Government aggregator* (Raleigh-Durham): A state or regional agency aggregates events from government-run cultural sites (state parks, historic sites, museums). These venues typically report to the government system rather than maintaining their own feeds. Phase 4 yield is low — the aggregator IS the authoritative source for these sites.

*Direct sources* (Bloomington, Davis): No major aggregator. The calendar is already built from direct institutional feeds (universities, libraries, arts councils). Phase 4 doesn't apply — you're already at upstream authority level.

Check the aggregator's role before investing time. But always check the long tail regardless of pattern — smaller organizations often maintain their own infrastructure even when big venues don't.

### Throughout all phases:

1. **Search** for feeds (see [Procedures](procedures.md))
2. **Test** each discovered feed to verify it works and has events
3. **Document** findings in `cities/{city}/SOURCES_CHECKLIST.md`
4. **Add** working feeds to the pipeline
5. **Configure geo-filtering** if feeds include events outside your area
6. **Register the city** in the app

Steps 1-3 are the core discovery loop. Steps 4-6 are pipeline setup. All the details are in the [Procedures](procedures.md) doc.

---

## Duplicates and Event Ordering

**Deduplication is automatic.** When the same event appears in multiple sources, the system keeps the version from the most authoritative source (the venue or library itself) over aggregators (newspapers, regional event platforms). All contributing sources are still listed in the attribution — a concert might show `Bohemian, GoLocal, Eventbrite` — so you can see how events flow through the local information ecosystem.

**Event ordering is automatic.** Within each timeslot, events with similar titles are grouped together. "Baby Storytime", "Family Storytime", and "Preschool Storytime" at different library branches appear adjacent rather than scattered randomly.

**Aggregators** are the key configuration. Each city lists its aggregators — newspapers or platforms that republish events from many local sources. Primary sources (venues, libraries, etc.) need no special configuration.

Current cities and their known aggregators:

- **Santa Rosa:** North Bay Bohemian, Press Democrat, Creative Sonoma, GoLocal Cooperative
- **Toronto:** NOW Toronto, Toronto Events (Tockify)

To add your city or flag an aggregator, [open an issue](https://github.com/judell/community-calendar/issues/new?template=add-city-or-aggregator.md). Just name your city and any aggregators you know about — we'll help you figure out the rest.

For technical details on how deduplication and ordering work, see [Deduplication and Event Ordering](deduplication.md).

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

## Working with an AI Agent

If you're comfortable in a terminal and already have a GitHub workflow, you know the drill — clone the repo, point your agent at [AGENTS.md](../AGENTS.md), and go.

If that sentence meant nothing to you, don't worry. Here's the short version: an AI agent is a conversational partner that can also edit files, run commands, and push changes to this project. You tell it what you want ("find yoga and meditation event sources in Durham") and it does the searching, testing, and wiring. You steer; it drives.

### Getting started with a cloud workspace

You don't need to install anything on your computer. Several services give you a cloud workspace with an AI agent connected to this project:

- **[exe.dev](https://exe.dev)** — A cloud VM with a conversational agent. Connect it to this repository and start talking.
- **[GitHub Copilot coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)** — Works directly on github.com. You file an issue describing what you want, assign it to Copilot, and it opens a pull request with the changes. Requires a paid [GitHub Copilot](https://github.com/features/copilot) plan.
- **[Firebase Studio](https://firebase.studio/)** — Google's browser-based workspace with Gemini AI. Import from GitHub. Free tier available (currently in preview).
- **[OpenAI Codex](https://chatgpt.com/codex)** — Cloud sandbox preloaded with your repo, conversational interface, produces pull requests. Requires a ChatGPT Pro or Team plan.

The steps below use exe.dev as an example, but the pattern is the same across all of these: connect to the project, describe what you want in plain language, review the agent's work, approve or adjust.

1. **Get a GitHub account.** If you don't already have one, create one at [github.com](https://github.com). It's free. You can even make a fresh account just for this project — no prior history needed.

2. **Open the project in your cloud workspace.** Connect to this repository. This gives you an AI agent that already understands the project structure.

3. **Start talking.** Tell the agent what you want to do in plain language:
   - *"Find event sources for yoga and meditation in Durham, NC"*
   - *"Check if the Durham Public Library has an ICS feed"*
   - *"Add this Meetup group to the calendar: [URL]"*

   The agent searches, tests feeds, edits configuration files, and proposes changes. You review what it did and say yes or no.

4. **Your changes get saved.** When the agent makes changes you approve, they're committed to the project through Git — the version control system that tracks every change anyone makes. If something goes wrong, everything can be rolled back. Nothing is permanent until you're happy with it.

### What about Git and the command line?

You'll see the agent running commands in a terminal. You don't need to understand them. But if you're curious:

- **Git** is how this project tracks changes. Think of it like Google Docs revision history, but for code and configuration files.
- A **commit** is a saved snapshot — "added 5 new yoga sources for Durham."
- A **pull request** is a proposal — "here are my changes, please review them before they go live."
- The **command line** (or terminal) is where the agent types commands. You're watching over its shoulder, not typing yourself.

If you want to learn more about any of this as you go, just ask the agent. It can explain what it's doing and why. Some curators never look at the terminal; others get curious and start learning Git along the way. Both are fine.

### What if something goes wrong?

Nothing you or the agent does is irreversible. Git keeps a complete history of every change. If a feed turns out to be broken, or a scraper doesn't work, the change can be undone cleanly. The worst case is wasted time, never wasted data.

---

## See Also

- [Procedures](procedures.md) — Step-by-step how-tos for searching, testing, adding feeds, geo-filtering, and city registration
- [Discovery Lessons](discovery-lessons.md) — Real-world lessons and gotchas from source discovery
- [Deduplication and Event Ordering](deduplication.md) — Technical details on how duplicates are handled and events are ordered
- [AGENTS.md](../AGENTS.md) — Technical reference for scrapers and automation
