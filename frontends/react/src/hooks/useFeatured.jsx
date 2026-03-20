import { useRef, useEffect, useCallback, createContext, useContext, useSyncExternalStore } from 'react';
import { useAuth } from './useAuth.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

const FeaturedContext = createContext(null);

function createFeaturedStore() {
  let ids = new Set();
  let listeners = new Set();
  return {
    getSnapshot: () => ids,
    subscribe: (cb) => { listeners.add(cb); return () => listeners.delete(cb); },
    set: (newIds) => { ids = newIds; listeners.forEach(cb => cb()); },
    add: (id) => { ids = new Set(ids); ids.add(id); listeners.forEach(cb => cb()); },
    remove: (id) => { ids = new Set(ids); ids.delete(id); listeners.forEach(cb => cb()); },
  };
}

export function FeaturedProvider({ city, children }) {
  const { user, session } = useAuth();
  const store = useRef(createFeaturedStore()).current;

  useEffect(() => {
    if (!user || !session) {
      store.set(new Set());
      return;
    }

    const headers = { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session.access_token };
    const cityFilter = city ? `&city=eq.${city}` : '';
    const url = `${SUPABASE_URL}/rest/v1/event_enrichments?curator_id=eq.${user.id}&featured=eq.true${cityFilter}&select=event_id`;

    fetch(url, { headers })
      .then(r => r.json())
      .then(data => {
        const arr = Array.isArray(data) ? data : [];
        store.set(new Set(arr.map(e => e.event_id).filter(Boolean)));
      })
      .catch(() => store.set(new Set()));
  }, [user, session, city]);

  const toggleFeatured = useCallback(async (event) => {
    if (!user || !session) return;

    const headers = {
      apikey: SUPABASE_KEY,
      Authorization: 'Bearer ' + session.access_token,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal,resolution=merge-duplicates',
    };

    const ids = store.getSnapshot();
    const wasFeatured = ids.has(event.id);

    // Optimistic update
    if (wasFeatured) {
      store.remove(event.id);
    } else {
      store.add(event.id);
    }

    try {
      await fetch(`${SUPABASE_URL}/rest/v1/event_enrichments?on_conflict=event_id,curator_id`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          event_id: event.id,
          curator_id: user.id,
          city: city || event.city || null,
          featured: !wasFeatured,
        }),
      });
    } catch {
      // Revert on failure
      if (wasFeatured) {
        store.add(event.id);
      } else {
        store.remove(event.id);
      }
    }
  }, [user, session, city, store]);

  return (
    <FeaturedContext.Provider value={{ featuredStore: store, toggleFeatured }}>
      {children}
    </FeaturedContext.Provider>
  );
}

export function useFeatured() {
  const ctx = useContext(FeaturedContext);
  if (!ctx) throw new Error('useFeatured must be used within FeaturedProvider');
  return ctx;
}

export function useIsEventFeatured(eventId) {
  const { featuredStore } = useFeatured();
  const ids = useSyncExternalStore(featuredStore.subscribe, featuredStore.getSnapshot);
  return ids.has(eventId);
}
