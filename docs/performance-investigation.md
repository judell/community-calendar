# Performance Investigation: Bloomington Calendar Startup

**Date:** 2026-04-08

## Problem

The Bloomington calendar loads ~5000 events on page load via a Supabase REST API call. The iframe embed is noticeably slow. We wanted to measure where time is spent and find quick wins.

## Method: xs-trace for startup timing

The [trace-tools](https://github.com/xmlui-org/trace-tools/) kit includes `xs-trace.js` which provides timing wrappers (`window.xsTrace`, `window.xsTraceWith`, `window.xsTraceEvent`). These emit `app:trace` entries into `window._xsLogs`.

**Problem:** `_xsLogs` is normally only populated during an active user-interaction trace. On cold page load there's no trace session, so the wrappers are no-ops.

**Solution:** Bootstrap `window._xsLogs = []` in a `<script>` tag before any other scripts load. This causes all xs-trace wrappers to record during startup. Then inspect results in the console:

```js
window._xsLogs.filter(e => e.kind === 'app:trace').map(e =>
  e.label + ': ' + (e.duration||0).toFixed(1) + 'ms  @ ' +
  e.perfTs.toFixed(0) + (e.data ? ' ' + JSON.stringify(e.data) : ''))
```

We wrapped these functions with xsTrace:
- `expandEnrichments`
- `filterExternalExclusions`
- `dedupeEvents` (already had `xsTraceWith`)
- `filterHiddenSources`
- `buildSearchIndex`

## Before: baseline measurements

The processing chain (`processedEvents` reactive variable in Main.xmlui):

```
expandEnrichments -> filterExternalExclusions -> dedupeEvents -> filterHiddenSources -> buildSearchIndex
```

### Startup timeline

| Phase | Timestamp | Duration | Notes |
|-------|-----------|----------|-------|
| Empty data runs (2x) | ~1085ms | 0ms each | Chain evaluates before data arrives |
| Enrichments arrive (2x) | ~1130ms | ~3ms | 15 enrichments, fast |
| **Events API response** | ~3691ms | | **~2.5s network wait** for 5000 events |
| **dedupeEvents #1** | ~3692ms | **522ms** | 5015 in -> 3040 out |
| buildSearchIndex #1 | ~4215ms | 2.6ms | |
| **dedupeEvents #2** | ~4219ms | **642ms** | 5015 in -> 3040 out (identical!) |
| buildSearchIndex #2 | ~4861ms | 2.5ms | |
| filterEvents + render | ~4889ms | | UI appears |

### Key findings

1. **`dedupeEvents` is the bottleneck**: 522ms + 642ms = **1,164ms** of main thread blocking
2. **The processing chain runs twice** with the full event set back-to-back
3. **The dedup cache never hits**: the reactive expression `[...events.value, ...expandEnrichments(...)]` creates a new array reference each time, so `events === _dedupedEventsLastInput` is always `false`
4. **`expandEnrichments` was called twice per evaluation**: once in the `Array.isArray()` guard and once for the value
5. Everything else (`filterExternalExclusions`, `filterHiddenSources`, `buildSearchIndex`) is negligible: under 3ms each
6. Console showed: `[Violation] 'setTimeout' handler took 2210ms`

## Fix applied

### 1. Dedup cache: key on content, not reference

Changed cache validation from reference equality to length + first/last element identity:

```js
// Before (never hits because spread creates new array)
if (events === _dedupedEventsLastInput && _dedupedEventsCache) {
  return _dedupedEventsCache;
}

// After (hits when same data is re-spread into a new array)
if (_dedupedEventsCache &&
    events.length === _dedupedEventsLastLen &&
    events[0] === _dedupedEventsLastFirst &&
    events[events.length - 1] === _dedupedEventsLastLast) {
  return _dedupedEventsCache;
}
```

### 2. Split processedEvents expression

Broke the monolithic reactive expression into three variables so `expandEnrichments` is called once:

```xml
<!-- Before: expandEnrichments called twice (Array.isArray check + value) -->
<variable name="processedEvents" value="{window.buildSearchIndex(window.filterHiddenSources(window.dedupeEvents(window.filterExternalExclusions([...(Array.isArray(events.value) ? events.value : []), ...(Array.isArray(window.expandEnrichments(enrichments.value, ...)) ? window.expandEnrichments(enrichments.value, ...) : [])])), hiddenSources))}" />

<!-- After: three variables, expandEnrichments called once -->
<variable name="expandedEnrichments" value="{window.expandEnrichments(...)}" />
<variable name="combinedEvents" value="{[...events.value, ...expandedEnrichments]}" />
<variable name="processedEvents" value="{window.buildSearchIndex(window.filterHiddenSources(window.dedupeEvents(window.filterExternalExclusions(combinedEvents)), hiddenSources))}" />
```

## After: results

| Phase | Timestamp | Duration | Notes |
|-------|-----------|----------|-------|
| **dedupeEvents #1** | ~2865ms | **763ms** | 5015 in -> 3040 out |
| buildSearchIndex #1 | ~3628ms | 4.1ms | |
| **dedupeEvents #2** | ~3633ms | **0.0ms** | Cache hit! |
| buildSearchIndex #2 | ~3633ms | 0.3ms | |

The second dedupeEvents call now returns instantly from cache. Client-side processing time dropped from ~1,164ms to ~763ms (**~35% faster**).

## Next: remaining optimization opportunities

### 1. Server-side deduplication (biggest win)
The single `dedupeEvents` call still takes ~600-750ms to process 5015 events down to 3040. A Postgres view or materialized view could return pre-deduplicated data, eliminating this cost entirely. This would save ~700ms on every cold start.

### 2. Network payload size
5000 events at ~2.5s network time. Options:
- Return only fields needed for the list view (title, start_time, source, location, category) — descriptions could be fetched on demand
- Paginate the initial load (first 200 events, then fetch more as user scrolls)
- Server-side `select` to exclude large fields like `description` from the list query

### 3. Reduce reactive re-evaluations
The chain still runs 6+ times during startup (empty data, enrichments-only, full data, etc.). Debouncing or batching reactive updates could reduce redundant work.

## Instrumentation notes

The xs-trace wrappers were removed from production after measurement. To re-enable for the next round of tuning:

1. Add `<script>window._xsLogs = [];</script>` before other scripts in `index.html`
2. Wrap target functions with `window.xsTrace('label', function() { ... })` or `window.xsTraceWith('label', fn, extractData)`
3. Inspect via console: `window._xsLogs.filter(e => e.kind === 'app:trace')`
