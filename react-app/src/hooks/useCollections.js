import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth.jsx';
import { usePicks } from './usePicks.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

/** Curator's collection CRUD (auth required). */
export function useCollections() {
  const { user, session } = useAuth();
  const { city } = usePicks();
  const [collections, setCollections] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const headers = useCallback(() => {
    if (!session) return null;
    return {
      apikey: SUPABASE_KEY,
      Authorization: 'Bearer ' + session.access_token,
      'Content-Type': 'application/json',
    };
  }, [session]);

  // Fetch user's collections
  useEffect(() => {
    if (!user || !session || !city) { setCollections([]); return; }

    fetch(`${SUPABASE_URL}/rest/v1/collections?user_id=eq.${user.id}&city=eq.${city}&select=*&order=created_at.desc`, {
      headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session.access_token },
    })
      .then(r => r.json())
      .then(data => setCollections(Array.isArray(data) ? data : []))
      .catch(() => setCollections([]));
  }, [user, session, city, refreshKey]);

  const refresh = useCallback(() => setRefreshKey(k => k + 1), []);

  const createCollection = useCallback(async (name) => {
    const h = headers();
    if (!h || !user || !city) return null;
    const res = await fetch(`${SUPABASE_URL}/rest/v1/collections`, {
      method: 'POST', headers: { ...h, Prefer: 'return=representation' },
      body: JSON.stringify({ user_id: user.id, city, name }),
    });
    const data = await res.json();
    refresh();
    return Array.isArray(data) ? data[0] : data;
  }, [headers, user, refresh]);

  const deleteCollection = useCallback(async (id) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collections?id=eq.${id}`, {
      method: 'DELETE', headers: h,
    });
    refresh();
  }, [headers, refresh]);

  const addEventToCollection = useCallback(async (collectionId, eventId) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collection_events`, {
      method: 'POST', headers: h,
      body: JSON.stringify({ collection_id: collectionId, event_id: eventId }),
    });
    refresh();
  }, [headers, refresh]);

  const removeEventFromCollection = useCallback(async (collectionId, eventId) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${collectionId}&event_id=eq.${eventId}`, {
      method: 'DELETE', headers: h,
    });
    refresh();
  }, [headers, refresh]);

  const getCollectionEvents = useCallback(async (collectionId) => {
    const h = headers();
    if (!h) return [];
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${collectionId}&select=id,event_id,sort_order,events(id,title,start_time,location)&order=sort_order`,
      { headers: h }
    );
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  }, [headers]);

  return { collections, createCollection, deleteCollection, addEventToCollection, removeEventFromCollection, getCollectionEvents, refresh };
}
