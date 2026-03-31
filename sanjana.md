# Event Concierge: Handoff Doc

## What it is

A chat-in-modal feature where users talk to Claude about what events they're looking for. Claude acts as a concierge: asks about interests, timing, and location, then recommends matching events rendered as EventCards inside the modal.

## What was built

### Frontend (XMLUI)

- **Icon**: `bot-message-square` from Lucide, added to IconRow (gated on auth)
- **ChatDialog.xmlui**: Modal with scrollable message area (400px, overflowY scroll), user messages in italic Text, assistant messages in Markdown, recommended events as EventCards via nested Items
- **APICall**: POSTs to `chat-events` edge function with conversation history and city
- **Trace**: `window.traceChatConcierge()` in index.html emits `chatConcierge` app:trace entries with event count and titles

### Backend (Supabase Edge Function)

- **chat-events v9**: Queries next 30 days of events for the city (title, start_time, end_time, location, category, source, url), sends to Claude with a concierge system prompt
- **Model**: Claude Haiku 4.5 (~4.5s response time)
- **JSON protocol**: Claude returns `{"reply": "...", "recommended_titles": ["..."]}`, edge function matches titles against queried events, returns `{reply, events}` with full event objects
- **Robust parsing**: Handles code fences, escaped quotes, fallback extraction

### Files changed

| File | What |
|------|------|
| `xmlui/icons/l-bot-message-square.svg` | Lucide icon |
| `xmlui/config.json` | Icon resource registration |
| `xmlui/components/IconRow.xmlui` | Chat icon in toolbar |
| `xmlui/components/ChatDialog.xmlui` | Chat modal UI |
| `xmlui/Main.xmlui` | ChatDialog inclusion |
| `xmlui/index.html` | `traceChatConcierge` helper |
| `supabase/functions/chat-events/index.ts` | Edge function |

## Sonnet vs Haiku

We tried both during the session:
- **Sonnet**: Better quality recommendations, but 9-13s per turn. Also more reliable at returning valid JSON.
- **Haiku**: 4.5s per turn, but weaker relevance (boat cruises for hiking queries) and sometimes returns raw JSON instead of parsing correctly (escaped quotes in titles broke JSON.parse; fixed with fallback extraction).

A next step could be letting the user choose, or using Haiku for early conversational turns and Sonnet for final recommendations.

## Trace instrumentation

- `window.traceChatConcierge(events)` in `index.html` calls `window.xsTraceEvent('chatConcierge', { eventCount, titles })`
- Emits `app:trace` entries visible in trace-tools Inspector alongside engine events
- Important: `.map(function(e) { ... })` doesn't work in inline XMLUI expressions. The fix was moving the trace call to a window function in index.html (per rule 6: keep complex functions out of XMLUI)
- Confirmed working in xs-trace-20260330T235858: entry 38 shows `chatConcierge` with 7 events

## Known issues

### Prompt quality
- **Relevance**: Recommendations are often off-target. "Hiking" returned boat cruises and bicycle rides. The prompt needs better instruction about matching user intent to event content, not just category labels.
- **Title matching**: Exact title match is brittle. Claude sometimes modifies titles (adds quotes, truncates). Fuzzy matching or ID-based matching would be more reliable.
- **Over-asking vs under-asking**: Tuned toward "recommend eagerly" but still sometimes asks unnecessary follow-ups when it has enough context.

### UI
- **Enter-to-send not implemented**: Form approach added Cancel/Save buttons (ModalDialog behavior). TextBox doesn't expose onKeyDown. Needs a different approach.
- **No visual distinction for user vs assistant**: Just italic vs normal. Could use background colors or alignment.
- **IconRow reverted on main**: Due to xmlui-org/xmlui#3185 (Select dropdownHeight bug). Branch has the icon; main does not.

### Architecture
- **Events re-fetched every turn**: The edge function queries Supabase on every message. Could cache per conversation.
- **All events in system prompt**: ~1000 events as pipe-delimited text. Works for Haiku's context window but costly. Could pre-filter or summarize.
- **No auth on edge function**: `verify_jwt: false`. Should gate on auth to control API costs.
- **Message cleanup**: Extra fields (events array) on messages must be stripped before sending to Anthropic API. Fixed with `cleanMessages` map in edge function.

## What to try next

1. **Better prompt engineering**: Include event descriptions in the summary so Claude can match on content, not just titles. Add negative examples ("do not recommend cycling events for someone who wants to hike").
2. **Fuzzy title matching**: Use substring/similarity matching instead of exact lowercase match.
3. **Model selection**: Let user choose Sonnet (quality) vs Haiku (speed), or auto-escalate.
4. **Enter-to-send**: Investigate code-behind keydown handler or a custom component wrapper.
5. **Cost controls**: Add auth requirement, rate limiting, or per-user quotas.
