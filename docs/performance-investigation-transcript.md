# Performance Investigation Transcript

A lightly edited transcript of a Claude Code session investigating Bloomington calendar startup performance. April 8, 2026.

---

**Jon:** Let's have a timing analysis of the bloomington calendar loading in an iframe. I want to make it faster. We pull in 5000 events on page load, it's noticeably slow due to that, then there's the client-side filtering. It's always a tradeoff between having a lot searchable in memory and optimizing for cold start. Anyway here's a trace, see what you can see, we might need to turn on xs-trace for timing in which case let's do that. I am running on 8080.

**Claude:** *(finds the latest trace export, starts to read it)*

**Jon:** Actually the page load I just did has no startup phase like other apps do. I think we need to wrap xs-trace around the API calls? There are no user interactions on page load to trigger a trace.

**Claude:** Right — xs-trace captures user interactions, not the initial data fetch. Let me find the calendar code to see how the API calls work.

**Jon:** Look in the trace-tools doc to find out about the xs-trace wrapper.

**Claude:** *(searches trace-tools, finds and reads `xs-trace.js`)*

OK so `xs-trace.js` provides timing wrappers, but the problem is `_xsLogs` only exists when a trace is active (i.e. triggered by user interaction). On cold page load there's no active trace.

**Jon:** Right here in ~/community-calendar.

**Claude:** *(reads Main.xmlui, helpers.js, Globals.xs, index.html)*

Here's what I see. The bottleneck on page load has two phases:

**Phase 1: API fetch** — The `DataSource id="events"` fires a single Supabase REST call for 5000 events.

**Phase 2: Client-side processing chain** (Main.xmlui line 133):
```
filterExternalExclusions → dedupeEvents → filterHiddenSources → buildSearchIndex
```
All run synchronously on every reactive evaluation.

The `xs-trace.js` wrappers won't help here because `_xsLogs` is `null` at page load — it's only populated when the XMLUI inspector starts a trace via user interaction.

**Two approaches to get timing:**

1. **Quick console instrumentation** — add `performance.mark`/`performance.measure` calls around the processing chain in `helpers.js`, then view in DevTools Performance tab.

2. **Bootstrap `_xsLogs` early** — initialize `window._xsLogs = []` before XMLUI loads, so the xs-trace wrappers actually record during startup, then export later.

Option 2 is more interesting since you already have the xs-trace infrastructure. Want me to:

1. Add `window._xsLogs = [];` early in `index.html` (before XMLUI loads)
2. Wrap the expensive functions (`dedupeEvents`, `buildSearchIndex`, `filterHiddenSources`, `filterExternalExclusions`, `expandEnrichments`) with `xsTrace()` calls in `helpers.js`

Then you can reload, and the startup timings will be in `_xsLogs` — viewable in the console or via a trace export.

**Jon:** Yes that's just what I was hoping for.

**Claude:** *(adds `window._xsLogs = []` to index.html, wraps all five functions with xsTrace in helpers.js)*

Go ahead and reload the page in the browser, then open the console and run:

```js
window._xsLogs.filter(e => e.kind === 'app:trace')
```

**Jon:** *(reloads, pastes console output showing 41 trace entries)*

**Claude:** Here's what the data tells us. Focusing on the `startup-*` trace entries with real data:

**Timeline:**

| Phase | perfTs | Duration | Notes |
|-------|--------|----------|-------|
| Early runs (no data yet) | ~1085ms | 0ms each | Chain runs 2x on empty/null data |
| Enrichments arrive | ~1130ms | ~3ms | Small dataset |
| Chain run #1 (enrichments only) | ~1133ms | ~5ms | No events yet, fast |
| **Events API response** | ~3691ms | | **~2.5s network wait** |
| **dedupeEvents** #1 | ~3692ms | **~522ms** | The big one |
| buildSearchIndex #1 | ~4215ms | 2.6ms | |
| **dedupeEvents** #2 | ~4219ms | **~642ms** | Runs again immediately! |
| buildSearchIndex #2 | ~4861ms | 2.5ms | |
| filterEvents calls | ~4889ms | | Rendering begins |

