import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Format date for ICS (YYYYMMDDTHHMMSSZ)
function formatICSDate(isoString: string): string {
  // Remove timezone info and format as ICS date
  const d = new Date(isoString);
  return d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

// Escape text for ICS format
function escapeICS(text: string | null): string {
  if (!text) return "";
  return text
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\n/g, "\\n");
}

// Generate ICS content from events
function generateICS(events: any[], calendarName: string): string {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Community Calendar//My Picks//EN",
    `X-WR-CALNAME:${escapeICS(calendarName)}`,
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
  ];

  for (const event of events) {
    lines.push("BEGIN:VEVENT");
    lines.push(`UID:pick-${event.id}@community-calendar`);
    lines.push(`DTSTAMP:${formatICSDate(new Date().toISOString())}`);
    lines.push(`DTSTART:${formatICSDate(event.start_time)}`);
    if (event.end_time) {
      lines.push(`DTEND:${formatICSDate(event.end_time)}`);
    }
    lines.push(`SUMMARY:${escapeICS(event.title)}`);
    if (event.location) {
      lines.push(`LOCATION:${escapeICS(event.location)}`);
    }
    if (event.description) {
      lines.push(`DESCRIPTION:${escapeICS(event.description)}`);
    }
    if (event.url) {
      lines.push(`URL:${event.url}`);
    }
    lines.push("END:VEVENT");
  }

  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Get token from query params
    const url = new URL(req.url);
    const token = url.searchParams.get("token");

    if (!token) {
      return new Response(JSON.stringify({ error: "Missing token parameter" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Create Supabase client with service role for database access
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Validate token and get user_id
    const { data: tokenData, error: tokenError } = await supabase
      .from("feed_tokens")
      .select("user_id")
      .eq("token", token)
      .single();

    if (tokenError || !tokenData) {
      return new Response(JSON.stringify({ error: "Invalid token" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const userId = tokenData.user_id;

    // Get user's picks with event details
    const { data: picks, error: picksError } = await supabase
      .from("picks")
      .select(`
        event_id,
        events (
          id,
          title,
          start_time,
          end_time,
          location,
          description,
          url,
          source
        )
      `)
      .eq("user_id", userId);

    if (picksError) {
      console.error("Error fetching picks:", picksError);
      return new Response(JSON.stringify({ error: "Failed to fetch picks" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Extract events from picks (flatten the join)
    const events = (picks || [])
      .map((p: any) => p.events)
      .filter((e: any) => e !== null)
      .sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));

    // Generate ICS
    const ics = generateICS(events, "My Picks - Community Calendar");

    // Generate ETag from content hash for cache validation
    const encoder = new TextEncoder();
    const data = encoder.encode(ics);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const etag = `"${hashArray.slice(0, 8).map(b => b.toString(16).padStart(2, '0')).join('')}"`;

    return new Response(ics, {
      headers: {
        ...corsHeaders,
        "Content-Type": "text/calendar; charset=utf-8",
        "Content-Disposition": 'attachment; filename="my-picks.ics"',
        "Cache-Control": "no-cache, must-revalidate",
        "ETag": etag,
        "Last-Modified": new Date().toUTCString(),
      },
    });
  } catch (error) {
    console.error("Error:", error);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
