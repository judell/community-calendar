import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth.jsx';
import { usePicks } from './usePicks.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import { buildSourceFilter } from '../lib/sourceFilter.js';

/** Curator's collection CRUD (auth required). */
export function useCollections() {
  const { user, session } = useAuth();
  const { city } = usePicks();
  const [collections, setCollections] = useState([]);
  const [membershipMap, setMembershipMap] = useState({});  // event_id → [{id, name}]
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

  // Build reverse map: event_id → collections it belongs to
  // For manual collections: query collection_events
  // For auto collections: check rules against events client-side (done via allEvents param)
  useEffect(() => {
    if (!session || !collections.length) { setMembershipMap({}); return; }

    const manualCols = collections.filter(c => c.type !== 'auto');
    const manualIds = manualCols.map(c => c.id);

    // Fetch manual collection memberships
    const manualPromise = manualIds.length
      ? fetch(
          `${SUPABASE_URL}/rest/v1/collection_events?collection_id=in.(${manualIds.join(',')})&select=collection_id,event_id`,
          { headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session.access_token } }
        ).then(r => r.json())
      : Promise.resolve([]);

    manualPromise
      .then(rows => {
        if (!Array.isArray(rows)) rows = [];
        const colMap = Object.fromEntries(collections.map(c => [c.id, c.name]));
        const map = {};
        for (const row of rows) {
          if (!map[row.event_id]) map[row.event_id] = [];
          map[row.event_id].push({ id: row.collection_id, name: colMap[row.collection_id] });
        }
        // Auto-collection membership is computed at render time in components
        // since we'd need the full events list here which we don't have
        setMembershipMap(map);
      })
      .catch(() => setMembershipMap({}));
  }, [session, collections]);

  const refresh = useCallback(() => setRefreshKey(k => k + 1), []);

  const createCollection = useCallback(async (name, opts) => {
    const h = headers();
    if (!h || !user || !city) return null;
    const body = { user_id: user.id, city, name };
    if (opts?.type === 'auto') {
      body.type = 'auto';
      body.rules = opts.rules || {};
    }
    const res = await fetch(`${SUPABASE_URL}/rest/v1/collections`, {
      method: 'POST', headers: { ...h, Prefer: 'return=representation' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    refresh();
    return Array.isArray(data) ? data[0] : data;
  }, [headers, user, city, refresh]);

  const renameCollection = useCallback(async (id, newName) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collections?id=eq.${id}`, {
      method: 'PATCH', headers: h,
      body: JSON.stringify({ name: newName }),
    });
    refresh();
  }, [headers, refresh]);

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

  const removeEventFromCollection = useCallback(async (collectionId, eventId, sourceUid, { type } = {}) => {
    const h = headers();
    if (!h) return;
    const col = collections.find(c => c.id === collectionId);
    const colType = type || col?.type;
    if (colType === 'auto') {
      // Insert exclusion by source_uid
      if (!sourceUid) return;
      await fetch(`${SUPABASE_URL}/rest/v1/auto_collection_exclusions`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ collection_id: collectionId, source_uid: sourceUid }),
      });
    } else {
      await fetch(`${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${collectionId}&event_id=eq.${eventId}`, {
        method: 'DELETE', headers: h,
      });
    }
    refresh();
  }, [headers, collections, refresh]);

  const restoreExcludedEvent = useCallback(async (collectionId, sourceUid) => {
    const h = headers();
    if (!h) return;
    await fetch(
      `${SUPABASE_URL}/rest/v1/auto_collection_exclusions?collection_id=eq.${collectionId}&source_uid=eq.${encodeURIComponent(sourceUid)}`,
      { method: 'DELETE', headers: h }
    );
    refresh();
  }, [headers, refresh]);

  /** For auto collections, returns { active, excluded }. For manual, returns { active, excluded: [] }. */
  const getCollectionEvents = useCallback(async (collectionId) => {
    const h = headers();
    if (!h) return { active: [], excluded: [] };

    const col = collections.find(c => c.id === collectionId);

    if (col?.type === 'auto') {
      // Query events directly using rules
      const rules = col.rules || {};
      const now = new Date().toISOString();
      let url = `${SUPABASE_URL}/rest/v1/events?city=eq.${encodeURIComponent(col.city)}&start_time=gte.${now}&order=start_time.asc&select=*`;
      url += buildSourceFilter(rules.sources);
      if (rules.categories?.length) {
        url += `&category=in.(${rules.categories.map(c => encodeURIComponent(c)).join(',')})`;
      }

      const [evRes, exRes, manualRes] = await Promise.all([
        fetch(url, { headers: h }),
        fetch(`${SUPABASE_URL}/rest/v1/auto_collection_exclusions?collection_id=eq.${collectionId}&select=source_uid`, { headers: h }),
        fetch(`${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${collectionId}&select=id,event_id,events(*)`, { headers: h }),
      ]);
      const allEvents = await evRes.json();
      const exclusions = await exRes.json();
      const manualAdds = await manualRes.json();
      const excludedUids = new Set((Array.isArray(exclusions) ? exclusions : []).map(e => e.source_uid));

      const ruleMatched = Array.isArray(allEvents) ? allEvents : [];
      const active = ruleMatched.filter(ev => !excludedUids.has(ev.source_uid));
      const excludedEvents = ruleMatched.filter(ev => excludedUids.has(ev.source_uid));

      // Merge manually-added events (not already in active from rules)
      const activeIds = new Set(active.map(ev => ev.id));
      const manualRows = (Array.isArray(manualAdds) ? manualAdds : []).filter(ce => ce.events && !activeIds.has(ce.event_id));
      const manualEvents = manualRows.map(ce => ce.events);

      const toShape = (ev) => ({ id: ev.id, event_id: ev.id, events: ev });

      return {
        active: [...active.map(toShape), ...manualEvents.map(toShape)],
        excluded: excludedEvents.map(toShape),
      };
    }

    // Manual collection: existing code
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/collection_events?collection_id=eq.${collectionId}&select=id,event_id,sort_order,events(id,title,start_time,location)&order=sort_order`,
      { headers: h }
    );
    const data = await res.json();
    return { active: Array.isArray(data) ? data : [], excluded: [] };
  }, [headers, collections]);

  const updateCollectionRules = useCallback(async (collectionId, rules) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collections?id=eq.${collectionId}`, {
      method: 'PATCH', headers: h,
      body: JSON.stringify({ rules }),
    });
    refresh();
  }, [headers, refresh]);

  const updateAllowedDomains = useCallback(async (collectionId, domains) => {
    const h = headers();
    if (!h) return;
    await fetch(`${SUPABASE_URL}/rest/v1/collections?id=eq.${collectionId}`, {
      method: 'PATCH', headers: h,
      body: JSON.stringify({ allowed_domains: domains }),
    });
    refresh();
  }, [headers, refresh]);

  return { collections, membershipMap, createCollection, renameCollection, deleteCollection, addEventToCollection, removeEventFromCollection, restoreExcludedEvent, getCollectionEvents, updateCollectionRules, updateAllowedDomains, refresh };
}
