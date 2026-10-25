import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function jsonResponse(body: unknown, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

// Constant-time string comparison, so response timing doesn't leak how
// much of a guessed secret matched.
function timingSafeEqual(a: string, b: string): boolean {
  const ea = new TextEncoder().encode(a);
  const eb = new TextEncoder().encode(b);
  if (ea.length !== eb.length) return false;
  let diff = 0;
  for (let i = 0; i < ea.length; i++) diff |= ea[i] ^ eb[i];
  return diff === 0;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  // Trusted-caller gate. This function writes with the service-role key,
  // and the publishable key that reaches it is public (it ships in
  // xmlui/config.json), so the nightly workflow must also present the
  // shared LOAD_EVENTS_SECRET. Fails closed when the secret is unset.
  const expectedSecret = Deno.env.get("LOAD_EVENTS_SECRET");
  if (!expectedSecret) {
    console.error("LOAD_EVENTS_SECRET is not set; refusing all requests");
    return jsonResponse({ success: false, error: "Server misconfigured" }, 500);
  }
  const presented = req.headers.get("x-load-events-secret") ?? "";
  if (!timingSafeEqual(presented, expectedSecret)) {
    return jsonResponse({ success: false, error: "Unauthorized" }, 401);
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

      // Remove stale events for this city that are no longer in the feed
      // Uses RPC to avoid URL length limits with large IN lists
      const newSourceUids = Array.from(uniqueEvents.keys());
      let deleted = 0;
      if (newSourceUids.length > 0) {
        const { data: delCount, error: delError } = await supabase
          .rpc("delete_stale_events", { p_city: city, p_source_uids: newSourceUids });
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

    // The legacy "fetch every city's events.json from GitHub" mode (empty
    // body, driven by the load-events-daily cron) was removed: an empty POST
    // would re-import and sweep every city. CI uploads per city instead.
    return jsonResponse({ success: false, error: "Expected {city, events}" }, 400);
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
