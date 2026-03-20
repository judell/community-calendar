import { useState, useEffect } from 'react';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

// Compute date range: 1 hour ago to 13 months out
// 13 months covers annual recurring events even when not perfectly yearly.
// Event times are stored as real UTC in timestamptz columns,
// so we send UTC ISO strings for correct comparison
function getDateRange() {
  const now = new Date();
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  const rangeEnd = new Date(now.getTime() + 395 * 24 * 60 * 60 * 1000);
  return {
    from: oneHourAgo.toISOString(),
    to: rangeEnd.toISOString(),
  };
}

export function useEvents(city, session) {
  const [events, setEvents] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!city) {
      setEvents(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const { from, to } = getDateRange();

    const url = `${SUPABASE_URL}/rest/v1/public_events?select=*&order=start_time.asc&limit=5000&start_time=gte.${from}&start_time=lte.${to}&city=eq.${city}`;

    const headers = {
      apikey: SUPABASE_KEY,
      'Cache-Control': 'no-cache, no-store, must-revalidate',
    };
    // Pass auth token so public_events view can include curator's private sources
    if (session?.access_token) {
      headers['Authorization'] = 'Bearer ' + session.access_token;
    }

    fetch(url, { headers })
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setLoading(false);
      })
      .catch(() => {
        setEvents([]);
        setLoading(false);
      });
  }, [city, session]);

  return { events, loading };
}

export { getDateRange };
