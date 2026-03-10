import { useState, useEffect } from 'react';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import { applyEnrichments } from '../lib/helpers.js';

/** Fetch a single public collection + its events (no auth required). */
export function useCollection(feedId) {
  const [collection, setCollection] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!feedId) { setLoading(false); return; }

    const headers = { apikey: SUPABASE_KEY };

    async function load() {
      try {
        // Fetch collection metadata
        const colRes = await fetch(
          `${SUPABASE_URL}/rest/v1/collections?id=eq.${feedId}&select=*`,
          { headers }
        );
        const colData = await colRes.json();
        const col = Array.isArray(colData) ? colData[0] : null;
        setCollection(col || null);
        if (!col) { setEvents([]); setLoading(false); return; }

        // Fetch collection events with joined event data
        const evRes = await fetch(
          `${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${feedId}&select=sort_order,event_id,events(*)&order=sort_order`,
          { headers }
        );
        const evData = await evRes.json();
        const rawEvents = (Array.isArray(evData) ? evData : [])
          .filter(ce => ce.events)
          .map(ce => ({ ...ce.events, _sort_order: ce.sort_order }));

        // Fetch curator's enrichments and apply them
        const enrRes = await fetch(
          `${SUPABASE_URL}/rest/v1/event_enrichments?curator_id=eq.${col.user_id}&select=*`,
          { headers }
        );
        const enrichments = await enrRes.json();
        const enriched = applyEnrichments(rawEvents, Array.isArray(enrichments) ? enrichments : []);

        setEvents(enriched);
      } catch {
        setCollection(null);
        setEvents([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [feedId]);

  return { collection, events, loading };
}
