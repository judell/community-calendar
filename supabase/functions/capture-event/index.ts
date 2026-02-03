import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const EXTRACTION_PROMPT = `Extract event details from this poster image. Return ONLY valid JSON, no other text:
{
  "title": "event name",
  "start_time": "ISO8601 datetime (YYYY-MM-DDTHH:MM:SS)",
  "end_time": "ISO8601 datetime or null",
  "location": "venue/address or null",
  "description": "brief description or null",
  "url": "website if visible or null"
}

Rules:
- If you cannot determine the year, assume 2025 or 2026 based on context (current year is 2025).
- If you cannot determine the exact time, make a reasonable guess (e.g., evening events at 19:00).
- If the date/time is completely unreadable, set start_time to null.
- Keep description brief (1-2 sentences max).
- Return ONLY the JSON object, no markdown or explanation.`;

async function extractEventFromImage(imageBytes: Uint8Array, mediaType: string): Promise<any> {
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!anthropicKey) {
    throw new Error("ANTHROPIC_API_KEY not configured");
  }

  // Convert bytes to base64
  const base64 = btoa(String.fromCharCode(...imageBytes));

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
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: {
                type: "base64",
                media_type: mediaType,
                data: base64,
              },
            },
            {
              type: "text",
              text: EXTRACTION_PROMPT,
            },
          ],
        },
      ],
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

  // Parse the JSON response
  try {
    return JSON.parse(textContent.text);
  } catch (e) {
    // Try to extract JSON from the response if it has extra text
    const jsonMatch = textContent.text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    throw new Error("Failed to parse event JSON from response");
  }
}

async function commitEvent(
  supabase: any,
  event: any,
  userId: string
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
      source: "poster_capture",
      source_uid: sourceUid,
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

    // Handle multipart/form-data (from Actions.upload)
    if (contentType.includes("multipart/form-data")) {
      const formData = await req.formData();
      const mode = formData.get("mode") as string;
      const file = formData.get("file") as File;

      if (mode === "extract") {
        if (!file) {
          return new Response(JSON.stringify({ error: "Missing file" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          });
        }

        const imageBytes = new Uint8Array(await file.arrayBuffer());
        const mediaType = file.type || "image/jpeg";
        const extractedEvent = await extractEventFromImage(imageBytes, mediaType);

        return new Response(JSON.stringify({ event: extractedEvent }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
    }

    // Handle application/json (for commit mode and legacy base64 extract)
    if (contentType.includes("application/json")) {
      const body = await req.json();
      const { mode, image, media_type, event } = body;

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

        const result = await commitEvent(supabase, event, userData.user.id);

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
