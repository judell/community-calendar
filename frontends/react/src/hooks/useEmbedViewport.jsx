import React, { createContext, useContext, useEffect, useRef, useCallback } from 'react';

const EmbedViewportContext = createContext({ isEmbed: false, getViewportRect: () => null });

export function EmbedViewportProvider({ children }) {
  const params = new URLSearchParams(window.location.search);
  const isEmbed = params.has('embed');
  const viewportRef = useRef(null);

  useEffect(() => {
    if (!isEmbed) return;

    function handleMessage(e) {
      if (e.data?.type === 'community-calendar-embed-viewport') {
        const { iframeTop, iframeHeight, viewportHeight, parentScrollY } = e.data;
        const visibleTop = Math.max(0, parentScrollY - iframeTop);
        const iframeBottom = iframeTop + iframeHeight;
        const viewportBottom = parentScrollY + viewportHeight;
        const visibleBottom = Math.min(iframeHeight, viewportBottom - iframeTop);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        viewportRef.current = { visibleTop, visibleHeight };
      }
    }

    window.addEventListener('message', handleMessage);
    // Signal to parent that we're ready for viewport info
    window.parent.postMessage({ type: 'community-calendar-embed-ready' }, '*');

    return () => window.removeEventListener('message', handleMessage);
  }, [isEmbed]);

  const getViewportRect = useCallback(() => viewportRef.current, []);

  return (
    <EmbedViewportContext.Provider value={{ isEmbed, getViewportRect }}>
      {children}
    </EmbedViewportContext.Provider>
  );
}

export function useEmbedViewport() {
  return useContext(EmbedViewportContext);
}
