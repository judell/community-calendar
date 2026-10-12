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
      const errorDetails: string[] = [];

      for (let i = 0; i < eventsArray.length; i += batchSize) {
        const batchNum = i / batchSize;
        const batch = eventsArray.slice(i, i + batchSize);
        let lastError: any = null;

        // Retry each batch up to 3 times for transient failures
        for (let attempt = 0; attempt < 3; attempt++) {
          const { error } = await supabase
            .from("events")
            .upsert(batch, { onConflict: "source_uid", ignoreDuplicates: false });
          if (!error) {
            inserted += batch.length;
            lastError = null;
            break;
          }
          lastError = error;
          console.error(`Batch ${batchNum} attempt ${attempt + 1} error:`, JSON.stringify(error));
          if (attempt < 2) {
            await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
          }
        }
        if (lastError) {
          errors += batch.length;
          errorDetails.push(`batch ${batchNum}: ${lastError.message || JSON.stringify(lastError)}`);
        }
      }

      // Remove stale events for this city that are no longer in the feed.
      // Scoped to the sources present in the payload: a source that failed to
      // produce output is absent here and keeps its rows (issue #227).
      // Uses RPC to avoid URL length limits with large IN lists.
      const newSourceUids = Array.from(uniqueEvents.keys());
      // Derive present sources from the accepted events, not the raw body: an
      // event with a source_id but no source_uid is dropped by the upsert, so
      // it must not activate a sweep of that source (no keep uid would exist).
      const presentSources = [
        ...new Set(Array.from(uniqueEvents.values()).map((e: any) => e.source_id).filter(Boolean)),
      ];
      if (newSourceUids.length > 0 && presentSources.length === 0) {
        console.warn(
          `Cleanup ${city}: payload has source_uids but no source_id; stale sweep skipped`
        );
      }
      let deleted = 0;
      if (newSourceUids.length > 0) {
        const { data: delCount, error: delError } = await supabase
          .rpc("delete_stale_events", {
            p_city: city,
            p_source_uids: newSourceUids,
            p_sources: presentSources,
          });
        if (delError) {
          console.error(`Cleanup ${city} error:`, delError);
          errorDetails.push(`cleanup: ${delError.message}`);
        } else {
          deleted = delCount || 0;
        }
      }
      if (deleted > 0) {
        console.log(`Cleaned up ${deleted} stale events for ${city}`);
      }

      const result: any = { success: errors === 0, city, fetched: events.length, unique: uniqueEvents.size, deleted, inserted, errors };
      if (errorDetails.length > 0) {
        result.errorDetails = errorDetails;
      }
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

    // Collect events per city for stale cleanup after upsert
    const allEvents: any[] = [];
    const eventsByCity = new Map<string, string[]>(); // city -> source_uids
    const sourcesByCity = new Map<string, string[]>(); // city -> source_ids
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
        const cityUids: string[] = [];
        const citySources: string[] = [];
        for (const event of events) {
          event.city = event.city || city;
          // Only an accepted event (one with a source_uid) activates its
          // source for cleanup; see the direct-POST path note above.
          if (event.source_uid) {
            cityUids.push(event.source_uid);
            if (event.source_id) citySources.push(event.source_id);
          }
        }
        eventsByCity.set(city, cityUids);
        sourcesByCity.set(city, [...new Set(citySources)]);
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
    const errorDetails: string[] = [];

    for (let i = 0; i < eventsArray.length; i += batchSize) {
      const batchNum = i / batchSize;
      const batch = eventsArray.slice(i, i + batchSize);
      let lastError: any = null;

      for (let attempt = 0; attempt < 3; attempt++) {
        const { error } = await supabase
          .from("events")
          .upsert(batch, { onConflict: "source_uid", ignoreDuplicates: false });
        if (!error) {
          inserted += batch.length;
          lastError = null;
          break;
        }
        lastError = error;
        console.error(`Batch ${batchNum} attempt ${attempt + 1} error:`, JSON.stringify(error));
        if (attempt < 2) {
          await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
        }
      }
      if (lastError) {
        errors += batch.length;
        errorDetails.push(`batch ${batchNum}: ${lastError.message || JSON.stringify(lastError)}`);
      }
    }

    // Remove stale events per city, scoped to the sources present in the
    // payload, using RPC to avoid URL length limits
    let deleted = 0;
    for (const [city, uids] of eventsByCity) {
      if (uids.length > 0) {
        const sources = sourcesByCity.get(city) ?? [];
        if (sources.length === 0) {
          console.warn(
            `Cleanup ${city}: payload has source_uids but no source_id; stale sweep skipped`
          );
        }
        const { data: delCount, error: delError } = await supabase
          .rpc("delete_stale_events", {
            p_city: city,
            p_source_uids: uids,
            p_sources: sources,
          });
        if (delError) {
          console.error(`Cleanup ${city} error:`, delError);
        } else {
          deleted += delCount || 0;
        }
      }
    }
    if (deleted > 0) {
      console.log(`Cleaned up ${deleted} stale events`);
    }

    const result: any = { success: errors === 0, fetched: allEvents.length, unique: uniqueEvents.size, deleted, inserted, errors };
    if (errorDetails.length > 0) {
      result.errorDetails = errorDetails;
    }
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
