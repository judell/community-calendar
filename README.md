# Community Calendar

Public events are trapped in information silos. The library posts to their website, the YMCA uses Google Calendar, the theater uses Eventbrite, Meetup groups have their own pages. Anyone wanting to know "what's happening this weekend?" must check a dozen different sites.

Existing local aggregators typically expect event producers to "submit" events via a web form. This means producers must submit to several aggregators to reach their audience — tedious and error-prone. Worse, if event details change, producers must update each aggregator separately.

This project takes a different approach: **event producers are the authoritative sources for their own events**. They publish once to their own calendar, and individuals and aggregators pull from those sources. When details change, the change propagates automatically. This is how RSS feeds work for blogs,iCalendar can do the same for events.

The gold standard is **iCalendar (ICS) feeds** — a format that machines can read, merge, and republish. If you're an event producer and your platform can publish an ICS feed, that's great. But ICS isn't the only way. The real requirement is to **embrace the open web**. A clean HTML page with well-structured event data works. What doesn't work: events locked in Facebook or behind login walls.

## Live App

**XMLUI App**: https://judell.github.io/community-calendar/

**Feed Health Report**: https://judell.github.io/community-calendar/report.html

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Scrapers      │────▶│   ICS Files     │────▶│  combined.ics   │
│ (various sites) │     │ (per source)    │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   XMLUI App     │◀────│    Supabase     │◀────│  events.json    │
│  (GitHub Pages) │     │   (database)    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

Scrapers and ICS feed downloads run daily in GitHub Actions. Individual ICS files are combined into a single feed per city, converted to JSON, and posted to Supabase. The XMLUI frontend queries Supabase and renders events. See [docs/pipeline.md](docs/pipeline.md) for the full pipeline details.

## The Curator Role

A **curator** builds and maintains the calendar for their community. You don't create events — you discover and connect existing event sources: find organizations publishing calendars, test that feeds work, add them to the aggregator, and filter out noise. The goal is a comprehensive, low-maintenance calendar that updates automatically. See [docs/curator-guide.md](docs/curator-guide.md) for the full playbook.

## Features

- **Event pipeline** — ICS feeds, scrapers, deduplication, source attribution. [docs/pipeline.md](docs/pipeline.md)
- **Event classification** — AI-powered categorization with curator overrides. [docs/pipeline.md](docs/pipeline.md#event-classification)
- **Search and snippets** — Client-side filtering with scored description snippets. [docs/search-and-performance.md](docs/search-and-performance.md)
- **Personal picks** — Save events, subscribe via personal ICS feed. [docs/picks.md](docs/picks.md)
- **Event capture** — Photograph a poster or speak event details. [docs/audio-capture.md](docs/audio-capture.md)
- **Recurrence enrichment** — Curators attach recurrence rules visible to all users. [docs/recurrence.md](docs/recurrence.md)

## Add an Event Source

Know of a local calendar that should be included? [Open an issue](https://github.com/judell/community-calendar/issues/new?template=add-feed.md) with the feed URL and a link to the events page. If you're comfortable with pull requests, you can also add the feed directly to `cities/{city}/feeds.txt` — see the [issue template](https://github.com/judell/community-calendar/issues/new?template=add-feed.md) for the format.

## Development

- **App architecture**: [docs/app-architecture.md](docs/app-architecture.md) — XMLUI components, local dev setup, resources
- **Tests**: Browser-based unit tests in `test.html`; regression tests via [trace-tools](https://github.com/xmlui-org/trace-tools). [docs/regression-testing.md](docs/regression-testing.md)
- **Adding a city**: [docs/curator-guide.md](docs/curator-guide.md) (discovery) and [AGENTS.md](AGENTS.md) (technical steps)
- **Adding sources**: [docs/procedures.md](docs/procedures.md) — feed discovery, testing, geo-filtering
- **Supabase**: [supabase/README.md](supabase/README.md) — schema, edge functions, auth, RLS
- **Scrapers**: [scrapers/README.md](scrapers/README.md) — scraper library and per-site docs
- **Timezones**: [docs/timezone.md](docs/timezone.md) — ICS timezone handling conventions
- **Deduplication**: [docs/deduplication.md](docs/deduplication.md) — dedup implementation details
- **AI agents**: [AGENTS.md](AGENTS.md) — operating guide for AI agents working on this codebase

## Repo Structure

```
.github/workflows/      # GitHub Actions automation
cities/                 # Per-city data (feeds.txt, SOURCES_CHECKLIST.md)
cli/                    # CLI tools
docs/                   # Detailed documentation
scrapers/               # Event scrapers for sites without ICS feeds
scripts/                # Build and utility scripts (combine_ics, ics_to_json, classify, etc.)
supabase/               # DDL docs, edge functions (load-events, my-picks, capture-event)
xmlui/                  # XMLUI app (Main.xmlui, Globals.xs, components/, helpers.js)
```
