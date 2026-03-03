# Engagement Strategy: Bloomington and Toronto Visits (April 2026)

## Purpose

I'll be spending extended time in Bloomington and Toronto in March, with friends who are well connected in civic, educational, and tech spaces. This document helps them help me make the most of that time — identifying who to meet, what to pitch, and what each type of ally gets out of participating.

The goal is to ally with aggregators, organizational stakeholders, and long-tail event producers. The pattern analysis from the curator guide (direct sources vs. platform infrastructure vs. media aggregator) shapes the approach differently for each city.

## What This Project Is (and Isn't)

This project is **open-source technology for community event aggregation**, not a destination site. We're building the plumbing — tools and techniques for assembling a comprehensive, machine-readable feed of community events from upstream sources, paired with a high-quality mobile-friendly app that serves civilians and curators.

 We don't aim to monetize this. We care about solving the problem: public events are trapped in silos, and nobody should have to check a dozen sites to find out what's happening this weekend.

The goal for any city is to have **strong local aggregators that use this technology**. A small city might join the home repo directly as a new city folder. A bigger city would fork it and run their own instance. Either way, we want to help incumbent aggregators survive and flourish by freeing them from the tedious work of collecting event data. And where no aggregator exists, we want to provide an opportunity for new entrants.

## The Pitches

There are three audiences, each with a different pitch.

### To aggregators (newspapers, regional platforms, event sites)

**The frank version:** "We're building an open technology layer. We've solved the hard problem of assembling feeds from dozens of upstream sources — Meetup, Google Calendar, WordPress, Tockify, custom scrapers for sites that don't have feeds. Yes, open feeds mean anyone could build an aggregator on top of this data — including your competitors. That's the risk. Here's the reward: you no longer have to do the expensive, error-prone work of collecting event data. Submission forms, manual entry, chasing venues for updates — that all goes away. The plumbing is handled. You can focus entirely on what actually differentiates you: editorial voice, curation, local context, recommendations, audience trust."

**The deeper point:** "When the Bohemian links to an event, that link carries trust and context that a raw feed listing never will. Your value was never in hoarding the data — it's in what you add on top. An open data layer makes your value-add more visible, not less. And the technology actively drives traffic back to you: when we got an event via your calendar, we link to your page for that event, not just the venue's."

**The ask:** Two things. First, we'd love a relationship so we hear about platform changes before they break the pipeline. Second, consider pulling from open upstream feeds as inputs — it's more reliable than submission forms, and you get automatic updates when event details change.

### To event producers (venues, institutions, organizations)

**The simple version:** "Publish your events as an open feed — an ICS calendar, a Google Calendar, whatever your platform supports. You publish once, and it propagates everywhere: to us, to local aggregators, to anyone who wants to include your events. No more submitting to five different sites. No more updating each one when a date changes."

**The ask depends on the city:**

- **Where strong aggregators exist:** "Publish an open feed, and lobby your local aggregator to pull from it. Tell the Bohemian or NOW Magazine: 'here's my calendar feed, just subscribe to it instead of making me fill out your form every week.'" We lobby the aggregators from our side; producers lobby from theirs.

- **Where no aggregator exists:** "Your city doesn't have a good local events aggregator. Someone should become one — maybe you, maybe a local newspaper, maybe a civic org, maybe a neighborhood association. This technology gives you the foundation: fork the repo, point it at your city's sources, and you have a comprehensive feed to build on top of. Run your own branded front-end, add editorial picks, highlight what matters to your community. The data layer is free and open."

### To potential curators

"A curator discovers and connects event sources — you don't create events, you wire up the plumbing. You can go deep on the technical side, or you can just steer while an AI agent does the searching and wiring. Either way, you know your community better than any algorithm. The health dashboard shows you what's working and what's broken, and your judgment drives what gets fixed."

---

## Bloomington

### Pattern: Direct Sources (no major aggregator)

Bloomington's calendar is already built from 27 direct institutional feeds — IU LiveWhale, city Google Calendars, BloomingtonOnline, Meetup groups, custom scrapers. There's no aggregator intermediary to bypass. The opportunity here is **filling gaps and building relationships for ongoing curation**.

### Current Strengths

- University events well covered (IU Jacobs, Auditorium, Eskenazi Museum via LiveWhale)
- City/civic solid (Parks & Rec, B-Square, Farmers Market)
- Music venues covered (Bluebird, Bishop, Comedy Attic, Buskirk-Chumley)
- Community events via BloomingtonOnline's Google Calendars

### Known Gaps

These are documented in SOURCES_CHECKLIST.md as blocked, pending, or dead ends:

