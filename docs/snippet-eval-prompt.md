# Snippet Logic Evaluation

## Context

This community calendar app aggregates events from dozens of sources per city (ICS feeds, scrapers, APIs). Each event has a title, date, location, source attribution, and a free-text `description` field.

The `description` field is messy. It comes from many different sources and contains a mix of:
- Actual event descriptions ("Join us for an immersive audiovisual experience...")
- Metadata lines ("Instructor: Suzanne Carson", "Price: $85", "Doors: 7pm")
- Navigation/CTA text ("Back to All Shows", "Buy Tickets", "Register")
- URLs, HTML fragments, markdown artifacts
- Venue/room names ("Southern Cross")
- Press release boilerplate ("Date: For Immediate Release")

We display a short **snippet** on each event card — ideally the single best sentence that tells you what the event is about. The snippet should make you want to click for more detail.

## Current Logic

The current `getSnippet()` function in `helpers.js` (reproduced below) takes this approach:

1. Strip HTML, URLs, markdown artifacts
2. Split into lines
3. Skip lines that match a "label: value" pattern (1-3 words before a colon)
4. Skip lines matching a short blocklist of CTA/navigation prefixes
5. Skip lines under 15 characters
6. Among surviving candidates, prefer the first line that's at least 40 characters
7. Truncate to ~100 characters at a word boundary

```javascript
function getSnippet(description) {
  if (!description) return null;
  var text = description;
  if (/<[a-z][\s\S]*>/i.test(text)) {
    var doc = new DOMParser().parseFromString(text, 'text/html');
    text = doc.body.textContent || '';
  }
  text = text.replace(/https?:\/\/\S+/g, '');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/\\([*_\[\](){}+#>|`~])/g, '$1');
  text = text.replace(/[\t\r]+/g, ' ').replace(/ {2,}/g, ' ');

  var lines = text.split('\n').map(function(l) { return l.trim(); }).filter(Boolean);

  var labelPattern = /^\w+(\s+\w+){0,2}\s*:/;
  var shortJunkPattern = /^(back to |buy |get |view |click |tap |see all|show |sold out|wait ?list|loading|free$|-free$|\$\d)/i;
  var candidates = [];
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].length <= 15) continue;
    if (labelPattern.test(lines[i])) continue;
    if (shortJunkPattern.test(lines[i])) continue;
    candidates.push(lines[i]);
  }

  var line = null;
  for (var i = 0; i < candidates.length; i++) {
    if (candidates[i].length >= 40) { line = candidates[i]; break; }
  }
  if (!line && candidates.length) line = candidates[0];
  if (!line) return null;

  if (line.length <= 100) return line;
  var cut = line.lastIndexOf(' ', 100);
  if (cut < 40) cut = 100;
  var snippet = line.substring(0, cut).replace(/[\s(,\-;:]+$/, '');
  return snippet + '...';
}
```

## Your Task

Review `docs/snippet-report.md` which shows the output of this logic across ~15,000 events in 6 cities. For each event you'll see:

- **With snippets**: `- **Event Title** — snippet text`
- **Without snippets**: `- **Event Title** — raw description start` (or "no description")

Evaluate:

1. **False positives**: Snippets that are NOT good descriptions — metadata, pricing, dates, boilerplate, or nonsensical fragments that slipped through the filters.

2. **False negatives**: Events in the "without snippets" section that DO have a usable description in their raw text, but the current logic rejected all lines.

3. **Propose improvements** to the logic that retain generality. We want rules that work across all cities and source types, not city-specific or source-specific heuristics. The label pattern (`^\w+(\s+\w+){0,2}\s*:`) was our key insight — it catches dozens of metadata patterns with one rule. We want more insights like that.

4. **Consider whether "first long line" is the right strategy**, or whether scoring/ranking candidates would produce better results. For example: lines with articles and prepositions are more likely to be sentences than fragments. Lines that repeat the event title are less useful than lines that add new information.

Present your findings as:
- A list of specific problematic snippets you found (with city and title)
- A list of specific missed opportunities you found
- Concrete code suggestions (modified `getSnippet` function or additional heuristics)
