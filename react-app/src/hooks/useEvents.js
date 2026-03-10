import { useState, useEffect } from 'react';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

// Compute date range: 1 hour ago to 3 months out
// NOTE: Event times are stored as local times with +00:00 marker,
// so we format local times directly to match the database format
function getDateRange() {
  const pad = n => n.toString().padStart(2, '0');
  const formatLocal = d =>
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

  const now = new Date();
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
  const threeMonthsLater = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000);
  return {
    from: formatLocal(oneHourAgo),
    to: formatLocal(threeMonthsLater),
  };
}

export function useEvents(city) {
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

    const url = `${SUPABASE_URL}/rest/v1/events?select=*&order=start_time.asc&limit=5000&start_time=gte.${from}&start_time=lte.${to}&city=eq.${city}`;

    fetch(url, {
      headers: {
        apikey: SUPABASE_KEY,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    })
      .then(res => res.json())
      .then(data => {
        setEvents(data);
        setLoading(false);
      })
      .catch(() => {
        setEvents([]);
        setLoading(false);
      });
  }, [city]);

  return { events, loading };
}

export { getDateRange };
