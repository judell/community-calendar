import { useState, useEffect } from 'react';
import { getResponsiveColumnCount } from '../lib/helpers.js';

export function useColumnCount() {
  const [columnCount, setColumnCount] = useState(() => getResponsiveColumnCount());

  useEffect(() => {
    function handleResize() {
      setColumnCount(getResponsiveColumnCount());
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return columnCount;
}
