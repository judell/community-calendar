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

// ============================================
// Enrichment helpers (RRULE, save/load)
// ============================================

// Local cache for enrichments (keyed by event_id)
let _enrichmentsCache = {};

// Build RRULE string from UI selections using rrule library
function buildRRule(frequency, selectedDays) {
  if (!frequency || frequency === 'none') return null;

  // Map day codes to rrule weekday constants
  const dayMap = {
    'SU': rrule.RRule.SU,
    'MO': rrule.RRule.MO,
    'TU': rrule.RRule.TU,
    'WE': rrule.RRule.WE,
    'TH': rrule.RRule.TH,
    'FR': rrule.RRule.FR,
    'SA': rrule.RRule.SA
  };

  const options = {
    freq: frequency === 'WEEKLY' ? rrule.RRule.WEEKLY : rrule.RRule.MONTHLY
  };

  if (frequency === 'WEEKLY' && selectedDays && selectedDays.length > 0) {
    options.byweekday = selectedDays.map(d => dayMap[d]).filter(Boolean);
  }

  const rule = new rrule.RRule(options);
  // Return just the rule part without "RRULE:" prefix (we add that in ICS generation)
  return rule.toString().replace('RRULE:', '');
}

// Parse RRULE string back to frequency + days for UI
function parseRRule(rruleString) {
  if (!rruleString) return { frequency: 'none', days: [] };

  try {
    // Add RRULE: prefix if not present for parsing
    const fullRule = rruleString.startsWith('RRULE:') ? rruleString : 'RRULE:' + rruleString;
    const rule = rrule.RRule.fromString(fullRule);

    const freqMap = {
      [rrule.RRule.WEEKLY]: 'WEEKLY',
      [rrule.RRule.MONTHLY]: 'MONTHLY',
      [rrule.RRule.DAILY]: 'DAILY',
      [rrule.RRule.YEARLY]: 'YEARLY'
    };

    const dayCodeMap = {
      0: 'MO', 1: 'TU', 2: 'WE', 3: 'TH', 4: 'FR', 5: 'SA', 6: 'SU'
    };

    const frequency = freqMap[rule.options.freq] || 'none';
    const days = (rule.options.byweekday || []).map(d => {
      // byweekday can be Weekday objects or numbers
      const dayNum = typeof d === 'number' ? d : d.weekday;
      return dayCodeMap[dayNum];
    }).filter(Boolean);

    return { frequency, days };
  } catch (e) {
    console.error('Error parsing RRULE:', e);
    return { frequency: 'none', days: [] };
  }
}

// Save enrichment to Supabase (upsert)
async function saveEnrichment(eventId, data) {
  if (!window.authSession) {
    alert('Please sign in to save enrichments');
    return null;
  }

  const headers = {
    'apikey': window.SUPABASE_KEY,
    'Authorization': 'Bearer ' + window.authSession.access_token,
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates,return=representation'
  };

  const payload = {
    event_id: eventId,
    curator_id: window.authUser.id,
    rrule: data.rrule || null,
    url: data.url || null,
    description: data.description || null,
    location: data.location || null,
    end_time: data.end_time || null,
    categories: data.categories || null,
    notes: data.notes || null,
    updated_at: new Date().toISOString()
  };

  const url = `${window.SUPABASE_URL}/rest/v1/event_enrichments`;
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    const result = await res.json();
    // Update local cache
    _enrichmentsCache[eventId] = result[0] || payload;
    return _enrichmentsCache[eventId];
  } else {
    console.error('Error saving enrichment:', res.status, await res.text());
    return null;
  }
}

// Load enrichment from cache or fetch from Supabase
async function loadEnrichment(eventId) {
  // Return cached if available
  if (_enrichmentsCache[eventId]) {
    return _enrichmentsCache[eventId];
  }

  if (!window.authSession) return null;

  const headers = {
    'apikey': window.SUPABASE_KEY,
    'Authorization': 'Bearer ' + window.authSession.access_token
  };

  const url = `${window.SUPABASE_URL}/rest/v1/event_enrichments?event_id=eq.${eventId}&curator_id=eq.${window.authUser.id}`;
  const res = await fetch(url, { headers });

  if (res.ok) {
    const data = await res.json();
    if (data && data.length > 0) {
      _enrichmentsCache[eventId] = data[0];
      return data[0];
    }
  }
  return null;
}

// Load all enrichments for current user (for bulk prefetch)
async function loadAllEnrichments() {
  if (!window.authSession) return [];

  const headers = {
    'apikey': window.SUPABASE_KEY,
    'Authorization': 'Bearer ' + window.authSession.access_token
  };

  const url = `${window.SUPABASE_URL}/rest/v1/event_enrichments?curator_id=eq.${window.authUser.id}`;
  const res = await fetch(url, { headers });

  if (res.ok) {
    const data = await res.json();
    // Populate cache
    data.forEach(e => {
      _enrichmentsCache[e.event_id] = e;
    });
    return data;
  }
  return [];
}

// Get enrichment from cache (synchronous, for UI)
function getEnrichmentFromCache(eventId) {
  return _enrichmentsCache[eventId] || null;
}

// Toggle a day in/out of an array (for RRULE day picker)
function toggleDay(days, day) {
  return days.includes(day) ? days.filter(d => d !== day) : [...days, day];
}

// Export for browser (attach to window)
if (typeof window !== 'undefined') {
  window.toggleDay = toggleDay;
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
  // Enrichment helpers
  window.buildRRule = buildRRule;
  window.parseRRule = parseRRule;
  window.saveEnrichment = saveEnrichment;
  window.loadEnrichment = loadEnrichment;
  window.loadAllEnrichments = loadAllEnrichments;
  window.getEnrichmentFromCache = getEnrichmentFromCache;
}
