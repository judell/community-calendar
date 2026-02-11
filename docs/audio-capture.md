# Audio Capture

Capture event details by speaking into your phone or uploading an audio file. The system transcribes your speech and extracts structured event data using AI.

## Architecture

A two-step pipeline handles audio:

1. **Whisper** (OpenAI) transcribes audio to text
2. **Claude** (Anthropic) extracts structured event JSON from the transcript

This approach was chosen because the Claude Messages API does not support audio input natively. The browser's MediaRecorder API captures microphone audio as WebM (Chrome) or MP4 (Safari), which Whisper handles directly.

## How It Works

From the app, click the play icon (visible to authorized users). Choose "Select Audio File" to upload a recording, or "Record from Microphone" to speak directly. After recording, tap "Stop and Process" to send audio to the `capture-event` edge function.

The edge function returns extracted event fields (title, date, time, location, description, url) plus the raw Whisper transcript. The user reviews and edits the extracted fields in the PickEditor form. When confirmed:

- The event is inserted into the `events` table with `source='poster_capture'`
- The transcript is saved in the `transcript` column
- The transcript is also appended to the event description with a heading: "Transcribed audio from {username}:"
- The user's city (from the URL's `?city=` param) is saved in the `city` column
- A pick is created linking the user to the event
- If recurrence is set, an enrichment is created with the RRULE

## Prompt Engineering

The extraction prompt includes several contextual hints:

- **Year**: Hardcoded to 2026 to prevent defaulting to training-data years. Earlier attempts that said "assume 2025 or 2026" confused the model — mentioning any other year causes it to pick that year instead.
- **Day inference**: If you say "Tuesday ride," it maps to the next upcoming Tuesday
- **Recurrence**: Mentions of "weekly" or named days produce recurrence descriptions
- **Duration**: Unknown end times get reasonable estimates (1hr for meetups, 2-3hr for concerts)
- **Provenance URLs**: Mentioning "check Facebook" or "it's on Meetup" generates a search URL for that platform. Facebook uses `/search/top/?q=` (not `/search/events?q=` which doesn't work).

## Recurrence Detection

Two layers detect recurrence from audio:

**Server-side** (Claude prompt): The extraction prompt tells Claude to note recurrence in the description field (e.g., "Weekly on Tuesdays").

**Client-side** (`detectRecurrence()` in `helpers.js`): When the PickEditor opens, it scans the extracted description and title for recurrence language:
- `"every Tuesday"` or `"on Tuesdays"` → Weekly, day=TU
- `"weekly"` or `"every week"` → Weekly (also scans for a day name in surrounding text)
- `"1st Tuesday of every month"` → Monthly, ordinal=1, day=TU

If detected, the recurrence section auto-expands with frequency and days pre-selected. The user can adjust before saving.

## ICS Integration

When saving a captured event, recurrence rules (RRULE) and URLs flow through to:
- The `.ics` download (RRULE, DTEND, URL fields in the VEVENT)
- The Google Calendar link (`recur=RRULE:FREQ=WEEKLY;BYDAY=TU` parameter)
- The `my-picks` edge function ICS feed

This required fixing several data flow gaps:
- PickEditor's AddToCalendar component now receives `rrule` and `url` props
- `buildGoogleCalendarUrl()` now includes the `recur` parameter
- Captured events (no existing event ID) now create enrichments via a chained API call in `captureApi.onSuccess`

## Development History

The audio capture feature evolved through rapid iteration (v17–v23 of the capture-event edge function):

| Version | Changes |
|---------|---------|
| v17 | Initial audio support: Whisper transcription + Claude extraction |
| v18 | Fixed year prompt: "always use 2026" instead of "assume 2025 or 2026" |
| v19 | Save transcript to DB, return transcript in extract response |
| v20 | Estimate end times, pass rrule/url to calendar exports |
| v21 | Save city from client, fix detectRecurrence day detection, fix "on Tuesdays" pattern |
| v22 | Fix Facebook URL template: `/search/top/?q=` not `/search/events?q=` |
| v23 | Append transcript to event description with "Transcribed audio from {username}:" heading |

Key lessons learned:
- **Year hallucination**: Any mention of a wrong year in the prompt causes the model to use it. The fix was to remove all mention of other years.
- **Recurrence day detection**: "Weekly bike ride on Tuesdays" matched "weekly" first, returning `WEEKLY` with no day. Fixed by also scanning for day names when "weekly" is matched.
- **Data flow through capture path**: The captured event path (no event ID) was missing enrichment creation, city assignment, and transcript/url passthrough — each had to be wired separately.
- **GitHub Pages deploy lag**: Client code changes require push → CI build → Pages deploy (1-2 min). Tests before deployment use old client code and produce confusing results.

## Secrets Required

- `ANTHROPIC_API_KEY` — Supabase edge function secret (Claude extraction)
- `OPENAI_API_KEY` — Supabase edge function secret (Whisper transcription)

## Key Files

- `supabase/functions/capture-event/index.ts` — edge function (v23)
- `components/AudioCaptureDialog.xmlui` — UI dialog (file picker, microphone recording)
- `components/PickEditor.xmlui` — review/edit form, commit, enrichment creation
- `components/AddToCalendar.xmlui` — ICS download + Google Calendar link (includes RRULE)
- `helpers.js` — `startRecording`, `stopRecording`, `getRecordingFile`, `detectRecurrence`, `buildGoogleCalendarUrl`
- `docs/audio-input.md` — original implementation plan (superseded by this doc)
