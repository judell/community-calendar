import React, { createContext, useContext } from 'react';

const FeedCtx = createContext(null);

/** Wraps a feed view to provide remove-from-collection capability to cards. */
export function FeedProvider({ collection, onRemoveEvent, children }) {
  return (
    <FeedCtx.Provider value={{ collection, onRemoveEvent }}>
      {children}
    </FeedCtx.Provider>
  );
}

/** Returns { collection, onRemoveEvent } if inside a FeedProvider, else null. */
export function useFeedContext() {
  return useContext(FeedCtx);
}
