# Documentation Index

## Architecture & Pipeline
- [app-architecture.md](app-architecture.md) — XMLUI frontend, Supabase backend, component layout
- [pipeline.md](pipeline.md) — End-to-end event pipeline: feeds → ICS → dedup → JSON → Supabase
- [FUNCTIONS.md](FUNCTIONS.md) — Postgres functions vs Edge Functions
- [AUTH.md](AUTH.md) — Supabase Auth setup (GitHub OAuth, Google OAuth, magic link)
- [timezone.md](timezone.md) — ICS timezone conventions and pipeline handling

## Discovery & Curation
- [curator-guide.md](curator-guide.md) — Philosophy, source types, aggregators, deduplication, categories
- [procedures.md](procedures.md) — Step-by-step source discovery and pipeline setup
- [discovery-lessons.md](discovery-lessons.md) — Real-world lessons from source discovery across cities
- [source-links.md](source-links.md) — Source attribution link architecture

## Features
- [picks.md](picks.md) — Personal event picks and ICS feed
- [recurrence.md](recurrence.md) — Recurrence rules and enrichment
- [audio-capture.md](audio-capture.md) — Speech-to-event via Whisper + Claude
- [search-and-performance.md](search-and-performance.md) — Client-side search, snippet scoring, virtualization
- [deduplication.md](deduplication.md) — Five-level dedup pipeline

## Admin
- [admin-interface.md](admin-interface.md) — Admin UI features and roadmap
- [admin-dashboard-requirements.md](admin-dashboard-requirements.md) — Dashboard spec for curators

## Testing
- [regression-testing.md](regression-testing.md) — Trace-tools CI setup
- [search-pattern-tests.md](search-pattern-tests.md) — Search discovery test patterns

## Auto-generated
- [prodid.md](prodid.md) — ICS platform inventory (via `scripts/prodid.py`)
- [snippet-eval-prompt.md](snippet-eval-prompt.md) — LLM prompt for snippet quality evaluation

## Planning & Notes
- [engagement-strategy.md](engagement-strategy.md) — Bloomington and Toronto engagement plan
- [barrel-proof-investigation.md](barrel-proof-investigation.md) — Data quality investigation (blog material)
- [notes-for-blog-posts.md](notes-for-blog-posts.md) — Blog post ideas and findings
- [ui-puzzles.md](ui-puzzles.md) — Open UI design problems

## Superseded
- [audio-input.md](audio-input.md) — Original audio planning doc (see audio-capture.md)
