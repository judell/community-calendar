import React, { createContext, useContext, useState, useCallback } from 'react';
import { useCollections } from './useCollections.js';

const Ctx = createContext({ target: null, setTarget: () => {}, addToTarget: () => {} });

export function TargetCollectionProvider({ children }) {
  const { collections, addEventToCollection, removeEventFromCollection, createCollection, membershipMap, refresh } = useCollections();
  const [targetId, setTargetId] = useState(null);

  // Resolve target from collections (null if deleted or not found)
  const target = targetId ? collections.find(c => c.id === targetId) || null : null;

  const setTarget = useCallback((id) => setTargetId(id), []);

  const addToTarget = useCallback(async (eventId) => {
    if (!target) return;
    await addEventToCollection(target.id, eventId);
  }, [target, addEventToCollection]);

  const removeFromTarget = useCallback(async (eventId) => {
    if (!target) return;
    await removeEventFromCollection(target.id, eventId);
  }, [target, removeEventFromCollection]);

  return (
    <Ctx.Provider value={{ target, setTarget, addToTarget, removeFromTarget, collections, createCollection, membershipMap, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useTargetCollection() {
  return useContext(Ctx);
}
