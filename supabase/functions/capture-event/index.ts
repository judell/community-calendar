import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-ue-client-tx-id",
};

const EVENT_JSON_FORMAT = `{
  "title": "event name",
  "start_time": "ISO8601 datetime (YYYY-MM-DDTHH:MM:SS)",
  "end_time": "ISO8601 datetime or null",
  "location": "venue/address or null",
  "description": "brief description or null",
  "url": "website if visible or null"
}`;

function getSharedRules(): string {
  const today = new Date().toISOString().substring(0, 10);
  return `Rules:
- Today's date is ${today}. Use this to calculate upcoming dates (e.g., "next Tuesday" means the next Tuesday on or after today).
- If you cannot determine the exact time, make a reasonable guess (e.g., evening events at 19:00).
- If end_time is unknown, estimate a reasonable duration (e.g., 1 hour for meetups, 2-3 hours for concerts/festivals).
- If the date/time is completely unreadable, set start_time to null.
- Keep description brief (1-2 sentences max).
- Return ONLY the JSON object, no markdown or explanation.`;
}

function getImageExtractionPrompt(): string {
  return `Extract event details from this poster image. Return ONLY valid JSON, no other text:
${EVENT_JSON_FORMAT}

${getSharedRules()}`;
}

function getAudioExtractionPrompt(): string {
  return `Extract event details from this transcript of an audio recording (e.g., a voice memo, radio ad, or voicemail about an event). Return ONLY valid JSON, no other text:
${EVENT_JSON_FORMAT}

${getSharedRules()}
- The transcript may contain filler words, false starts, or informal speech — extract the key event details.
- If multiple events are mentioned, extract only the first/primary one.
- If a day of the week is mentioned or implied (e.g., "Thursday night trivia", "Saturday morning farmers market"), set start_time to the NEXT upcoming occurrence of that day.
- If the event sounds recurring (e.g., "every week", "weekly", a named day implying regularity), mention the recurrence in the description (e.g., "Weekly on Thursdays").
- If the speaker mentions where to find more info (e.g., "check meetup for details", "it's on eventbrite", "search Facebook for downtown art walk"), construct a plausible search URL for the url field:
  - Facebook: https://www.facebook.com/search/top/?q={event+name+city}
  - Meetup: https://www.meetup.com/find/?keywords={event+name}&location={city}
  - Eventbrite: https://www.eventbrite.com/d/{state}--{city}/{event-name}
  - Generic: https://www.google.com/search?q={event+name+city}
- If no source is mentioned, leave url as null.`;
}

function parseEventJson(text: string): any {
  try {
    return JSON.parse(text);
  } catch (e) {
    // Try to extract JSON from the response if it has extra text
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    throw new Error("Failed to parse event JSON from response");
  }
}

async function callClaude(content: any[]): Promise<any> {
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!anthropicKey) {
    throw new Error("ANTHROPIC_API_KEY not configured");
  }

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
      messages: [{ role: "user", content }],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Anthropic API error:", errorText);
    throw new Error(`Anthropic API error: ${response.status}`);
  }

  const result = await response.json();
  const textContent = result.content?.find((c: any) => c.type === "text");
  if (!textContent?.text) {
    throw new Error("No text response from Claude");
  }

  return parseEventJson(textContent.text);
}

