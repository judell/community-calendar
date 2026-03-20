import React from 'react';
import { createPortal } from 'react-dom';
import { useEmbedViewport } from '../hooks/useEmbedViewport.jsx';

export default function EmbedModal({ children, onClose }) {
  const { isEmbed, getViewportRect } = useEmbedViewport();
  const rect = isEmbed ? getViewportRect() : null;

  const content = rect ? (
    // Embed mode: absolute positioning at the visible slice of the iframe
    <div
      style={{
        position: 'absolute',
        top: rect.visibleTop,
        left: 0,
        right: 0,
        height: rect.visibleHeight,
        zIndex: 50,
      }}
      className="bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {children}
    </div>
  ) : (
    // Non-embed / no viewport info: standard fixed positioning
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {children}
    </div>
  );

  return createPortal(content, document.body);
}
