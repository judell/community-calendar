import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const body = await req.json().catch(() => ({}));

    // --- Direct POST mode: CI sends {city, events} per city ---
    if (body.city && Array.isArray(body.events)) {
      const city = body.city;
      const events = body.events;
      console.log(`Direct POST: ${events.length} events for ${city}`);

      for (const event of events) {
        event.city = event.city || city;
      }

      const { count, error: delError } = await supabase
        .from("events")
        .delete({ count: "exact" })
        .eq("city", city);
      if (delError) {
        console.error(`Delete ${city} error:`, delError);
      } else {
        console.log(`Deleted ${count} existing events for ${city}`);
      }

      const uniqueEvents = new Map();
      for (const event of events) {
        if (event.source_uid && !uniqueEvents.has(event.source_uid)) {
          uniqueEvents.set(event.source_uid, event);
        }
      }
      console.log(`Unique events for ${city}: ${uniqueEvents.size}`);

      const batchSize = 500;
      const eventsArray = Array.from(uniqueEvents.values());
      let inserted = 0;
      let errors = 0;

      for (let i = 0; i < eventsArray.length; i += batchSize) {
        const batch = eventsArray.slice(i, i + batchSize);
        const { error } = await supabase
          .from("events")
          .upsert(batch, { onConflict: "source_uid", ignoreDuplicates: false });
        if (error) {
          console.error(`Batch ${i / batchSize} error:`, error);
          errors += batch.length;
        } else {
          inserted += batch.length;
        }
      }

      const result = { success: errors === 0, city, fetched: events.length, unique: uniqueEvents.size, deleted: count || 0, inserted, errors };
      console.log("Result:", result);
      return new Response(JSON.stringify(result), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // --- Legacy mode: fetch events.json from GitHub for each city ---
    const ghRepo = Deno.env.get("GITHUB_REPO") || "judell/community-calendar";
    const RAW_BASE = `https://raw.githubusercontent.com/${ghRepo}/main/cities`;

    let cities: string[] = [];
    if (body.cities && Array.isArray(body.cities)) {
      cities = body.cities;
    }

    if (cities.length === 0) {
      try {
        const apiUrl = `https://api.github.com/repos/${ghRepo}/contents/cities`;
        const resp = await fetch(apiUrl, { headers: { "User-Agent": "load-events" } });
        if (resp.ok) {
          const entries = await resp.json();
          cities = entries.filter((e: any) => e.type === "dir").map((e: any) => e.name);
        }
      } catch (e) {
        console.error("Failed to discover cities:", e);
      }
    }

    if (cities.length === 0) {
      return new Response(JSON.stringify({ success: false, error: "No cities found" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    console.log(`Processing cities: ${cities.join(", ")}`);

    const allEvents: any[] = [];
    let deleted = 0;
    for (const city of cities) {
      const url = `${RAW_BASE}/${city}/events.json`;
      console.log(`Fetching events from ${city}:`, url);
      try {
        const response = await fetch(url);
        if (!response.ok) {
          console.error(`Failed to fetch ${city}: ${response.status}`);
          continue;
        }
        const events = await response.json();
        for (const event of events) {
          event.city = event.city || city;
        }
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

    const uniqueEvents = new Map();
    for (const event of allEvents) {
      if (event.source_uid && !uniqueEvents.has(event.source_uid)) {
        uniqueEvents.set(event.source_uid, event);
      }
    }
    console.log(`Unique events: ${uniqueEvents.size}`);

    const batchSize = 500;
    const eventsArray = Array.from(uniqueEvents.values());
    let inserted = 0;
    let errors = 0;

    for (let i = 0; i < eventsArray.length; i += batchSize) {
      const batch = eventsArray.slice(i, i + batchSize);
      const { error } = await supabase
        .from("events")
        .upsert(batch, { onConflict: "source_uid", ignoreDuplicates: false });
      if (error) {
        console.error(`Batch ${i / batchSize} error:`, error);
        errors += batch.length;
      } else {
        inserted += batch.length;
      }
    }

    const result = { success: errors === 0, fetched: allEvents.length, unique: uniqueEvents.size, deleted, inserted, errors };
    console.log("Result:", result);
    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