async function extractEventFromImage(imageBytes: Uint8Array, mediaType: string): Promise<any> {
  // Convert bytes to base64 (chunked to avoid stack overflow on large images)
  let binary = '';
  const chunkSize = 8192;
  for (let i = 0; i < imageBytes.length; i += chunkSize) {
    const chunk = imageBytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  const base64 = btoa(binary);

  return callClaude([
    {
      type: "image",
      source: { type: "base64", media_type: mediaType, data: base64 },
    },
    { type: "text", text: getImageExtractionPrompt() },
  ]);
}

async function transcribeAudio(audioBytes: Uint8Array, mediaType: string): Promise<string> {
  const openaiKey = Deno.env.get("OPENAI_API_KEY");
  if (!openaiKey) {
    throw new Error("OPENAI_API_KEY not configured");
  }

  // Map MIME type to file extension for Whisper
  const extMap: Record<string, string> = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "mp4",
    "audio/m4a": "m4a",
    "audio/x-m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
  };
  const ext = extMap[mediaType] || "mp3";

  const formData = new FormData();
  formData.append("file", new File([audioBytes], `audio.${ext}`, { type: mediaType }));
  formData.append("model", "whisper-1");

  const response = await fetch("https://api.openai.com/v1/audio/transcriptions", {
    method: "POST",
    headers: { "Authorization": `Bearer ${openaiKey}` },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Whisper API error:", errorText);
    throw new Error(`Whisper API error: ${response.status}`);
  }

  const result = await response.json();
  if (!result.text) {
    throw new Error("No transcript returned from Whisper");
  }

  console.log("Transcript:", result.text.substring(0, 200));
  return result.text;
}

async function extractEventFromAudio(audioBytes: Uint8Array, mediaType: string): Promise<{ event: any; transcript: string }> {
  const transcript = await transcribeAudio(audioBytes, mediaType);

  const event = await callClaude([
    {
      type: "text",
      text: `${getAudioExtractionPrompt()}\n\nTranscript:\n${transcript}`,
    },
  ]);

  return { event, transcript };
}

async function commitEvent(
  supabase: any,
  event: any,
  userId: string,
  transcript?: string
): Promise<{ event_id: number }> {
  // Generate unique source_uid
  const sourceUid = `poster_capture:${userId}:${crypto.randomUUID()}`;

  // Insert into events table
  const { data: eventData, error: eventError } = await supabase
    .from("events")
    .insert({
      title: event.title,
      start_time: event.start_time,
      end_time: event.end_time || null,
      location: event.location || null,
      description: event.description || null,
      url: event.url || null,
      city: event.city || null,
      source: "poster_capture",
      source_uid: sourceUid,
      transcript: transcript || null,
    })
    .select("id")
    .single();

  if (eventError) {
    console.error("Error inserting event:", eventError);
    throw new Error(`Failed to insert event: ${eventError.message}`);
  }

  // Insert into picks table
  const { error: pickError } = await supabase.from("picks").insert({
    user_id: userId,
    event_id: eventData.id,
  });

  if (pickError) {
    console.error("Error inserting pick:", pickError);
    throw new Error(`Failed to insert pick: ${pickError.message}`);
  }

  return { event_id: eventData.id };
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  try {
    const contentType = req.headers.get("content-type") || "";
    console.log("Content-Type:", contentType);

    // Handle multipart/form-data (from Actions.upload)
    if (contentType.includes("multipart/form-data")) {
      const formData = await req.formData();
      const mode = formData.get("mode") as string;

      // Find the file - Actions.upload uses the filename as the field name
      let file: File | null = null;
      formData.forEach((value, key) => {
        if (value instanceof File) {
          file = value;
        }
      });
      console.log("Mode:", mode, "File:", file?.name, "File type:", file?.type);

      if (mode === "extract") {
        if (!file) {
          return new Response(JSON.stringify({ error: "Missing file" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const fileBytes = new Uint8Array(await file.arrayBuffer());
        const mediaType = file.type || "image/jpeg";
        const isAudio = mediaType.startsWith("audio/");

        console.log(`Extracting event from ${isAudio ? "audio" : "image"}, mediaType: ${mediaType}, size: ${fileBytes.length}`);

        if (isAudio) {
          const { event: extractedEvent, transcript } = await extractEventFromAudio(fileBytes, mediaType);
          return new Response(JSON.stringify({ event: extractedEvent, transcript }), {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        } else {
          const extractedEvent = await extractEventFromImage(fileBytes, mediaType);
          return new Response(JSON.stringify({ event: extractedEvent }), {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }
      }
    }

    // Handle application/json (for commit mode and legacy base64 extract)
    if (contentType.includes("application/json")) {
      const body = await req.json();
      const { mode, image, media_type, event, transcript } = body;

      if (mode === "extract") {
        // Legacy base64 mode
        if (!image) {
          return new Response(JSON.stringify({ error: "Missing image parameter" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const mediaType = media_type || "image/jpeg";
        // Decode base64 to bytes
        const binaryString = atob(image);
        const imageBytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          imageBytes[i] = binaryString.charCodeAt(i);
        }
        const extractedEvent = await extractEventFromImage(imageBytes, mediaType);

        return new Response(JSON.stringify({ event: extractedEvent }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      } else if (mode === "commit") {
        // Commit mode: save event and create pick
        if (!event) {
          return new Response(JSON.stringify({ error: "Missing event parameter" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        if (!event.title || !event.start_time) {
          return new Response(
            JSON.stringify({ error: "Event must have title and start_time" }),
            {
              status: 400,
              headers: { ...corsHeaders, "Content-Type": "application/json" },
            }
          );
        }

        // Get user from auth header
        const authHeader = req.headers.get("Authorization");
        if (!authHeader?.startsWith("Bearer ")) {
          return new Response(JSON.stringify({ error: "Missing authorization" }), {
            status: 401,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const token = authHeader.replace("Bearer ", "");

        // Create Supabase client with service role for database writes
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        const supabase = createClient(supabaseUrl, supabaseServiceKey);

        // Verify the token and get user
        const supabaseAuth = createClient(
          supabaseUrl,
          Deno.env.get("SUPABASE_ANON_KEY")!
        );
        const { data: userData, error: authError } = await supabaseAuth.auth.getUser(token);

        if (authError || !userData?.user) {
          return new Response(JSON.stringify({ error: "Invalid authorization" }), {
            status: 401,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        // Append transcript to description if present
        if (transcript) {
          const username = userData.user.user_metadata?.user_name || userData.user.email || "unknown";
          event.description = (event.description || "") + `\n\nTranscribed audio from ${username}:\n${transcript}`;
        }

        const result = await commitEvent(supabase, event, userData.user.id, transcript);

        return new Response(JSON.stringify({ success: true, ...result }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
    }

    return new Response(
      JSON.stringify({ error: "Invalid request format or mode" }),
      {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ error: error.message || "Internal server error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
