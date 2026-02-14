# Pending / Done

## Table of Contents
- [PENDING: Bidirectional Infinite Scroll](#pending-bidirectional-infinite-scroll)
- [DONE: "More" Button for Calendar Display](#done-more-button-for-calendar-display)

# PENDING: Bidirectional Infinite Scroll

Discovery:
- Not blocked by XMLUI runtime.
- `List` has internal scroll-threshold fetch hooks for both directions:
  - `requestFetchPrevPage`
  - `requestFetchNextPage`
- These are wired in source but under-documented in component docs/metadata.
- `ScrollViewer` does not expose a generic scroll event, so this should be implemented through `List` pagination hooks, not custom viewport scroll listeners.

Evidence (XMLUI source):
- `/Users/jonudell/xmlui/xmlui/src/components/List/List.tsx` wires `requestFetchPrevPage` and `requestFetchNextPage` to `ListNative`.
- `/Users/jonudell/xmlui/xmlui/src/components/List/ListNative.tsx` invokes those callbacks near top/bottom during scroll.
- `/Users/jonudell/xmlui/xmlui/src/components-core/ApiBoundComponent.tsx` auto-injects pagination handlers for API-bound list data.

Analysis:
- Current app paging is manual/index-window (`More events...`), so infinite scroll requires moving from "single window + jump" to "accumulated window + append/prepend".
- This is feasible in both directions with stable anchors if we keep deterministic item ids and clamp bounds.
- Main risk is UX/state coherence with search:
  - search should operate within current browse baseline, not reset to origin
  - fetch triggers should be disabled or adjusted during active search to avoid surprising jumps.

Plan (high level):
1. Replace manual `More` progression with list-driven page requests (`requestFetchNextPage` / `requestFetchPrevPage`).
2. Keep a cursor/index state model that supports append (future) and prepend (earlier) slices.
3. Preserve viewport anchor on prepend so content doesn’t jump.
4. Define search contract: retain current baseline, suppress auto-fetch while typing.
5. Keep `More` as temporary fallback behind a flag until infinite scroll is validated, then remove.

# DONE: "More" Button for Calendar Display

Implemented:
- `More events...` pagination in `Main.xmlui` with fixed 50-item windows.
- Deterministic index-based paging in `helpers.js` with one-item overlap (last item stays visible as first on next page).
- Search continuity with paging state:
  - browse position is preserved
  - entering/exiting search does not lose the current `More` position
  - `More` hides during active search
- Reliable top jump on `More` using `Bookmark` anchor scroll (`topAnchor.scrollIntoView()`), without changing page centering/layout.

Result:
- Browse beyond 50 items without keystroke perf regression.
- Preserve context while paging and searching.