| Gap | Why it's stuck | What a local contact could unlock |
|-----|---------------|-----------------------------------|
| WonderLab Museum | Cloudflare blocks scraping | A conversation with their web person; maybe they'll expose an ICS feed or whitelist us |
| WFHB Community Radio | mod_security blocks scraping | Same — a human relationship may solve what code can't |
| Monroe County schools (MCCSC) | Migrated to ParentSquare, old feed is 404 | A PTA contact who knows the new platform |
| Visit Bloomington | Simpleview CMS, no API | Tourism board contact; or confirmation it's not worth pursuing |
| FAR Center for Contemporary Arts | Craft CMS, no feed | Intro to their web/marketing person |
| Neighborhood associations | Sites appear inactive | Are these orgs actually active? Locals would know |
| Herald-Times / Indiana Daily Student | Derivative aggregators, haven't investigated deeply | Are they worth approaching as partners? |

### Who to Meet

**Tier 1 — Organizational stakeholders (high leverage)**

- **IU Events office** — They run the LiveWhale system. We already pull 3 group feeds. They could point us to more IU group IDs, or even provide an all-events feed with better metadata.
- **Monroe County Public Library staff** — We scrape their LibCal already, but a relationship means we hear about platform changes before they break things.
- **City of Bloomington IT/communications** — We pull from their Google Calendars. A contact means stability and possibly more city feeds.
- **BloomingtonOnline maintainer(s)** — We use their Google Calendar feeds. Who runs this? Are there more calendars we're not seeing?

**Tier 2 — Long-tail producers (fill gaps)**

- **WonderLab Museum** — High-value family/science source, blocked by Cloudflare. A conversation could solve this.
- **WFHB Community Radio** — Their community calendar is one of the most comprehensive in town, but mod_security blocks us.
- **B-Square Bulletin maintainer** — We use 4 of their Google Calendars. Who curates these? What's their broader network?
- **Lotus Festival organizers** — We have their feed; they're connected to the world music / arts scene.

**Tier 3 — Community connectors (discover unknowns)**

- **Bloomington PRIDE / LGBTQ+ community** — Squarespace site with no feed. Events currently only visible via IU's all-events feed.
- **Faith communities** — UU Church, Friends Meeting. Are there interfaith councils that coordinate events?
- **Arts collectives** — Gallery Walk Bloomington, Juniper Art Gallery. Who's the informal hub of the arts scene?
- **Running / cycling / outdoor groups** — BARA (Wix, no feed), Bicycle Club (already have). Who else?

### Conversation Goals

1. **Get introductions** to web/marketing contacts at WonderLab, WFHB, and FAR Center — the three highest-value blocked sources.
2. **Learn who maintains** BloomingtonOnline and B-Square Bulletin — these community aggregators are already key sources and the people behind them are natural allies.
3. **Identify a potential local curator** — someone who knows the community well enough to notice gaps and cares enough to flag them. The delegating-curator model is designed for exactly this.
4. **Discover unknown sources** — locals know about events that never surface in web searches. "Oh, the Unitarian church has a huge community events board" or "the co-op posts events on their Google Calendar."

---

## Toronto

### Pattern: Platform Infrastructure (Tockify as primary publishing mechanism)

Toronto's biggest single source is `torevent` on Tockify (~2,900 events). Music venues like Comedy Bar, Tranzac, and Horseshoe Tavern don't maintain their own calendars — they submit to Tockify as their primary platform. This means Phase 4 upstream-authority work has lower yield for the big venues, but the long tail of community organizations is rich and largely untapped.

We already have 83 sources and ~9,200+ events. The opportunity here is **alliance-building with aggregators, filling the long tail, and unlocking scraper targets**.

### Current Strengths

- Massive Meetup coverage (49 groups across every category)
- Strong institutional feeds (York U, UofT, TPL, City of Toronto CKAN)
- Good arts/culture (Gardiner Museum, Textile Museum, Factory Theatre, etc.)
- Civic coverage (CKAN meetings + festivals datasets)

### Known Gaps and Opportunities

| Gap | Status | What a local contact could unlock |
|-----|--------|-----------------------------------|
| BlogTO | Needs scraper, highest-volume source we don't have | Intro to their tech team; or a developer who's scraped them before |
| AGO (Art Gallery of Ontario) | Cloudflare 403 | Same as WonderLab — a human conversation |
| ROM (Royal Ontario Museum) | 404 on events page | Contact in their marketing/web team |
| TIFF | No feed found | Someone who knows their tech stack |
| Harbourfront Centre | RSS exists but empty; WP Engine site | Likely has a JSON API; a web contact could confirm |
| Massey Hall / Roy Thomson Hall | 404 | Post-renovation, presumably a new site coming |
| The 519 (LGBTQ+ centre) | WordPress but no Tribe plugin | Could they install it? Or expose a feed? |
| Toronto Bicycling Network | RSS feed with 50+ events, needs RSS-to-ICS conversion | Low-tech conversion, but a relationship with TBN makes it sustainable |
| NOW Magazine | Already pulling ~30 events | They're a key aggregator — a relationship means we hear about changes |
| torevent (Tockify) | ~2,900 events, our biggest source | Who runs this? A relationship is essential for stability |
| Food & drink scene | Almost entirely on Eventbrite (no public feeds) | Farmers' markets, cooking schools, food festivals — locals know which ones have their own sites |
| Comedy / open mic | Mostly Facebook/Eventbrite | Bad-Dog Theatre, Second City, Comedy Bar — none have feeds |

