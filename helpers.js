// Community Calendar Helper Functions
// Pure functions for filtering, formatting, and deduplication

// Filter events by search term (searches title, location, source, and description)
function filterEvents(events, term) {
  if (!events) return events || [];
  if (!term) return events;
  const lower = term.toLowerCase();
  return events.filter(e =>
    (e.title && e.title.toLowerCase().includes(lower)) ||
    (e.location && e.location.toLowerCase().includes(lower)) ||
    (e.source && e.source.toLowerCase().includes(lower)) ||
    (e.description && e.description.toLowerCase().includes(lower))
  );
}

// Get description snippet with context around search term (returns null if no match in description)
function getDescriptionSnippet(description, term) {
  if (!description || !term) return null;
  const lower = description.toLowerCase();
  const termLower = term.toLowerCase();
  const idx = lower.indexOf(termLower);
  if (idx === -1) return null;

  // Extract context window (40 chars before and after)
  const contextSize = 40;
  const start = Math.max(0, idx - contextSize);
  const end = Math.min(description.length, idx + term.length + contextSize);

  let snippet = '';
  if (start > 0) snippet += '...';
  snippet += description.substring(start, idx);
  snippet += '**' + description.substring(idx, idx + term.length) + '**';
  snippet += description.substring(idx + term.length, end);
  if (end < description.length) snippet += '...';

  return snippet;
}

// Format day of week (using UTC since times were stored as local but marked UTC)
function formatDayOfWeek(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' });
}

// Format month and day (using UTC since times were stored as local but marked UTC)
function formatMonthDay(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

// Format date for display
function formatDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

// Format time for display
// Times were stored as local times but Supabase added +00:00, so use UTC values directly
function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const hours = d.getUTCHours();
  const mins = d.getUTCMinutes();
  // Skip midnight times (likely means time unknown)
  if (hours === 0 && mins === 0) return '';
  // Format as 12-hour time
  const h = hours % 12 || 12;
  const ampm = hours < 12 ? 'AM' : 'PM';
  const m = mins.toString().padStart(2, '0');
  return `${h}:${m} ${ampm}`;
}

// Truncate text with ellipsis
function truncate(text, maxLen) {
  if (!text) return '';
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trim() + '...';
}

// Aggregate events by source, return sorted array of {source, count}
function getSourceCounts(events) {
  if (!events || !events.length) return [];
  const counts = {};
  events.forEach(e => {
    const src = e.source || 'Unknown';
    counts[src] = (counts[src] || 0) + 1;
  });
  return Object.entries(counts)
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count);
}

// Deduplicate events: merge events with same title + start_time, combine sources
// Cache variables (module-level for browser, will be on window)
let _dedupedEventsCache = null;
let _dedupedEventsCacheKey = null;

function dedupeEvents(events) {
  if (!events || !events.length) return [];

  // Use cache if events array hasn't changed
  const cacheKey = events.length + '-' + (events[0]?.id || '');
  if (_dedupedEventsCacheKey === cacheKey && _dedupedEventsCache) {
    return _dedupedEventsCache;
  }

  const groups = {};
  events.forEach(e => {
    const key = (e.title || '').trim().toLowerCase() + '|' + (e.start_time || '');
    if (!groups[key]) {
      groups[key] = { ...e, sources: [e.source], mergedIds: [e.id] };
    } else {
      // Track all merged event IDs (for picks to work across sources)
      groups[key].mergedIds.push(e.id);
      // Add source if not already present
      if (!groups[key].sources.includes(e.source)) {
        groups[key].sources.push(e.source);
      }
      // Prefer non-empty values for other fields
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      if (!groups[key].description && e.description) groups[key].description = e.description;
    }
  });
  // Convert sources array to comma-separated string
  const result = Object.values(groups).map(e => ({
    ...e,
    source: e.sources.sort().join(', ')
  })).sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));

  // Cache the result
  _dedupedEventsCache = result;
  _dedupedEventsCacheKey = cacheKey;
  return result;
}

// Clear dedupe cache (useful for testing)
function clearDedupeCache() {
  _dedupedEventsCache = null;
  _dedupedEventsCacheKey = null;
}

// Check if an event is picked (supports merged IDs from cross-source duplicates)
function isEventPicked(mergedIds, picks) {
  if (!picks || !Array.isArray(picks)) return false;
  if (!mergedIds) return false;
  // mergedIds can be an array (from dedupe) or a single ID
  const ids = Array.isArray(mergedIds) ? mergedIds : [mergedIds];
  return picks.some(p => ids.some(id => p.event_id == id));
}

// Build Google Calendar URL for an event
function buildGoogleCalendarUrl(event) {
  if (!event) return '';

  function formatGoogleDate(isoString) {
    if (!isoString) return '';
    return isoString.replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  }

  const startDate = formatGoogleDate(event.start_time);
  const endDate = event.end_time ? formatGoogleDate(event.end_time) : startDate;

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title || '',
    dates: startDate + '/' + endDate,
    location: event.location || '',
    details: event.description || ''
  });

  return 'https://calendar.google.com/calendar/render?' + params.toString();
}

// Export for browser (attach to window)
if (typeof window !== 'undefined') {
  window.filterEvents = filterEvents;
  window.getDescriptionSnippet = getDescriptionSnippet;
  window.formatDayOfWeek = formatDayOfWeek;
  window.formatMonthDay = formatMonthDay;
  window.formatDate = formatDate;
  window.formatTime = formatTime;
  window.truncate = truncate;
  window.getSourceCounts = getSourceCounts;
  window.dedupeEvents = dedupeEvents;
  window.clearDedupeCache = clearDedupeCache;
  window.isEventPicked = isEventPicked;
  window.buildGoogleCalendarUrl = buildGoogleCalendarUrl;
}
