# Audio Input: Implementation Plan

## Goal

Let users capture event info from audio (voice memos, radio ads, voicemails, etc.) the same way they can currently capture from poster images.

## Current State: Image Capture

```
Image → Claude API (one call) → event JSON → PickEditor → Supabase
```

Claude's Messages API supports `image` content blocks natively, so the entire flow is a single API call in the `capture-event` edge function.

## Problem

The Claude Messages API **does not support audio input**. Supported content block types are: `text`, `image`, `document`, `tool_use`, `tool_result`, `search_result`, `thinking`.

- [Messages API Reference](https://docs.anthropic.com/en/api/messages) — no audio content type
- [OpenAI SDK compatibility](https://docs.anthropic.com/en/api/openai-sdk) — "Audio input is not supported"

## Proposed Architecture

```
Audio file → Transcription → text → Claude API (text prompt) → event JSON → PickEditor
```

Two-step pipeline: transcribe first, then extract structured event data from the transcript.

## Transcription Options

| Option | Pros | Cons |
|--------|------|------|
| **OpenAI Whisper API** | Proven, accurate, simple REST API, $0.006/min | Extra API key, external dependency |
| **Browser Web Speech API** | Free, no server cost, no API key | Inconsistent across browsers, requires microphone permission for live recording, no file upload support in most browsers |
| **Deepgram** | Fast, accurate, REST API | Extra API key, less well-known |

**Recommendation:** OpenAI Whisper API. It handles file uploads via a simple multipart POST, supports mp3/mp4/wav/m4a/webm, and returns plain text. One additional secret to manage.

## Implementation Steps

### 1. Add Whisper API key as Supabase secret

```bash
# Via Supabase Dashboard: Settings → Edge Functions → Secrets
OPENAI_API_KEY=sk-...
```

### 2. Extend `capture-event` edge function

Add an `extractEventFromAudio()` function alongside the existing `extractEventFromImage()`:

```typescript
async function extractEventFromAudio(audioBytes: Uint8Array, mediaType: string): Promise<any> {
  const openaiKey = Deno.env.get("OPENAI_API_KEY");

  // Step 1: Transcribe via Whisper
  const ext = mediaType.split("/")[1] || "mp3";
  const formData = new FormData();
  formData.append("file", new File([audioBytes], `audio.${ext}`, { type: mediaType }));
  formData.append("model", "whisper-1");

  const whisperResponse = await fetch("https://api.openai.com/v1/audio/transcriptions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${openaiKey}` },
    body: formData,
  });
  const { text: transcript } = await whisperResponse.json();

  // Step 2: Extract event from transcript via Claude
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": anthropicKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      messages: [{
        role: "user",
        content: `Extract event details from this transcript of an audio recording.
Return ONLY valid JSON with the same format as the image extraction prompt.

Transcript:
${transcript}`
      }],
    }),
  });

  // ... parse response (same as image path)
}
```

Route in the main handler: detect audio MIME types (`audio/*`) and call `extractEventFromAudio` instead of `extractEventFromImage`.

### 3. Update CaptureDialog.xmlui

- Expand the file picker `accept` to include audio types: `image/*,audio/*`
- Show "Transcribing audio..." status when an audio file is selected (two-step process may be slower)
- The rest of the flow (PickEditor review/edit, commit) is unchanged

### 4. Update CaptureDialog icon/label

- Camera icon could become a more generic "capture" icon, or add a second microphone icon
- Tooltip: "Capture event from image or audio"

## What Stays the Same

- `commitEvent()` — unchanged
- PickEditor — unchanged (receives the same event JSON regardless of source)
- Supabase schema — captured events use `source: 'poster_capture'` (or add `'audio_capture'`)
- Auth flow — unchanged (user must be signed in)

## Cost Estimate

- Whisper: $0.006/minute — a 30-second voice memo costs ~$0.003
- Claude extraction: same as current image extraction (~$0.003 per call)
- Total per capture: ~$0.006

## Open Questions

1. **Live recording vs file upload?** File upload is simpler (select an audio file). Live recording via `MediaRecorder` API is possible but adds UI complexity (start/stop buttons, waveform display). Could start with file upload only.

2. **Source field value?** Use `poster_capture` for both image and audio? Or distinguish with `audio_capture`?

3. **Max audio length?** Whisper supports up to 25MB files. Should we cap at e.g. 2 minutes to control costs and relevance?

4. **Wait for Claude native audio?** If Anthropic adds audio input to the Messages API, the Whisper step becomes unnecessary. The two-step architecture means we could swap it out later with minimal changes.
