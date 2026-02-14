# Understanding List Virtualization and Search in This App

## Our Setup

From `Main.xmlui`:
```xmlui
<List data="{window.filterEvents(window.dedupeEvents([...]), filterTerm)}"
      fixedItemSize="true" limit="50">
```

Three key props work together: `data` (pre-filtered), `fixedItemSize="true"`, and `limit="50"`.

## How the Search Chain Works

Data flows through several stages on every keystroke:

1. **DataSource fetch** — up to 5000 events from Supabase (one-time)
2. **`dedupeEvents()`** — O(n) grouping pass with a simple cache (`helpers.js:141`)
3. **`filterEvents()`** — O(n) scan across title, location, source, and description (`helpers.js:46`). Runs on **every keystroke** because `filterTerm` is a reactive var
4. **`limit="50"`** — XMLUI truncates the filtered result to 50 items before handing them to the virtualizer
5. **Virtualization** — only the ~10-15 items visible in the viewport get DOM nodes; the other 35-40 of the 50 are "virtual" (no DOM cost)
6. **`fixedItemSize="true"`** — lets the virtualizer measure one card and assume all are that height, so it can compute scroll positions without measuring every item

## Why Search Gets Snappier as You Type

The expensive part per keystroke is the XMLUI engine's reactive re-evaluation and React reconciliation of up to 50 items. As you type more characters:

- The filter output shrinks (say from 800 → 200 → 40 matches)
- `limit="50"` clips the array, so the List receives `min(matches, 50)` items
- Fewer items = fewer React elements to diff = faster reconciliation
- Once matches < 50, the list just gets shorter

## Why limit=50

Measured data shows limit=50 delivers a 38% improvement on the first keystroke vs limit=100 (859ms → 531ms). The tradeoff — users can only scroll 50 events before needing to search — is barely a tradeoff in practice. Search is one click (the magnifying glass) and one keystroke away. A calendar user scanning for events will either find what they want in the first screenful (~12 cards) or reach for search.

| Limit | Pros | Cons |
|-------|------|------|
| **50** (current) | 38% faster search; best responsiveness | Users scroll 50 events before needing to search |
| **100** | More scrollable | ~100 virtual elements tracked; first keystroke ~859ms |
| **200+** | More browsable | Heavier reconciliation on each keystroke; noticeable lag |

## Fetch Size vs. Virtualization

These are independent concerns. Whether Supabase returns 200 or 5000 events, the virtualizer always sees at most 50. The fetch size affects the JS filter scan cost (2-3ms — negligible), not the rendering cost.

## The Key Insight

The `limit` is **not** about DOM nodes — virtualization handles that. It's about **React's virtual DOM diffing**. Each item in the list, even if not rendered to the DOM, is a React element that must be created, diffed, and reconciled on every keystroke.

## fixedItemSize Tradeoffs

Our EventCards have **variable actual heights** (wrapping titles, conditional location/description lines). `fixedItemSize="true"` tells the virtualizer to measure the first card and assume all match.

| | `fixedItemSize="true"` (current) | `fixedItemSize="false"` |
|---|---|---|
| **Scroll perf** | Best — no per-item measurement | Slightly worse |
| **Scrollbar accuracy** | May drift with variable heights | Accurate (progressively) |
| **Visual correctness** | Cards may clip or show extra whitespace | Each card gets its true height |

At limit=50, measurement shows **no performance difference** between true and false. We could switch to `false` for accurate scrollbar positioning with no cost. We keep `true` as the default since it doesn't hurt.

## Measuring and Optimizing Search Performance

App-level measurement using [trace-tools](https://github.com/xmlui-org/trace-tools) confirms that `filterEvents` takes 2-3ms — the bottleneck is engine-internal reactive overhead and React reconciliation, not app-level code. The only effective app-level lever is `limit` (lowering from 100 to 50 gave a 38% improvement). See the [xsTrace case study](https://github.com/xmlui-org/trace-tools#xstrace-case-study-community-calendar-search) for the full investigation, measurement methodology, and engine analysis.

## XMLUI List Documentation

- [List component docs](https://docs.xmlui.org/components/List) (limit, fixedItemSize, virtualization)
- [Items component docs](https://docs.xmlui.org/components/Items) (non-virtualized alternative)