### Who to Meet

**Tier 1 — Aggregator relationships (strategic)**

- **torevent operator** — This is our single most important Toronto relationship. ~2,900 events. Who runs this Tockify calendar? How do venues submit? Are they open to collaboration?
- **NOW Magazine events team** — Traditional alt-weekly aggregator. We pull their WordPress Tribe feed. A relationship means stability and mutual benefit (we send traffic back via source attribution).
- **City of Toronto Open Data team** — We use their CKAN datasets for meetings and festivals. They may know of other civic event datasets.

**Tier 2 — Institutional stakeholders (unlock big sources)**

- **UofT events office** — We scrape their aggregate page + departments. A contact could point us to a better feed or more departments.
- **Toronto Public Library** — We already scrape BiblioCommons for kids/family events. TPL is huge; there may be more program categories worth adding.
- **York University events** — We pull their 6,500-event MEC feed. A contact ensures stability.

**Tier 3 — Long-tail producers and scraper targets**

- **Harbourfront Centre** — Major waterfront venue, WP Engine site. Someone who knows their stack could tell us if there's a JSON endpoint.
- **AGO, ROM, TIFF** — The big three Toronto cultural institutions, all currently blocked/missing. Even one feed from these would be high-value.
- **The 519 Community Centre** — LGBTQ+ hub. WordPress but no events plugin. Could they add one?
- **BlogTO events team** — Highest-volume source we're missing. Their tech team could advise on scraping or (long shot) expose a feed.
- **YOHOMO** — LGBTQ+ events aggregator. Scraper opportunity.
- **Community centres** (Scadding Court already in, but there are dozens more) — Who coordinates Toronto's community centre network?
- **BIAs (Business Improvement Areas)** — Bloor West Village BIA is already in. Toronto has ~80 BIAs. Which ones have event calendars?

**Tier 4 — Community connectors**

- **Toronto tech community** — We have TechTO, TorontoJS, Python Toronto, etc. via Meetup. But the tech community also knows who's doing interesting civic tech. Allies here may become contributors.
- **Civic tech community** — Civic Tech Toronto is a natural ally. They care about open data and community infrastructure.
- **Arts council / arts community** — Toronto Arts Council has a WordPress site with events. Who in the arts scene knows where the gaps are?

### Conversation Goals

1. **Find the torevent operator** — this is job #1. Our biggest source and we don't know who runs it.
2. **Build aggregator alliances** — NOW Magazine, torevent, City of Toronto. Frame it as symbiotic: we drive traffic back to them, we don't compete.
3. **Unlock the big three** (AGO, ROM, TIFF) — even partial progress on any of these is a win. A single contact at each institution could change the picture.
4. **Identify a local curator** — Toronto is big enough to benefit from someone who monitors the health dashboard and knows which neighborhoods or categories are underrepresented.
5. **Map the long tail** — community centres, BIAs, cultural associations. Locals know which ones are active and tech-savvy enough to have feeds.
6. **Civic tech connection** — Civic Tech Toronto could be both a source of tech volunteers and a channel for evangelizing the calendar-as-infrastructure idea.

---

## What Friends Can Do Before I Arrive

For both cities, the most valuable thing a friend can do is **make introductions**. Specifically:

1. **Forward the pitch** (adapted to the specific person) to contacts at the organizations listed above.
2. **Set up coffee/lunch meetings** with the Tier 1 contacts — these are the strategic relationships.
3. **Ask around**: "Who runs [X]?" — especially for BloomingtonOnline, B-Square Bulletin, and torevent, where we don't know the operators.
4. **Identify potential curators** — people who are civic-minded, know the community, and might enjoy the curator role (even in delegating mode).

## What I'll Bring to Each Meeting

- A live demo of the city's calendar showing their events already included (or showing the gap where theirs should be)
- The health dashboard showing source status
- A clear ask tailored to the contact (feed access, introduction to their web person, feedback on coverage gaps)
- The "you don't have to change anything" message — we pull from what you already publish
