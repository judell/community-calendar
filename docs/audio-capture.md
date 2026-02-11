# Audio Capture

Capture event details by speaking into your phone or uploading an audio file. The system transcribes your speech and extracts structured event data using AI.

## Architecture

A two-step pipeline handles audio:

1. **Whisper** (OpenAI) transcribes audio to text
2. **Claude** (Anthropic) extracts structured event JSON from the transcript

This approach was chosen because the Claude Messages API does not support audio input natively. The browser's MediaRecorder API captures microphone audio as WebM (Chrome) or MP4 (Safari), which Whisper handles directly.

## How It Works

From the app, click the play icon (visible to authorized users). Choose "Select Audio File" to upload a recording, or "Record from Microphone" to speak directly. After recording, tap "Stop and Process" to send audio to the `capture-event` edge function.

The edge function returns extracted event fields (title, date, time, location, description, url) plus the raw Whisper transcript. Both are saved to the database when the user confirms.

## Prompt Engineering

The extraction prompt includes several contextual hints:

- **Year**: Hardcoded to 2026 to prevent defaulting to training-data years
- **Day inference**: If you say "Tuesday ride," it maps to the next upcoming Tuesday
- **Recurrence**: Mentions of "weekly" or named days produce recurrence descriptions
- **Duration**: Unknown end times get reasonable estimates (1hr for meetups, 2-3hr for concerts)
- **Provenance URLs**: Mentioning "check Facebook" or "it's on Meetup" generates a search URL for that platform

## ICS Integration

When saving a captured event, recurrence rules (RRULE) and URLs flow through to both the .ics download and Google Calendar link. The `my-picks` edge function also includes RRULEs in its calendar feed.

## Secrets Required

- `ANTHROPIC_API_KEY` — Supabase edge function secret
- `OPENAI_API_KEY` — Supabase edge function secret

## Key Files

- `supabase/functions/capture-event/index.ts` — edge function (v20)
- `components/AudioCaptureDialog.xmlui` — UI dialog
- `helpers.js` — `startRecording`, `stopRecording`, `getRecordingFile`
