import { useState, useEffect } from 'react';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

export function useEnrichments(city) {
  const [enrichments, setEnrichments] = useState(null);

  useEffect(() => {
    if (!city) {
      setEnrichments(null);
      return;
    }

    const url = `${SUPABASE_URL}/rest/v1/event_enrichments?select=*&city=eq.${city}`;

    fetch(url, {
      headers: {
        apikey: SUPABASE_KEY,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    })
      .then(res => res.json())
      .then(data => setEnrichments(data))
      .catch(() => setEnrichments([]));
  }, [city]);

  return enrichments;
}
