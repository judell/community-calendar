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
    // RRULE for recurring events (from enrichment)
    if (event.rrule) {
      lines.push(`RRULE:${event.rrule}`);
    }
    lines.push(`SUMMARY:${escapeICS(event.title)}`);
    if (event.location) {
      lines.push(`LOCATION:${escapeICS(event.location)}`);
    }
    // Build description: original + curator notes
    let description = event.description || "";
    if (event.notes) {
      description = description
        ? `${description}\n\n--- Curator notes ---\n${event.notes}`
        : event.notes;
    }
    if (description) {
      lines.push(`DESCRIPTION:${escapeICS(description)}`);
    }
    if (event.url) {
      lines.push(`URL:${event.url}`);
    }
    // Categories from enrichment
    if (event.categories && event.categories.length > 0) {
      lines.push(`CATEGORIES:${event.categories.join(",")}`);
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
    // Get token and format from query params
    const url = new URL(req.url);
    const token = url.searchParams.get("token");
    const format = url.searchParams.get("format") || "ics";

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

    // Get user's picks with event details and enrichments
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

    // Get user's enrichments for these events
    const eventIds = (picks || []).map((p: any) => p.event_id).filter(Boolean);
    const { data: enrichments } = await supabase
      .from("event_enrichments")
      .select("*")
      .eq("curator_id", userId)
      .in("event_id", eventIds);

    // Create a map of enrichments by event_id
    const enrichmentMap = new Map(
      (enrichments || []).map((e: any) => [e.event_id, e])
    );

    if (picksError) {
      console.error("Error fetching picks:", picksError);
      return new Response(JSON.stringify({ error: "Failed to fetch picks" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Extract events from picks and merge with enrichments
    const events = (picks || [])
      .map((p: any) => {
        const event = p.events;
        if (!event) return null;
        const enrichment = enrichmentMap.get(event.id);
        return {
          ...event,
          // Enrichment overrides
          rrule: enrichment?.rrule || null,
          categories: enrichment?.categories || null,
          notes: enrichment?.notes || null,
          // Enrichment can override these if present
          description: enrichment?.description || event.description,
          location: enrichment?.location || event.location,
        };
      })
      .filter((e: any) => e !== null)
      .sort((a: any, b: any) => a.start_time.localeCompare(b.start_time));

    // Return JSON or ICS based on format parameter
    if (format === "json") {
      return new Response(JSON.stringify(events), {
        headers: {
          ...corsHeaders,
          "Content-Type": "application/json",
          "Cache-Control": "no-cache, must-revalidate",
        },
      });
    }

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
