# Understanding List Virtualization in This App

## Our Setup

From `Main.xmlui`:
```xmlui
<List data="{window.filterEvents(window.dedupeEvents([...]), filterTerm)}"
      fixedItemSize="true" limit="50">
```

Three key props work together: `data` (pre-filtered), `fixedItemSize="true"`, and `limit="50"`.

## How the Virtualization + Search Chain Works

The data flows through several stages, each with its own cost:

1. **DataSource fetch** — up to 5000 events from Supabase (one-time)
2. **`dedupeEvents()`** — O(n) grouping pass with a simple cache (`helpers.js:141`)
3. **`filterEvents()`** — O(n) scan across title, location, source, and description (`helpers.js:46`). Runs on **every keystroke** because `filterTerm` is a reactive var
4. **`limit="50"`** — XMLUI truncates the filtered result to 50 items before handing them to the virtualizer
5. **Virtualization** — only the ~10-15 items visible in the viewport get DOM nodes; the other 35-40 of the 50 are "virtual" (no DOM cost)
6. **`fixedItemSize="true"`** — lets the virtualizer measure one card and assume all are that height, so it can compute scroll positions without measuring every item

## Why Search Gets Snappier as You Type

The expensive part per keystroke is step 3 (the filter scan) plus step 5 (reconciling the React tree for up to 50 items). As you type more characters:

- The filter output shrinks (say from 800 → 200 → 40 matches)
- `limit="50"` clips the array, so the List component receives `min(matches, 50)` items
- Fewer items = fewer virtual elements to track = faster React reconciliation
- Once matches < 50, the list just gets shorter and React diffs less

## Tradeoffs of the `limit` Value

| Limit | Pros | Cons |
|-------|------|------|
| **50** (current) | 38% faster search; reconciliation and reactive overhead both halve | Users scroll through 50 events before needing to search |
| **100** | More scrollable without searching | ~100 virtual elements tracked; first keystroke ~859ms |
| **200-500** | More browsable without searching; users see more results | Heavier React reconciliation on each keystroke (even though DOM nodes stay ~12-15); filter narrows help less since limit is higher |
| **No limit** | Full dataset browsable | With 800+ events, every keystroke triggers reconciliation of the full filtered set; likely noticeable lag on mobile |

### Why limit=50 is the right choice

The measured data shows limit=50 delivers a 38% improvement on the first keystroke (859ms → 531ms). The theoretical tradeoff — users can only scroll 50 events before needing to search — is barely a tradeoff in practice. Search is one click (the magnifying glass icon) and one keystroke away. A calendar user scanning for events will either find what they want in the first screenful (~12 cards) or reach for search. The 38 off-screen items between limit=50 and limit=100 are items the user would have to deliberately scroll past — unlikely behavior when search is available. Meanwhile, every keystroke they type benefits from faster reconciliation.

## Fetch Size vs. Virtualization

These are independent concerns. The `limit="50"` on the List and the `fixedItemSize` behavior are entirely downstream of the fetch:

1. Supabase returns up to 5000 events (one-time fetch, held in memory)
2. `dedupeEvents()` and `filterEvents()` run over that full in-memory array on every keystroke
3. `limit="50"` truncates the result before handing it to the virtualizer
4. The virtualizer only cares about how many items it receives (≤50), not how many were fetched

Whether Supabase returns 200 or 5000 events, the virtualizer always sees at most 50. The fetch size affects steps 2-3 (the JS filter scan cost), not the virtualization/rendering cost.

## The Key Insight

The `limit` is **not** about DOM nodes — virtualization handles that. It's about **React's virtual DOM diffing**. Each item in the list, even if not rendered to the DOM, is a React element that must be created, diffed, and potentially reconciled on every state change (i.e., every keystroke). 50 works well because:

- It's well below your typical unfiltered dataset (~800+), so the first few keystrokes feel fast
- It's well above the visible viewport (~12 cards), so users can scroll meaningfully
- `fixedItemSize="true"` eliminates per-item measurement, keeping the virtualizer's job trivial
- Search is always one click away, making the scroll limit nearly invisible to users

## Tradeoffs of `fixedItemSize="true"`

Our EventCards have **variable actual heights** due to:

- Titles that wrap to multiple lines (`overflowMode="flow"`)
- Conditional location line (`when="{$props.event.location}"`)
- Conditional description snippet (only appears during search when there's a match in description)

So `fixedItemSize="true"` tells the virtualizer to measure the first card and assume all cards are that height. This is a performance optimization that trades accuracy for speed.

| | `fixedItemSize="true"` (current) | `fixedItemSize="false"` |
|---|---|---|
| **Scroll perf** | Best — no per-item measurement | Slightly worse — measures items as they enter viewport |
| **Scrollbar accuracy** | Inaccurate — thumb position drifts because estimated total height is wrong | Accurate (progressively, as items are measured) |
| **Visual correctness** | Cards may clip or have extra whitespace if actual height differs from first card's height | Each card gets its true height |
| **Search transition** | When description snippet appears/disappears, card height changes but virtualizer doesn't know | Adapts naturally |

The XMLUI List uses [Virtua](https://github.com/inokawa/virtua) under the hood. Per the XMLUI source (`xmlui/src/components/List/SCROLLBAR_ISSUE_SOLUTIONS.md`), scrollbar inaccuracy with variable-height items is an inherent limitation of all virtual scrollers — Virtua, react-virtuoso, FlashList all have this issue because they can't know the actual size of items that haven't been rendered yet.

**Bottom line:** If scrollbar jumping or content clipping aren't noticeable in practice, the `fixedItemSize="true"` lie is cheap and the perf win is real. If artifacts appear, switching to `false` fixes them at a modest cost.

## Measuring Search Performance with the Inspector

The XMLUI inspector (launched via the cog icon) reads `window._xsLogs` and visualizes traces in `xs-diff.html`. Here's what it already tells us about a search keystroke, and what's missing.

### What the Inspector Already Shows

When you type a character in the search box, the engine logs a trace with:

- **`interaction` (keydown)** — timestamped with `perfTs`
- **`handler:start` / `handler:complete` (onDidChange)** — with `duration` in ms, covering the time the engine spends executing `filterTerm = val` and reactively re-evaluating the List's `data` expression
- **`state:changes`** — shows `filterTerm` changing
- **Timeline breakdown** — the viewer calculates phases (handler time, idle gaps, overhead) and shows a per-phase duration table

So you get the **total keystroke-to-done time** and a breakdown into handler vs. post-handler phases.

### What's Missing

The engine treats the entire handler as one block. `filterEvents()` and `dedupeEvents()` run inside the reactive re-evaluation triggered by `filterTerm = val`, but the engine doesn't instrument them individually. A trace might show:

```
handler:didChange  45ms
```

But you can't tell how much of that 45ms was:

| Phase | Where it runs | Visible in inspector? |
|-------|--------------|----------------------|
| `dedupeEvents()` | Inside reactive re-eval of List `data` expression | No (bundled into handler duration) |
| `filterEvents()` scanning 800+ events | Inside reactive re-eval of List `data` expression | No (bundled into handler duration) |
| React reconciliation of ≤100 List items | After handler completes, in the XMLUI/React render cycle | Partially — shows as "overhead" or "after handlers" in timeline |

### Gap Analysis (before xsTrace)

| Measurement | Status | How to get it |
|-------------|--------|---------------|
| Total keystroke-to-done time | **Have it** | Inspector timeline `totalDuration` |
| Handler execution time | **Have it** | `handler:complete` duration |
| `dedupeEvents()` time | **Missing** | Add app-level timing |
| `filterEvents()` time | **Missing** | Add app-level timing |
| React reconciliation time | **Partial** | "after handlers" phase in timeline; could also use React DevTools Profiler |
| Time per character as search narrows | **Missing** | Would need to log per-keystroke timings and correlate with result count |

### Bridging the Gap: `xsTrace` (generic, in trace-tools)

Rather than adding ad-hoc `performance.now()` calls to each app, trace-tools provides a generic utility (`xs-trace.js`) that any XMLUI app can include. It pushes timing entries into `_xsLogs` so they appear in the inspector timeline alongside engine-generated handler and API entries.

**How it works:**

1. **`trace-tools/xs-trace.js`** — a small helper any app includes via `<script>`:
   ```js
   window.xsTrace = function(label, fn) {
     const logs = window._xsLogs;
     if (!logs) return fn(); // no inspector, just run
     const traceId = logs[logs.length - 1]?.traceId;
     const start = performance.now();
     const result = fn();
     const duration = performance.now() - start;
     logs.push({ kind: "app:timing", label, traceId, perfTs: start, duration });
     return result;
   }
   ```

2. **xs-diff.html** — renders `app:timing` entries in the timeline breakdown (alongside handlers and API calls)

3. **Any app** wraps expensive functions:
   ```js
   // before
   return filterEvents(events, term)
   // after
   return window.xsTrace("filterEvents", () => filterEvents(events, term))
   ```

**Why this works without engine changes:** Reactive expressions run synchronously within a handler, so the most recent `_xsLogs` entry reliably has the active `traceId`. The utility piggybacks on the existing `_xsLogs` infrastructure — no engine release needed.

**Implementation note:** In `helpers.js`, the wrapper must save a reference to the original function before overwriting `window.filterEvents`, because top-level function declarations in a non-module script *are* `window.filterEvents` — overwriting without saving causes infinite recursion:
```js
var _filterEvents = filterEvents;
window.filterEvents = function(events, term) {
  return window.xsTrace
    ? window.xsTrace("filterEvents", function() { return _filterEvents(events, term); })
    : _filterEvents(events, term);
};
```

## Measured Results: Search Typing "jazz"

With `xsTrace` in place, here's what the inspector shows for typing "jazz" one character at a time (Santa Rosa, ~800 events):

| Keystroke | Filter term | Total | filterEvents | Reactive + reconciliation overhead |
|-----------|------------|-------|-------------|-----------------------------------|
| 1st | "j" | 859ms | 2ms | 857ms |
| 2nd | "ja" | 929ms | 3ms | 926ms |
| 3rd | "jaz" | 554ms | 3ms | 551ms |
| 4th | "jazz" | 343ms | 3ms | 340ms |

### Where the Time Goes (per-keystroke perfTs analysis)

Looking at the `perfTs` gaps within each trace reveals three distinct phases. Here's the breakdown for the first keystroke ("j"):

| Phase | Duration | What's happening |
|-------|----------|-----------------|
| `handler:start` → `state:changes` | ~200ms | Engine processes state change (`filterTerm: "" → "j"`) |
| `state:changes` → `filterEvents` | ~414ms | Reactive re-evaluation of the List's `data` expression: array spreading, `dedupeEvents` (cache hit, ~0ms), `expandEnrichments` |
| `filterEvents` itself | ~2ms | O(n) scan over ~800 events |
| `filterEvents` → `handler:complete` | ~235ms | React reconciliation of ~100 List items (EventCard components) |

Both the pre-filter and post-filter overhead shrink as the result set shrinks — confirming the "getting snappier" effect is about reactive re-evaluation and React reconciliation, not about filtering.

### Key Findings

1. **`filterEvents` is negligible at 2-3ms** — server-side full-text search would not help. The client-side O(n) scan over 800 events is not the bottleneck.

2. **The reactive re-evaluation gap (~400ms on first keystroke) is the largest cost.** This is the XMLUI engine re-evaluating the complex `data` expression on the List, which includes array spreading, `dedupeEvents`, and `expandEnrichments`. This cost scales with expression complexity, not just item count.

3. **React reconciliation (~235ms on first keystroke) is the second largest cost.** This is React diffing and reconciling the ~100 EventCard components in the List. Lowering `limit` would directly reduce this.

4. **Both costs shrink as search narrows:** 859ms → 929ms → 554ms → 343ms. The blip at "ja" may be timing noise. By "jazz" (likely <100 results), reconciliation is significantly cheaper.

### Implications for Optimization

| Strategy | Would it help? | Why / why not |
|----------|---------------|---------------|
| Server-side full-text search (Supabase `tsvector`) | **No** | `filterEvents` is already 2-3ms |
| Lower `limit` from 100 to 50 | **Modest** | Would reduce React reconciliation (~235ms phase) |
| Debounce search input | **Yes** | Would skip intermediate keystrokes entirely |
| Simplify the `data` expression | **Potentially significant** | The 400ms reactive re-evaluation gap suggests the expression itself is expensive to re-evaluate |
| Pre-compute the deduped+enriched array | **Potentially significant** | Avoid re-evaluating `dedupeEvents(expandEnrichments(...))` on every keystroke when only `filterTerm` changed |

## Pre-compute Experiment: Dead End

Based on the analysis above, we tried pre-computing the deduped+enriched array so that per-keystroke evaluation would only run `filterEvents` against a pre-built array. Three iterations were attempted:

### Iteration 1: Reactive global variable

Store the pre-computed array in `var preparedEvents` (a reactive XMLUI global). ChangeListeners on `events.value` and `enrichments.value` recompute and assign it.

**Result: 4x worse** (3531ms vs 859ms for "j"). XMLUI deep-compares reactive variables on every state change. With 3099 objects in the array, the deep-comparison cost on every `filterTerm` change far exceeded the savings from avoiding recomputation.

### Iteration 2: XMLUI 0.12.1 engine

Attempted upgrading from 0.12.0 to 0.12.1 to see if newer engine handled reactivity better.

**Result: 10x worse** (massive React reconciliation regression). Reverted immediately.

### Iteration 3: Non-reactive window storage + counter

Store data on `window.preparedEvents` (outside XMLUI reactivity) and use a cheap `var preparedVersion = 0` counter to trigger re-renders. The List expression references the counter: `data="{preparedVersion && window.filterEvents(window.preparedEvents, filterTerm)}"`.

**Result: No meaningful improvement.** Comparison for "j" keystroke:

| Phase | Before (baseline) | After (pre-compute) |
|-------|-------------------|---------------------|
| state:changes → filterEvents (reactive overhead) | ~414ms | ~385ms |
| filterEvents | 2ms | 3ms |
| filterEvents → handler:complete (React reconciliation) | ~235ms | ~228ms |
| **Total** | **859ms** | **811ms** |

The ~400ms reactive re-evaluation gap is **not** caused by evaluating `dedupeEvents`/`expandEnrichments` — simplifying the expression saved only ~30ms. The cost is in XMLUI's internal reactive infrastructure: dependency tracking, change propagation, and preparing to re-render. It's inherent to the framework, not the expression.

### What This Rules Out

Pre-computing data at the application level cannot address the bottleneck because the bottleneck is inside the XMLUI engine's reactive loop, not in application code. The two remaining app-level strategies are:

- **Debounce** — skip intermediate keystrokes (avoids the cost entirely for skipped characters)
- **Lower `limit`** — reduce React reconciliation cost (the ~235ms phase)

Any deeper improvement requires changes to the XMLUI engine's reactive evaluation or React reconciliation strategy.

## Fixed Card Height Experiment: No Effect

With `fixedItemSize="true"` already set, we tested whether enforcing truly uniform card heights (via `height="90px" overflow="hidden"` on the Card) would improve performance. The hypothesis: variable actual heights might cause layout thrashing or reflow during reconciliation.

| Phase | Variable height | Fixed height | Diff |
|-------|----------------|-------------|------|
| State processing | ~104ms | ~107ms | +3ms |
| Reactive re-eval | ~298ms | ~241ms | -57ms (noise) |
| filterEvents | ~2ms | ~2ms | 0ms |
| Reconciliation | ~118ms | ~118ms | 0ms |
| **Total** | **531ms** | **476ms** | **~55ms (noise)** |

Reconciliation was identical (118ms both ways) — React's virtual DOM diffing doesn't care about actual CSS heights. The ~57ms difference in reactive re-eval is within run-to-run variability.

**Conclusion:** `fixedItemSize="true"` already tells the virtualizer to skip per-item measurement. Whether cards are genuinely uniform or not makes no measurable difference. The prop controls virtualizer behavior, not DOM layout cost.

### fixedItemSize="true" vs "false"

A follow-up test flipped the prop itself:

| Phase | true | false | Diff |
|-------|------|-------|------|
| State processing | ~104ms | ~104ms | 0ms |
| Reactive re-eval | ~298ms | ~290ms | -8ms |
| filterEvents | ~2ms | ~3ms | +1ms |
| Reconciliation | ~118ms | ~117ms | -1ms |
| **Total** | **531ms** | **520ms** | **-11ms (noise)** |

`fixedItemSize` is a no-op at limit=50. The virtualizer's per-item measurement cost is negligible at this scale — it would only matter with hundreds of items. We keep `true` as the default since it doesn't hurt, but at limit=50 we could switch to `false` and get accurate scrollbar positioning for free with no performance cost.

## Lowering limit to 50: Measured Win

After the pre-compute dead end, lowering `limit` from 100 to 50 was the simplest remaining lever. Here's the measured comparison for the first keystroke ("j"), both unbatched:

| Phase | limit=100 | limit=50 | Savings |
|-------|-----------|----------|---------|
| State processing | ~200ms | ~104ms | ~96ms |
| Reactive re-eval gap | ~414ms | ~298ms | ~116ms |
| filterEvents | ~2ms | ~2ms | 0ms |
| Reconciliation | ~235ms | ~118ms | ~117ms |
| **Total** | **859ms** | **531ms** | **328ms (38%)** |

Two surprises:

1. **Reconciliation roughly halved** (235→118ms) — expected, since half the List items means half the React elements to diff.

2. **Reactive re-eval also dropped** (414→298ms) — unexpected. This suggests that XMLUI's reactive overhead partly scales with the number of items the List will receive, not just expression complexity. The engine may be doing per-item work during dependency evaluation, not just during React reconciliation.

The combined effect is a 38% improvement on the worst-case keystroke. Subsequent keystrokes benefit proportionally — by "jazz" (fewer than 50 matches), the limit no longer clips the result and the improvement comes purely from the reactive re-eval savings.

## Engine Internals: Why the Reactive Gap Exists

Reading the XMLUI source (`StateContainer.tsx`, `Container.tsx`, `ListNative.tsx`, `container-helpers.tsx`) reveals exactly where the ~298ms reactive re-eval and ~118ms reconciliation come from. The engine is **not** a signals/observables system — it's built entirely on React state with a custom expression evaluation layer.

### The 6-Layer State Pipeline

Every component with variables gets wrapped in a `StateContainer` that assembles state through six layers:

1. Parent state (scoped by `uses`)
2. Component reducer state (`useReducer`)
3. Component APIs (`useState`)
4. Context variables (`$item`, `$itemIndex`, etc.)
5. Local variable resolution (**two passes** — once for forward references, once final)
6. Routing parameters

Each layer creates intermediate objects wrapped in `useShallowCompareMemoize`. Six layers times shallow comparison on potentially large state objects adds up.

### Two-Pass Variable Resolution

The most expensive part of the pipeline: `useVars` runs twice per render per `StateContainer`. Each pass iterates over every variable definition, collects dependency names, picks those values from state via `pickFromObject`, shallow-compares them against the last render, and only re-evaluates the expression if dependencies changed. This is per-variable, per-render, done twice, for every StateContainer in the tree.

### Why Reconciliation Scales with Item Count: renderChild Instability

The `stableRenderChild` callback in `Container.tsx` has `componentState` in its `useCallback` dependency array:

```typescript
const stableRenderChild = useCallback(
  (childNode, ...) => { /* uses componentState */ },
  [componentState, dispatch, appContext, ...]
);
```

When `filterTerm` changes, `componentState` changes, which recreates `stableRenderChild`, which changes the `renderChild` prop on every `MemoizedItem` in the List. This defeats `React.memo` — **all 50 items fully re-render on every keystroke**, even though only the parent's `filterTerm` changed, not any item's `$item` data.

Each re-rendered item goes through the full 6-layer `StateContainer` pipeline. With 50 items, that's 50 × 2-pass variable resolution = 100 variable resolution passes per keystroke.

### Why This Is Intentional

The initial reaction is "use a ref to stabilize `renderChild`." But the callback instability **is the change notification mechanism**. XMLUI doesn't use React Context per state value — it uses callback identity as a proxy for "something changed above you, re-evaluate." If `renderChild` were stable, children would never see updated parent state:

- `filterTerm` changes → description snippets wouldn't update
- `picksData` changes → pick checkboxes wouldn't reflect current state
- Any global variable change would be invisible to list items

The design chooses **correctness over performance**: every keystroke re-renders all items because the engine can't know which items depend on `filterTerm` vs which don't.

### What a Real Fix Would Require

| Strategy | Complexity | Effect |
|----------|-----------|--------|
| **Fine-grained dependency tracking** — track which items depend on which state keys; only re-render items whose dependencies changed | High (engine rewrite) | Would eliminate unnecessary item re-renders |
| **React Context for hot state** — put frequently-changing values like `filterTerm` in a Context so only consumers re-render | Medium (engine change) | Would decouple item re-renders from unrelated state changes |
| **Split renderChild** — separate structural (stable) from state-dependent (unstable) callback | Medium (engine change) | Would let `React.memo` work for items that only need structure |

This explains the earlier surprise that reactive re-eval dropped when limit went from 100 to 50: fewer items means fewer `StateContainer` pipelines running the 6-layer + 2-pass resolution. The limit controls not just React reconciliation but also how many times the engine's internal state assembly runs.

## Component Depth Experiment: The Real Cost

To isolate how much of the per-keystroke cost comes from the engine's base per-item overhead vs the component tree inside each item, we replaced EventCard (which has ~12 child components) with a bare `<Text value="{$item.title}" />`.

| Phase | EventCard (~12 children) | Text only (1 child) | Savings |
|-------|--------------------------|----------------------|---------|
| State processing | ~104ms | ~17ms | ~87ms (83%) |
| Reactive re-eval | ~298ms | ~51ms | ~247ms (83%) |
| filterEvents | ~2ms | ~2ms | 0ms |
| Reconciliation | ~118ms | ~25ms | ~93ms (78%) |
| **Total** | **531ms** | **102ms** | **429ms (81%)** |

Three data points confirm linear scaling:

| Template | ~Components/item | Total | Per item |
|----------|-----------------|-------|----------|
| Bare Text | 1 | 102ms | 2.0ms |
| Stripped Card (Card → VStack → Text ×4) | 6 | 240ms | 4.8ms |
| Full EventCard (+ Link, Markdown, HStack, AddToCalendar, Checkbox) | 12+ | 531ms | 10.6ms |

Phase breakdown across all three:

| Phase | Text (1) | Stripped (6) | Full (12+) |
|-------|----------|-------------|------------|
| State processing | ~17ms | ~56ms | ~104ms |
| Reactive re-eval | ~51ms | ~112ms | ~298ms |
| filterEvents | ~2ms | ~2ms | ~2ms |
| Reconciliation | ~25ms | ~63ms | ~118ms |
| **Total** | **102ms** | **240ms** | **531ms** |

Every phase scales with component count — not just reconciliation. The 6-layer StateContainer pipeline runs for every component in the tree, including simple Text elements that have no state of their own. Simple Text components cost ~0.55ms each per item; heavier components (Link, Markdown, AddToCalendar) cost ~0.97ms each.

### Why This Matters for XMLUI

The tempting app-level response is "simplify your cards — fewer components, better performance." But this is exactly the wrong takeaway. XMLUI's value proposition is composability: developers should write clean, readable component trees without worrying about depth. An EventCard *should* have a Card wrapping a VStack with Text, Link, and Checkbox children — that's the natural way to express the UI.

The problem is that the engine charges ~0.7ms per component per list item per keystroke. At this rate:

- 50 items × 5 components = 250 evaluations → ~175ms overhead
- 50 items × 12 components = 600 evaluations → ~420ms overhead
- 50 items × 20 components = 1000 evaluations → ~700ms overhead

A richer card template (with images, badges, action menus) would push into multi-second keystroke latency. Developers shouldn't have to choose between expressiveness and performance.

### What This Tells the Engine Team

The 6-layer StateContainer pipeline runs for every component in the tree, including leaf components like Text and SpaceFiller that have no variables, no loaders, and no state of their own. The overhead is structural — the pipeline runs because the component *exists*, not because it *needs* state resolution.

Potential engine-level improvements:

| Strategy | What it would do |
|----------|-----------------|
| **Fast-path for stateless components** | Skip the 6-layer pipeline for components with no variables, no `when`, no expressions referencing dynamic state. A Text with `value="{$props.event.title}"` where `$props` hasn't changed needs zero work. |
| **Shallow re-render boundary at List items** | When `filterTerm` changes but `$item` hasn't, the item subtree doesn't need to re-render. Only components that actually reference `filterTerm` (like the Markdown snippet) need updating. |
| **Batch the two-pass resolution** | The two-pass `useVars` loop could be eliminated for components whose variables have no forward references (the common case for leaf components). |
| **Lightweight container for leaf components** | Text, SpaceFiller, Icon — these don't need the full ContainerWrapper → StateContainer → Container pipeline. A direct adapter path would skip 90% of the overhead. |

The goal: make composition cost O(changed components), not O(total components). A keystroke that changes `filterTerm` should re-evaluate the ~3 components per card that reference it (the Markdown snippet and its parent conditionals), not all ~12.

## XMLUI List Documentation

- [List component docs (limit, fixedItemSize, virtualization)](https://docs.xmlui.org/components/List)
- [Items component docs (non-virtualized alternative)](https://docs.xmlui.org/components/Items)