**Key findings:**

1. **`dedupeEvents` is the bottleneck** — 522ms + 642ms = **~1.2 seconds** of main thread blocking
2. **The processing chain runs twice** with the full event set back-to-back
3. **Network fetch takes ~2.5s**
4. Everything else (`filterExternalExclusions`, `filterHiddenSources`, `buildSearchIndex`, `expandEnrichments`) is negligible — under 3ms each

Now let me capture the baseline with event counts. Can you run:

```js
window._xsLogs.filter(e => e.label === 'dedupeEvents' && e.data).map(e => e.data)
```

**Jon:** *(pastes results)*

```
{inputCount: 0, outputCount: 0}
{inputCount: 0, outputCount: 0}
{inputCount: 15, outputCount: 15}
{inputCount: 15, outputCount: 15}
{inputCount: 5015, outputCount: 3040}
{inputCount: 5015, outputCount: 3040}
```

**Claude:** Good baseline:

- 5015 events in (5000 from API + 15 enrichments) → 3040 after dedup
- `dedupeEvents` runs **twice** with the full set: 522ms + 642ms = **1,164ms**
- The second full dedupeEvents run (642ms) is pure waste — same 5015 in, same 3040 out

The dedup cache never hits because `[...events.value, ...expandEnrichments(...)]` creates a new array reference every time.

**Jon:** Is there anything we can just cut? Either of the #1s and/or #2s?

**Claude:** Two things to cut:

1. **`expandEnrichments` is called twice per evaluation** — the `Array.isArray` guard calls it, then the value branch calls it again.

2. **The dedup cache never hits** — because the spread creates a new array reference every time, so `events === _dedupedEventsLastInput` is always false.

*(proposes splitting the monolithic expression into three variables and fixing the cache)*

**Jon:** Yes but let's first capture a before snapshot. Or is what you have enough? We do need to verify it's the same set of events also.

**Claude:** What we have is a good "before" snapshot. The dedupeEvents data objects have the counts: 5015 in, 3040 out, confirmed same on both runs.

*(applies the Main.xmlui expression split)*

**Jon:** *(reloads)* Did not feel different. Are we stuck in browser cache again?

**Claude:** Try a hard refresh — Cmd+Shift+R.

**Jon:** *(hard refreshes, still sees two full 5015→3040 runs)*

**Claude:** Still two full runs. The split into separate variables didn't help — XMLUI's reactive system still creates a new `combinedEvents` array each time. The real fix is the dedup cache itself.

*(changes cache key from reference equality to length + first/last element identity)*

**Jon:** Let me try in FF though, we are always getting bit by browser cache. Nope same. Felt faster though, do you want to look at timing?

**Claude:** *(reads the full timing output)*

The cache is working! Look at the second 5015→3040 run:

**Before:** 522ms + 642ms = **1,164ms**
**After:** 763ms + **0.0ms** = **763ms**

The second dedupeEvents call hits the cache and returns instantly.

**Jon:** Now is a good stopping point. Commit and push, write up an issue, explain what we tested and how, what we improved, and what is the next thing to improve.

**Claude:** *(pauses)* We should remove the xs-trace wrappers first, right?

**Jon:** Hmm. We will now remove xs-trace wrappers right? Will put back for next phase of tuning but don't want the overhead in production. The basic trace-tools are zero impact unless xsVerbose is on.

**Claude:** Good call. *(reverts the xs-trace wrappers and `_xsLogs` bootstrap from index.html, keeps only the dedup cache fix and expression split)*

Final diff — just the two production fixes:

**helpers.js**: Cache keys on `length + first/last element identity` instead of reference equality.

**Main.xmlui**: Split monolithic `processedEvents` expression into `expandedEnrichments`, `combinedEvents`, `processedEvents` so `expandEnrichments` is called once.

*(commits, pushes, writes docs/performance-investigation.md, creates issue #53)*

**Result:** Client-side processing dropped from ~1,164ms to ~763ms (~35% faster). The next big win is server-side deduplication to eliminate the remaining ~700ms `dedupeEvents` call entirely.
