# Search and Performance

Client-side search filters events as you type. The search icon in the header toggles a search box with auto-focus. Searches match against title, location, source, and description.

## Description Snippets

Each event card shows a short snippet — ideally the single best sentence that describes the event. The `getSnippet(description, title)` function in `helpers.js` uses a scoring approach to find it:

1. **Prepare text** — preserve HTML line breaks (`<br>`, `</p>`, `</li>`) as newlines before stripping tags; strip URLs and markdown artifacts; fix smashed words from bad HTML cleanup (`"ZwiftJoin"` → `"Zwift Join"`); replace closing tags with spaces to prevent word smashing
2. **Score each candidate line** (and sentence fragments within long lines):
   - **Reward** sentence-like signals: punctuation (`.!?`), function words (`the, a, and, for, with`), descriptive verbs (`join, learn, discover, explore, celebrate`)
   - **Penalize** pricing/money (`$`, `fee`, `admission`), digit-heavy lines (6+ digits), very short non-sentences, lines that just repeat the event title, and lines without articles or verbs
   - **Hard-reject** lines matching CTA prefixes (`buy`, `register`, `sign up`, `back to`), lines containing meeting logistics (`zoom`, `meeting id`, `passcode`, `webex`), policy text (`prohibited`, `not permitted`), and cross-event boilerplate
3. **Salvage label-prefixed lines** — if a line starts with a `Label: value` pattern (1-3 words before a colon), strip the label and keep the remainder *if* it's at least 30 characters and contains function words (catches real descriptions hiding behind `Presenter:` or `About:` prefixes)
4. **Pick the highest-scoring candidate**, truncate to ~100 characters at a word boundary

When searching, a separate `getDescriptionSnippet(description, term)` shows where the search term matched in the description, with the match in **bold**.

### Snippet Quality

Snippet quality is an ongoing effort refined iteratively against real event data. The report generator (`scripts/snippet_report.py`) evaluates `getSnippet` across all cities and writes `docs/snippet-report.md` — a full listing of every event's title and snippet (or why it has none).

To regenerate the report after changing snippet logic:

```bash
python3 scripts/snippet_report.py
# Writes docs/snippet-report.md
```

The report helps identify:
- **False positives** — snippets that aren't useful descriptions (metadata, boilerplate, policy text)
- **False negatives** — events with real descriptions that got rejected
- **Coverage** — percentage of events with snippets per city (currently 60-92% depending on city)

The evaluation prompt (`docs/snippet-eval-prompt.md`) can be given to any LLM to review the report and recommend improvements. This is how the scoring approach was developed — iterating between report generation, LLM evaluation, and logic refinement.

## List Virtualization

The List uses three key props:
```xmlui
<List data="{window.filterEvents(window.dedupeEvents([...]), filterTerm)}"
      fixedItemSize="true" limit="50">
```

### How the Search Chain Works

Data flows through several stages on every keystroke:

1. **DataSource fetch** — up to 5000 events from Supabase (one-time)
2. **`dedupeEvents()`** — O(n) grouping pass with a simple cache (`helpers.js:141`)
3. **`filterEvents()`** — O(n) scan across title, location, source, and description (`helpers.js:46`). Runs on **every keystroke** because `filterTerm` is a reactive var
4. **`limit="50"`** — XMLUI truncates the filtered result to 50 items before handing them to the virtualizer
5. **Virtualization** — only the ~10-15 items visible in the viewport get DOM nodes; the other 35-40 are "virtual" (no DOM cost)
6. **`fixedItemSize="true"`** — lets the virtualizer measure one card and assume all are that height

Search gets snappier as you type because the filter output shrinks, so the List receives fewer items and React diffs less. The `limit` is **not** about DOM nodes — virtualization handles that. It's about **React's virtual DOM diffing**: each item, even if not rendered to the DOM, is a React element that must be created, diffed, and reconciled on every keystroke.

### Why limit=50

Measured data shows limit=50 delivers a 38% improvement on the first keystroke vs limit=100 (859ms → 531ms). The tradeoff — users can only scroll 50 events before searching — is barely a tradeoff in practice. Search is one click (the magnifying glass) and one keystroke away.

| Limit | Pros | Cons |
|-------|------|------|
| **50** (current) | 38% faster search; best responsiveness | Users scroll 50 events before needing to search |
| **100** | More scrollable | ~100 virtual elements tracked; first keystroke ~859ms |
| **200+** | More browsable | Heavier reconciliation on each keystroke; noticeable lag |

### fixedItemSize Tradeoffs

EventCards have **variable actual heights** (wrapping titles, conditional location/description/snippet). `fixedItemSize="true"` tells the virtualizer to measure the first card and assume all match.

| | `fixedItemSize="true"` (current) | `fixedItemSize="false"` |
|---|---|---|
| **Scroll perf** | Best — no per-item measurement | Slightly worse |
| **Scrollbar accuracy** | May drift with variable heights | Accurate (progressively) |
| **Visual correctness** | Cards may clip or show extra whitespace | Each card gets its true height |

At limit=50, measurement shows **no performance difference** between true and false. We could switch to `false` for accurate scrollbar positioning with no cost.

### Fetch Size vs. Virtualization

These are independent concerns. Whether Supabase returns 200 or 5000 events, the virtualizer always sees at most 50. The fetch size affects the JS filter scan cost (2-3ms — negligible), not the rendering cost.

### Measurement and Optimization

App-level measurement using [trace-tools](https://github.com/xmlui-org/trace-tools) confirms that `filterEvents` takes 2-3ms — the bottleneck is engine-internal reactive overhead and React reconciliation, not app-level code. The only effective app-level lever is `limit` (lowering from 100 to 50 cut the latency roughly in half). See the [xsTrace case study](https://github.com/xmlui-org/trace-tools#opt-in-app-level-timing-with-xstrace) for the full investigation, measurement methodology, and engine analysis.

XMLUI List docs: [List](https://docs.xmlui.org/components/List) | [Items](https://docs.xmlui.org/components/Items) (non-virtualized alternative)

The XMLUI inspector (cog icon → `xs-diff.html`) shows event traces, state changes, and API calls. Requires `xsVerbose: true` in `config.json`.
