# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the community calendar project.

## Format

Each ADR follows this structure:

```markdown
# NNNN. Title

Date: YYYY-MM-DD

## Status

Accepted | Deprecated | Superseded by [NNNN](NNNN-title.md)

## Context

What is the issue we're facing? What factors affect this decision?

## Decision

What did we decide to do?

## Consequences

What becomes easier or harder as a result?

## Alternatives Considered

What other options did we evaluate? Why didn't we choose them?
```

## Naming Convention

Files are named: `NNNN-title.md`

Example: `0001-use-supabase-for-storage.md`

## Creating a New ADR

Start numbering at `0001` and increment sequentially.

## Example ADRs to Consider Recording

- Why Supabase was chosen for the database
- Why XMLUI was chosen for the UI framework
- Why the `feeds` table is the source of truth (not `feeds.txt`)
- Why scrapers inherit from `BaseScraper`
- Why `X-SOURCE` is injected at download time (not at scraper time)
- Why geo-filtering is optional per city
