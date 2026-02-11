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

- **Today's date**: Injected dynamically (e.g., `Today's date is 2026-02-10`). Earlier versions only said "the current year is 2026" — without the full date, the model couldn't compute "next Tuesday" and consistently returned January 7 (a Wednesday). Even saying "assume 2025 or 2026" confused the model into picking 2025. The lesson: give the model exactly the date, computed at runtime, and mention no other dates.
- **Day inference**: If you say "Tuesday ride," it maps to the next upcoming Tuesday from today's date
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

`detectRecurrence` accepts multiple arguments (description, title) and returns on the first frequency match. Crucially, when "weekly" is found in one argument but no day name appears there, it now scans **all** arguments for a day. This handles the common case where the description says "Weekly bike ride meetup" and the title says "Taco Tuesday Ride" — without cross-referencing, the RRULE would be `FREQ=WEEKLY` with no `BYDAY`.

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

The audio capture feature evolved through rapid iteration (v17–v24 of the capture-event edge function):

| Version | Changes |
|---------|---------|
| v17 | Initial audio support: Whisper transcription + Claude extraction |
| v18 | Fixed year prompt: "always use 2026" instead of "assume 2025 or 2026" |
| v19 | Save transcript to DB, return transcript in extract response |
| v20 | Estimate end times, pass rrule/url to calendar exports |
| v21 | Save city from client, fix detectRecurrence day detection, fix "on Tuesdays" pattern |
| v22 | Fix Facebook URL template: `/search/top/?q=` not `/search/events?q=` |
| v23 | Append transcript to event description with "Transcribed audio from {username}:" heading |
| v24 | Inject dynamic today's date in prompt; fix record mode missing transcript/url |

Client-side fixes (not edge function versions, deployed via GitHub Pages):

| Commit | Changes |
|--------|---------|
| Include transcript in ICS | AddToCalendar description now appends transcript to match DB |
| Fix undefined UID in ICS | Use `savedPickId` (server-returned event ID) as fallback for captured events |
| Fix RRULE missing BYDAY | `detectRecurrence` scans all arguments (description + title) for day name |

Key lessons learned:
- **Date, not just year**: Telling the model "the current year is 2026" isn't enough — it needs today's full date to compute "next Tuesday." Without it, all five test captures returned January 7 (a Wednesday, not even a Tuesday). The fix: `getSharedRules()` computes `new Date().toISOString().substring(0, 10)` at request time and injects it into the prompt.
- **Year hallucination**: Any mention of a wrong year in the prompt causes the model to use it. v17 said "assume 2025 or 2026" and the model picked 2025 every time.
- **Recurrence day detection**: Three iterations. First, "Weekly bike ride on Tuesdays" matched "weekly" before reaching "on Tuesdays" — fixed by also scanning for day names when "weekly" is matched within the same text. Second, "Weekly bike ride meetup" (description) + "Taco Tuesday Ride" (title) — "weekly" matched in description with no day, and `detectRecurrence` returned without checking the title. Fixed by making the multi-argument wrapper scan all arguments for a day name when WEEKLY has empty days.
- **Two code paths, same dialog**: AudioCaptureDialog has file-upload and record modes. The file-upload path included `url` and `transcript` in the pickEvent object; the record path didn't. This caused null transcript/city/url in the DB for microphone recordings. Both paths must set identical fields.
- **Data flow through capture path**: The captured event path (no event ID) was missing enrichment creation, city assignment, and transcript/url passthrough — each had to be wired separately.
- **GitHub Pages deploy lag**: Client code changes require push → CI build → Pages deploy (1-2 min). Tests before deployment use old client code and produce confusing results.

## Secrets Required

- `ANTHROPIC_API_KEY` — Supabase edge function secret (Claude extraction)
- `OPENAI_API_KEY` — Supabase edge function secret (Whisper transcription)

## Key Files

- `supabase/functions/capture-event/index.ts` — edge function (v24)
- `components/AudioCaptureDialog.xmlui` — UI dialog (file picker, microphone recording)
- `components/PickEditor.xmlui` — review/edit form, commit, enrichment creation
- `components/AddToCalendar.xmlui` — ICS download + Google Calendar link (includes RRULE)
- `helpers.js` — `startRecording`, `stopRecording`, `getRecordingFile`, `detectRecurrence`, `buildGoogleCalendarUrl`
- `docs/audio-input.md` — original implementation plan (superseded by this doc)
