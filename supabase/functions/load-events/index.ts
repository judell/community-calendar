import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { resolveSweepScope } from "./scope.ts";
import { authorize, SECRET_HEADER } from "./auth.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  // Direct POST is the only mode left, and only CI holds this secret.
  const auth = authorize(req.headers.get(SECRET_HEADER), Deno.env.get("LOAD_EVENTS_SECRET"));
  if (auth !== "ok") {
    if (auth === "unconfigured") {
      console.error("LOAD_EVENTS_SECRET is not set; refusing all writes");
    }
    return new Response(JSON.stringify({ success: false, error: "unauthorized" }), {
      status: auth === "unconfigured" ? 500 : 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
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

      // Manifest of sources whose ingestion succeeded this build (#233).
      // Absent means the caller predates it; a present-but-empty array means
      // nothing ran.
      const ranSources = Array.isArray(body.ran_sources)
        ? body.ran_sources.filter((s: unknown) => typeof s === "string" && s.length > 0)
        : undefined;
      if (body.ran_sources !== undefined && ranSources === undefined) {
        console.warn(`Direct POST ${city}: ran_sources is not an array; ignoring it`);
      }
      if (ranSources) console.log(`Ran sources for ${city}: ${ranSources.length}`);

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
      // Scoped to the sources that ran this build (#233): `ran_sources` comes
      // from the runners, so a quiet source is swept while a failed one keeps
      // its rows. Without a manifest, fall back to the sources present in the
      // payload (#227). Uses RPC to avoid URL length limits with large IN lists.
      const newSourceUids = Array.from(uniqueEvents.keys());
      // Derive present sources from the accepted events, not the raw body: an
      // event with a source_id but no source_uid is dropped by the upsert, so
      // it must not activate a sweep of that source (no keep uid would exist).
      const presentSources = [
        ...new Set(Array.from(uniqueEvents.values()).map((e: any) => e.source_id).filter(Boolean)),
      ];
      if (newSourceUids.length > 0 && !ranSources && presentSources.length === 0) {
        console.warn(
          `Cleanup ${city}: payload has source_uids but no source_id and no ran_sources; stale sweep skipped`
        );
      }
      if (ranSources && ranSources.length > 0 && newSourceUids.length === 0) {
        console.warn(
          `Cleanup ${city}: ran_sources is non-empty but the payload has no events; nothing swept`
        );
      }
      let deleted = 0;
      if (errors > 0) {
        console.warn(
          `Cleanup ${city} skipped: ${errors} events failed to upsert, so their replacements may be missing`
        );
      }
      if (errors === 0 && newSourceUids.length > 0) {
        const { data: delCount, error: delError } = await supabase
          .rpc("delete_stale_events", {
            p_city: city,
            p_source_uids: newSourceUids,
            p_sources: resolveSweepScope(ranSources, presentSources),
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

    // The legacy mode (fetch cities/*/events.json from GitHub, sweep every
    // city) was removed with the security fix; the cron job that used it is
    // unscheduled by 20261024120000_lock_down_event_writes.sql.
    return new Response(
      JSON.stringify({ success: false, error: "expected {city, events}" }),
      { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : String(error) }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
