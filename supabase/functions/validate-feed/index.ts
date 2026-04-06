const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-ue-client-tx-id",
};

interface ParsedEvent {
  title: string;
  start_time: string;
  end_time: string | null;
  location: string | null;
  description: string | null;
  url: string | null;
  source: string | null;
  all_day: boolean;
}

/**
 * Parse an ICS datetime string into an ISO string.
 * Handles: 20260405T040000Z, 20260405T040000, 20260405
 */
function parseICSDate(raw: string): string | null {
  if (!raw) return null;
  // Strip any TZID prefix — take value after the colon if present
  const val = raw.includes(":") ? raw.split(":").pop()! : raw;
  const s = val.trim();

  if (s.length === 8) {
    // All-day: YYYYMMDD
    return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T00:00:00Z`;
  }
  if (s.length >= 15) {
    const iso = `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T${s.slice(9, 11)}:${s.slice(11, 13)}:${s.slice(13, 15)}`;
    return s.endsWith("Z") ? iso + "Z" : iso + "Z"; // treat naive as UTC for preview
  }
  return null;
}

/**
 * Unfold ICS continuation lines (lines starting with space or tab).
 */
function unfold(ics: string): string {
  return ics.replace(/\r?\n[ \t]/g, "");
}

/**
 * Extract field value from a VEVENT block.
 */
function extractField(block: string, field: string): string | null {
  const re = new RegExp(`^${field}[;:](.*)$`, "im");
  const m = block.match(re);
  if (!m) return null;
  let val = m[1];
  // If there's a TZID or other param, take value after last colon in the matched line
  // But only for date fields, not for text fields
  if (
    (field === "DTSTART" || field === "DTEND") &&
    val.includes(":")
  ) {
    // The regex matched "DTSTART;TZID=...:VALUE" — the full match includes ";TZID=...:VALUE"
    // We want just the date value
  }
  return val.trim();
}

/**
 * Unescape ICS text values.
 */
function unescapeICS(text: string): string {
  return text
    .replace(/\\n/gi, "\n")
    .replace(/\\,/g, ",")
    .replace(/\\;/g, ";")
    .replace(/\\\\/g, "\\");
}

/**
 * Parse an ICS string into an array of events.
 */
function parseICS(ics: string): ParsedEvent[] {
  const unfolded = unfold(ics);
  const events: ParsedEvent[] = [];
  const blocks = unfolded.split("BEGIN:VEVENT");

  for (let i = 1; i < blocks.length; i++) {
    const block = blocks[i].split("END:VEVENT")[0];

    const rawStart = extractField(block, "DTSTART");
    if (!rawStart) continue;

    const startTime = parseICSDate(rawStart);
    if (!startTime) continue;

    const rawEnd = extractField(block, "DTEND");
    const endTime = rawEnd ? parseICSDate(rawEnd) : null;

    const summary = extractField(block, "SUMMARY");
    if (!summary) continue;

    const location = extractField(block, "LOCATION");
    const description = extractField(block, "DESCRIPTION");
    const url = extractField(block, "URL");
    const source = extractField(block, "X-SOURCE");

    // Detect all-day: VALUE=DATE or 8-char date
    const isAllDay =
      rawStart.includes("VALUE=DATE") ||
      (rawStart.replace(/.*:/, "").trim().length === 8);

    events.push({
      title: unescapeICS(summary),
      start_time: startTime,
      end_time: endTime,
      location: location ? unescapeICS(location) : null,
      description: description ? unescapeICS(description) : null,
      url: url ? unescapeICS(url) : null,
      source: source ? unescapeICS(source) : null,
      all_day: isAllDay,
    });
  }

  return events;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { url } = await req.json();
    if (!url || typeof url !== "string") {
      return new Response(
        JSON.stringify({ error: "Missing or invalid 'url' parameter" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Fetch the feed
    const feedResp = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; CommunityCalendar/1.0)",
      },
    });

    if (!feedResp.ok) {
      return new Response(
        JSON.stringify({
          error: `Feed returned HTTP ${feedResp.status}`,
          valid: false,
        }),
        { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const icsText = await feedResp.text();

    if (!icsText.includes("BEGIN:VCALENDAR")) {
      return new Response(
        JSON.stringify({
          error: "Not a valid ICS feed (missing BEGIN:VCALENDAR)",
          valid: false,
        }),
        { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const allEvents = parseICS(icsText);

    // Filter to future events, sort by start_time, take first 20
    const now = new Date().toISOString();
    const futureEvents = allEvents
      .filter((e) => e.start_time >= now)
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
      .slice(0, 20);

    return new Response(
      JSON.stringify({
        valid: true,
        totalEvents: allEvents.length,
        futureEvents: futureEvents.length,
        events: futureEvents,
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: String(err), valid: false }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
