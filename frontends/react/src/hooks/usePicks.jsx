import { useState, useEffect, useCallback, useRef, createContext, useContext, useSyncExternalStore } from 'react';
import { useAuth } from './useAuth.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import { applyEnrichments } from '../lib/helpers.js';

const PicksContext = createContext(null);

// Simple external store for picked IDs — avoids re-rendering every card on change
function createPickedStore() {
  let ids = new Set();
  let listeners = new Set();
  return {
    getSnapshot: () => ids,
    subscribe: (cb) => { listeners.add(cb); return () => listeners.delete(cb); },
    set: (newIds) => { ids = newIds; listeners.forEach(cb => cb()); },
    add: (id) => { ids = new Set(ids); ids.add(id); listeners.forEach(cb => cb()); },
    remove: (id) => { ids = new Set(ids); ids.delete(id); listeners.forEach(cb => cb()); },
    has: (id) => ids.has(id),
  };
}

export function PicksProvider({ city, children }) {
  const { user, session } = useAuth();
  const [picks, setPicks] = useState([]);
  const pickedStore = useRef(createPickedStore()).current;
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
    if (!user || !session) {
      setPicks([]);
      pickedStore.set(new Set());
      return;
    }

    const headers = { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session.access_token };
    const cityFilter = city ? `&events.city=eq.${city}` : '';
    const picksUrl = `${SUPABASE_URL}/rest/v1/picks?select=id,event_id,events!inner(id,title,start_time,end_time,location,url,source,description,image_url,category,city)&user_id=eq.${user.id}${cityFilter}&order=created_at.desc`;
    const enrichCityFilter = city ? `&city=eq.${city}` : '';
    const enrichUrl = `${SUPABASE_URL}/rest/v1/event_enrichments?curator_id=eq.${user.id}${enrichCityFilter}&select=*`;

    Promise.all([
      fetch(picksUrl, { headers }).then(r => r.json()),
      fetch(enrichUrl, { headers }).then(r => r.json()),
    ])
      .then(([picksData, enrichData]) => {
        const arr = Array.isArray(picksData) ? picksData : [];
        const enrichments = Array.isArray(enrichData) ? enrichData : [];

        // Apply enrichment overrides to the embedded event objects
        if (enrichments.length > 0) {
          const events = arr.map(p => p.events).filter(Boolean);
          const enriched = applyEnrichments(events, enrichments);
          const byId = {};
          enriched.forEach(e => { byId[e.id] = e; });
          arr.forEach(p => { if (p.events && byId[p.events.id]) p.events = byId[p.events.id]; });
        }

        setPicks(arr);
        pickedStore.set(new Set(arr.map(p => p.event_id)));
      })
      .catch(() => {
        setPicks([]);
        pickedStore.set(new Set());
      });
  }, [user, session, city, refreshKey]);

  const togglePick = useCallback(async (event) => {
    const headers = getHeaders();
    if (!user || !headers) return false;

    const ids = event.mergedIds || [event.id];
    const wasPicked = ids.some(id => pickedStore.has(id));

    if (wasPicked) {
      // Optimistic: remove from store immediately
      ids.forEach(id => pickedStore.remove(id));

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
      }
      // Background refresh for picks list
      setRefreshKey(k => k + 1);
      return false;
    } else {
      // Optimistic: add to store immediately
      pickedStore.add(event.id);

      await fetch(`${SUPABASE_URL}/rest/v1/picks`, {
        method: 'POST', headers,
        body: JSON.stringify({ user_id: user.id, event_id: event.id }),
      });
      // Background refresh for picks list
      setRefreshKey(k => k + 1);
      return true;
    }
  }, [user, getHeaders, pickedStore]);

  const removePick = useCallback(async (pickId) => {
    const headers = getHeaders();
    if (!headers) return;
    // Find the event_id to remove from store
    const pick = picks.find(p => p.id === pickId);
    if (pick) pickedStore.remove(pick.event_id);

    await fetch(`${SUPABASE_URL}/rest/v1/picks?id=eq.${pickId}`, {
      method: 'DELETE', headers,
    });
    setRefreshKey(k => k + 1);
  }, [getHeaders, picks, pickedStore]);

  return (
    <PicksContext.Provider value={{ picks, pickedStore, togglePick, removePick, city }}>
      {children}
    </PicksContext.Provider>
  );
}

export function usePicks() {
  const ctx = useContext(PicksContext);
  if (!ctx) throw new Error('usePicks must be used within PicksProvider');
  return ctx;
}

// Lightweight hook — only re-renders when THIS event's picked state changes
export function useIsEventPicked(eventId) {
  const { pickedStore } = usePicks();
  const ids = useSyncExternalStore(pickedStore.subscribe, pickedStore.getSnapshot);
  return ids.has(eventId);
}
