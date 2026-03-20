const LEGACY_MAP = { grid: 'grid-nodesc', gridcompact: 'grid-noimage', gridtile: 'grid-tile' };

export function parseCardStyle(styleId) {
  const resolved = LEGACY_MAP[styleId] || styleId;
  if (resolved.startsWith('grid-')) {
    return { layout: 'grid', baseStyle: resolved.slice(5), resolvedId: resolved };
  }
  return { layout: 'masonry', baseStyle: resolved, resolvedId: resolved };
}

export function isGridLayout(styleId) {
  return parseCardStyle(styleId).layout === 'grid';
}

export function getColumnCount(styleId, rawColumnCount) {
  const { baseStyle } = parseCardStyle(styleId);
  if (['list', 'compactlist', 'datelist'].includes(styleId)) return 1;
  if (['compact'].includes(baseStyle)) return rawColumnCount >= 4 ? 2 : 1;
  if (['split', 'splitimage'].includes(baseStyle)) return Math.min(rawColumnCount, 2);
  if (['ticket'].includes(baseStyle)) return Math.max(1, Math.min(rawColumnCount - 1, 3));
  return rawColumnCount;
}
