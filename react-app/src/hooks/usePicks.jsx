import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { useAuth } from './useAuth.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

const PicksContext = createContext(null);

export function PicksProvider({ city, children }) {
  const { user, session } = useAuth();
  const [picks, setPicks] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const getHeaders = useCallback(() => {
    if (!session) return null;
    return {
      apikey: SUPABASE_KEY,
      Authorization: 'Bearer ' + session.access_token,
      'Content-Type': 'application/json',
    };
  }, [session]);

  // Fetch user's picks
  useEffect(() => {
    if (!user || !session) { setPicks([]); return; }

    const url = `${SUPABASE_URL}/rest/v1/picks?select=id,event_id,events(id,title,start_time,end_time,location,url,source,description,image_url,category)&user_id=eq.${user.id}&order=created_at.desc`;
    fetch(url, { headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session.access_token } })
      .then(r => r.json())
      .then(data => setPicks(Array.isArray(data) ? data : []))
      .catch(() => setPicks([]));
  }, [user, session, refreshKey]);

  const isEventPicked = useCallback((eventId) => {
    if (!picks.length) return false;
    return picks.some(p => p.event_id === eventId);
  }, [picks]);

  const togglePick = useCallback(async (event) => {
    const headers = getHeaders();
    if (!user || !headers) return false;

    const ids = event.mergedIds || [event.id];
    const checkUrl = `${SUPABASE_URL}/rest/v1/picks?select=id&user_id=eq.${user.id}&event_id=in.(${ids.join(',')})`;
    const checkRes = await fetch(checkUrl, { headers });
    const existing = await checkRes.json();

    if (existing?.length > 0) {
      await fetch(`${SUPABASE_URL}/rest/v1/picks?id=eq.${existing[0].id}`, {
        method: 'DELETE', headers,
      });
      for (const eid of ids) {
        await fetch(`${SUPABASE_URL}/rest/v1/event_enrichments?event_id=eq.${eid}&curator_id=eq.${user.id}`, {
          method: 'DELETE', headers,
        });
      }
      setRefreshKey(k => k + 1);
      return false;
    } else {
      await fetch(`${SUPABASE_URL}/rest/v1/picks`, {
        method: 'POST', headers,
        body: JSON.stringify({ user_id: user.id, event_id: event.id }),
      });
      setRefreshKey(k => k + 1);
      return true;
    }
  }, [user, getHeaders]);

  const removePick = useCallback(async (pickId) => {
    const headers = getHeaders();
    if (!headers) return;
    await fetch(`${SUPABASE_URL}/rest/v1/picks?id=eq.${pickId}`, {
      method: 'DELETE', headers,
    });
    setRefreshKey(k => k + 1);
  }, [getHeaders]);

  return (
    <PicksContext.Provider value={{ picks, isEventPicked, togglePick, removePick }}>
      {children}
    </PicksContext.Provider>
  );
}

export function usePicks() {
  const ctx = useContext(PicksContext);
  if (!ctx) throw new Error('usePicks must be used within PicksProvider');
  return ctx;
}
