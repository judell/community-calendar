# Pending: "More" Button for Calendar Display

## Problem
List is capped at `limit="50"` for search keystroke performance (531ms vs 859ms at 100). Users can only browse 50 events before needing to search.

## Three Approaches

### Option A: Dynamic limit (recommended)
`limit="{filterTerm ? 50 : displayLimit}"`

- Browsing: "More" button increments `displayLimit` by 50 (100, 150, etc.). No keystroke diffing happening, virtualization handles DOM fine.
- Searching: limit snaps back to 50 automatically — fast keystrokes preserved.
- The perf problem is specifically on keystrokes. When not typing, 100+ items in the virtualizer costs nothing measurable (README confirms: "virtualization handles that").

Changes:
1. `Main.xmlui` — add `var.displayLimit="{50}"`, change `limit="50"` to `limit="{filterTerm ? 50 : displayLimit}"`, add "More" button after List
2. `helpers.js` — stash `window._lastFilteredCount` in filterEvents wrapper so button knows when to hide
3. Button hidden during search and when all events are already visible

```xml
<Button
  when="{events.loaded && viewMode === 'all' && !filterTerm && window._lastFilteredCount > displayLimit}"
  label="More events..."
  variant="outlined"
  onClick="displayLimit = displayLimit + 50"
  width="100%"
  marginTop="$space-2"
/>
```

### Option B: Slice-based pagination
`.slice(displayOffset, displayOffset + 50)` in the data expression.

- Always exactly 50 items, zero perf concern
- Earlier events disappear when paging forward (needs "Back" button too)
- True time-based paging through events
- All data already client-side, no re-fetch needed

### Option C: Time-cursor paging (new)
Keep a `displayStartTime` cursor and always render the first 50 events at/after that time.

- Default cursor is `now` (or selected day start)
- `MORE` moves cursor to the start time of the last visible event
- If you hit item `#50` and it is still the same day (for example `7:30pm`), next page starts from that time and reveals later events
- Keeps page size fixed at 50 for predictable performance
- Matches browsing intent better than pure count growth

Implementation sketch:
1. `Main.xmlui`: add `var.displayStartTime` and compute a `pagedEvents` array from filtered events where `event.start_time >= displayStartTime`, then `slice(0, 50)`
2. `Main.xmlui`: `MORE` button sets `displayStartTime` to last visible event start time (plus a tiny tie-breaker if needed)
3. `helpers.js`: add stable cursor bump helper so same-timestamp events do not repeat forever
4. Reset `displayStartTime` when city/day/filter context changes

## Key Facts
- All events (up to 5000) are already fetched client-side
- `limit` on XMLUI List is a client-side truncation, not a fetch limit
- The perf issue is React virtual DOM diffing per keystroke, not DOM rendering (virtualization handles that)
- `window._lastFilteredCount` avoids the AppState reactive loop gotcha (lives on window, not in AppState)
- Time-cursor paging is useful when the first 50 events do not get past the current evening; `MORE` should advance time, not just count
