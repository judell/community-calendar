import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// Events JSON URLs by city (raw.githubusercontent.com updates immediately on push,
// unlike GitHub Pages which has a cache delay)
// Set GITHUB_REPO secret in Supabase to your fork's "owner/repo" (e.g. "my-org/community-calendar")
const githubRepo = Deno.env.get("GITHUB_REPO") ?? "judell/community-calendar";
const RAW_BASE = `https://raw.githubusercontent.com/${githubRepo}/main/cities`;
const EVENTS_URLS: Record<string, string> = {
  santarosa: `${RAW_BASE}/santarosa/events.json`,
  petaluma: `${RAW_BASE}/petaluma/events.json`,
  bloomington: `${RAW_BASE}/bloomington/events.json`,
  davis: `${RAW_BASE}/davis/events.json`,
  toronto: `${RAW_BASE}/toronto/events.json`,
  raleighdurham: `${RAW_BASE}/raleighdurham/events.json`,
  montclair: `${RAW_BASE}/montclair/events.json`,
  roanoke: `${RAW_BASE}/roanoke/events.json`,
};

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Create Supabase client with service role for database access
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Fetch events from all cities, delete stale records, then upsert
    const allEvents: any[] = [];
    let deleted = 0;
    for (const [city, url] of Object.entries(EVENTS_URLS)) {
      console.log(`Fetching events from ${city}:`, url);
      try {
        const response = await fetch(url);
        if (!response.ok) {
          console.error(`Failed to fetch ${city}: ${response.status}`);
          continue;
        }
        const events = await response.json();
        // Ensure city is set on each event
        for (const event of events) {
          event.city = event.city || city;
        }
        // Delete existing events for this city to remove stale records
        const { count, error: delError } = await supabase
          .from("events")
          .delete({ count: "exact" })
          .eq("city", city);
        if (delError) {
          console.error(`Delete ${city} error:`, delError);
        } else {
          deleted += count || 0;
          console.log(`Deleted ${count} existing events for ${city}`);
        }
        allEvents.push(...events);
        console.log(`Fetched ${events.length} events from ${city}`);
      } catch (e) {
        console.error(`Error fetching ${city}:`, e);
      }
    }
    console.log(`Total fetched: ${allEvents.length} events`);

    // Deduplicate by source_uid
    const uniqueEvents = new Map();
    for (const event of allEvents) {
      if (event.source_uid && !uniqueEvents.has(event.source_uid)) {
        uniqueEvents.set(event.source_uid, event);
      }
    }
    console.log(`Unique events: ${uniqueEvents.size}`);

    // Insert events in batches
    const batchSize = 500;
    const eventsArray = Array.from(uniqueEvents.values());
    let inserted = 0;
    let errors = 0;

    for (let i = 0; i < eventsArray.length; i += batchSize) {
      const batch = eventsArray.slice(i, i + batchSize);

      const { error } = await supabase
        .from("events")
        .upsert(batch, {
          onConflict: "source_uid",
          ignoreDuplicates: false
        });

      if (error) {
        console.error(`Batch ${i / batchSize} error:`, error);
        errors += batch.length;
      } else {
        inserted += batch.length;
      }
    }

    const result = {
      success: errors === 0,
      fetched: allEvents.length,
      unique: uniqueEvents.size,
      deleted,
      inserted,
      errors,
    };

    console.log("Result:", result);

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
