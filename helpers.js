// Community Calendar Helper Functions
// Pure functions for filtering, formatting, and deduplication

// --- Audio Recording ---
window.audioRecorder = null;
window.audioChunks = [];
window.audioBlob = null;
window.audioMimeType = null;

window.startRecording = async function() {
  try {
    var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    var mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
    window.audioRecorder = new MediaRecorder(stream, { mimeType: mimeType });
    window.audioChunks = [];
    window.audioBlob = null;
    window.audioMimeType = mimeType;
    window.audioRecorder.ondataavailable = function(e) {
      if (e.data.size > 0) {
        window.audioChunks.push(e.data);
        window.audioBlob = new Blob(window.audioChunks, { type: mimeType });
      }
    };
    window.audioRecorder.start(500);
    return true;
  } catch(e) {
    console.error('Failed to start recording:', e);
    return false;
  }
};

window.stopRecording = function() {
  if (window.audioRecorder && window.audioRecorder.state === 'recording') {
    window.audioRecorder.stop();
    window.audioRecorder.stream.getTracks().forEach(function(t) { t.stop(); });
  }
};

window.getRecordingFile = function() {
  if (!window.audioBlob) return null;
  var ext = window.audioMimeType === 'audio/webm' ? 'webm' : 'm4a';
  return new File([window.audioBlob], 'recording.' + ext, { type: window.audioMimeType });
};

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

// Return a fixed-size page from a start index.
// Uses one-item overlap so prior page's last item is first on next page.
function getPagedEvents(events, term, startIndex, pageSize) {
  const filtered = filterEvents(events, term) || [];
  const size = pageSize || 50;
  const index = Number.isFinite(startIndex) ? Math.max(0, startIndex) : 0;
  const step = Math.max(1, size - 1);

  if (!filtered.length) {
    if (typeof window !== 'undefined') {
      window._moreHasMore = false;
      window._moreNextIndex = null;
      window._moreHasPrev = false;
      window._morePrevIndex = null;
    }
    return [];
  }

  // During search we keep first-N behavior and hide paging controls in UI.
  if (term) {
    const clampedIndex = Math.max(0, Math.min(index, Math.max(0, filtered.length - 1)));
    const page = filtered.slice(clampedIndex, clampedIndex + size);
    if (typeof window !== 'undefined') {
      window._moreHasMore = false;
      window._moreNextIndex = null;
      window._moreHasPrev = false;
      window._morePrevIndex = null;
    }
    return page;
  }

  const page = filtered.slice(index, index + size);
  const hasMore = (index + size) < filtered.length;
  const nextIndex = hasMore ? (index + step) : null;
  const hasPrev = index > 0;
  const prevIndex = hasPrev ? Math.max(0, index - step) : null;

  if (typeof window !== 'undefined') {
    window._moreHasMore = hasMore;
    window._moreNextIndex = nextIndex;
    window._moreHasPrev = hasPrev;
    window._morePrevIndex = prevIndex;
  }

  return page;
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
    // Normalize start_time to ISO string for consistent dedup across formats
    // e.g. '2026-02-11T18:00:00+00:00' and '2026-02-11T18:00:00.000Z' are the same instant
    const normalizedTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    const key = (e.title || '').trim().toLowerCase() + '|' + normalizedTime;
    if (!groups[key]) {
      groups[key] = { ...e, sources: new Set([e.source]), mergedIds: [e.id] };
    } else {
      // Track all merged event IDs (for picks to work across sources)
      groups[key].mergedIds.push(e.id);
      // Add source (Set handles deduplication automatically)
      groups[key].sources.add(e.source);
      // Prefer non-empty values for other fields
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      if (!groups[key].description && e.description) groups[key].description = e.description;
      if (!groups[key].rrule && e.rrule) groups[key].rrule = e.rrule;
    }
  });
  // Convert sources Set to comma-separated string, with authoritative source first
  // (a source whose name appears in the event location is considered authoritative)
  // Filter mergedIds to only include numeric IDs (exclude synthetic enrichment IDs)
  let result = Object.values(groups).map(e => {
    const sourcesArr = Array.from(e.sources).sort();
    const loc = (e.location || '').toLowerCase();
    if (loc) {
      // Move any source whose name is found in the location to the front
      const authIdx = sourcesArr.findIndex(s => loc.includes(s.toLowerCase()));
      if (authIdx > 0) {
        const [auth] = sourcesArr.splice(authIdx, 1);
        sourcesArr.unshift(auth);
      }
    }
    return {
      ...e,
      source: sourcesArr.join(', '),
      mergedIds: e.mergedIds.filter(id => typeof id === 'number' || /^\d+$/.test(id))
    };
  }).sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));

  // Collapse long-running events (exhibitions, recurring services)
  result = collapseLongRunningEvents(result);

  // Cache the result
  _dedupedEventsCache = result;
  _dedupedEventsCacheKey = cacheKey;
  return result;
}

// For long-running events (exhibitions, recurring services), show only once per week.
// This reduces clutter while keeping events visible throughout their run.
// Weeks are anchored to "today" so the first occurrence shown is today or later,
// then subsequent occurrences appear ~7 days apart.
function collapseLongRunningEvents(events) {
  const MIN_OCCURRENCES = 5;  // Need at least this many to consider "long-running"
  const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

  // Get start of today (midnight UTC)
  const now = new Date();
  const todayStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));

  // Helper: get week number relative to today (0 = this week, 1 = next week, etc.)
  function getWeekFromToday(dateStr) {
    const d = new Date(dateStr);
    const eventDay = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const daysDiff = Math.floor((eventDay - todayStart) / (24 * 60 * 60 * 1000));
    return Math.floor(daysDiff / 7);
  }

  // Group by title + location + time-of-day to identify long-running events
  const groups = {};
  events.forEach(e => {
    const d = new Date(e.start_time);
    const timeOfDay = String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
    const key = (e.title || '').trim().toLowerCase() + '|' + (e.location || '').trim().toLowerCase() + '|' + timeOfDay;
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(e);
  });

  // Identify which event keys are "long-running"
  const longRunningKeys = new Set();
  for (const [key, groupEvents] of Object.entries(groups)) {
    if (groupEvents.length >= MIN_OCCURRENCES) {
      longRunningKeys.add(key);
    }
  }

  // For long-running events, track which weeks we've seen (relative to today)
  // key -> Set of week numbers
  const seenWeeks = {};

  // Build result: for long-running events, include only first occurrence per week
  const result = [];

  events.forEach(e => {
    const d = new Date(e.start_time);
    const timeOfDay = String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
    const key = (e.title || '').trim().toLowerCase() + '|' + (e.location || '').trim().toLowerCase() + '|' + timeOfDay;

    if (longRunningKeys.has(key)) {
      const weekNum = getWeekFromToday(e.start_time);
      if (!seenWeeks[key]) {
        seenWeeks[key] = new Set();
      }
      if (!seenWeeks[key].has(weekNum)) {
        seenWeeks[key].add(weekNum);
        // Mark as recurring so UI can indicate it
        result.push({ ...e, isRecurring: true });
      }
    } else {
      result.push(e);
    }
  });

  return result.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
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

  // Format date for Google Calendar (YYYYMMDDTHHMMSSZ format)
  // Must parse as Date first to handle timezone offset properly
  function formatGoogleDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  }

  const startDate = formatGoogleDate(event.start_time);
  const endDate = event.end_time ? formatGoogleDate(event.end_time) : startDate;

  var params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title || '',
    dates: startDate + '/' + endDate,
    location: event.location || '',
    details: event.description || ''
  });

  if (event.rrule) {
    var rrule = event.rrule.startsWith('RRULE:') ? event.rrule : 'RRULE:' + event.rrule;
    params.set('recur', rrule);
  }

  return 'https://calendar.google.com/calendar/render?' + params.toString();
}

// Format date for ICS (YYYYMMDDTHHMMSSZ)
function formatICSDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
}

// Escape text for ICS format
function escapeICS(text) {
  if (!text) return '';
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n');
}

// Generate ICS content for a single event and trigger download
function downloadEventICS(event) {
  if (!event) return;

  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Community Calendar//Event//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:event-${event.id}@community-calendar`,
    `DTSTAMP:${formatICSDate(new Date().toISOString())}`,
    `DTSTART:${formatICSDate(event.start_time)}`
  ];

  if (event.end_time) {
    lines.push(`DTEND:${formatICSDate(event.end_time)}`);
  }
  if (event.rrule) {
    const rruleStr = event.rrule.startsWith('RRULE:') ? event.rrule : 'RRULE:' + event.rrule;
    lines.push(rruleStr);
  }

  lines.push(`SUMMARY:${escapeICS(event.title)}`);

  if (event.location) {
    lines.push(`LOCATION:${escapeICS(event.location)}`);
  }
  if (event.description) {
    lines.push(`DESCRIPTION:${escapeICS(event.description)}`);
  }
  if (event.url) {
    lines.push(`URL:${event.url}`);
  }

  lines.push('END:VEVENT');
  lines.push('END:VCALENDAR');

  const icsContent = lines.join('\r\n');
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `${(event.title || 'event').replace(/[^a-z0-9]/gi, '_').substring(0, 30)}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ============================================
// Enrichment helpers (RRULE, save/load)
// ============================================

// Local cache for enrichments (keyed by event_id)
let _enrichmentsCache = {};

// Build RRULE string from UI selections using rrule library
// For WEEKLY: pass selectedDays (e.g. ['MO','WE'])
// For MONTHLY: pass ordinal (1-4) and monthDay (e.g. 'TU') for "1st Tuesday"
function buildRRule(frequency, selectedDays, ordinal, monthDay) {
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

  if (frequency === 'MONTHLY' && monthDay && ordinal) {
    options.byweekday = [dayMap[monthDay].nth(ordinal)];
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

// Compute ordinal weekday from a date string, e.g. '2026-03-03' → { ordinal: 1, day: 'TU' }
function getOrdinalWeekday(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr + 'T12:00:00Z'); // noon UTC to avoid timezone issues
  const dayOfMonth = d.getUTCDate();
  const ordinal = Math.ceil(dayOfMonth / 7); // 1st, 2nd, 3rd, 4th, 5th
  const dayCodes = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];
  const day = dayCodes[d.getUTCDay()];
  return { ordinal, day };
}

// Detect recurrence patterns in text — accepts multiple strings, returns first match
function detectRecurrence() {
  var allArgs = arguments;
  for (var i = 0; i < allArgs.length; i++) {
    var result = _detectRecurrenceInText(allArgs[i]);
    if (result) {
      // If WEEKLY with no days, scan ALL arguments for a day name
      if (result.frequency === 'WEEKLY' && result.days.length === 0) {
        var dayMap = { sunday: 'SU', monday: 'MO', tuesday: 'TU', wednesday: 'WE', thursday: 'TH', friday: 'FR', saturday: 'SA' };
        for (var j = 0; j < allArgs.length; j++) {
          if (allArgs[j]) {
            var dayMatch = allArgs[j].toLowerCase().match(/\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?\b/);
            if (dayMatch) {
              result.days = [dayMap[dayMatch[1]]];
              break;
            }
          }
        }
      }
      return result;
    }
  }
  return null;
}

function _detectRecurrenceInText(text) {
  if (!text) return null;
  const lower = text.toLowerCase();
  // Match "every Monday", "on Mondays", "every Wednesday", "on Wednesdays", etc.
  const everyDay = lower.match(/(?:every|on)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?/);
  if (everyDay) {
    const dayMap = { sunday: 'SU', monday: 'MO', tuesday: 'TU', wednesday: 'WE', thursday: 'TH', friday: 'FR', saturday: 'SA' };
    return { frequency: 'WEEKLY', days: [dayMap[everyDay[1]]] };
  }
  // Match "weekly", "every week" — also look for a day name in the same text
  if (/\bevery\s+week\b|\bweekly\b/.test(lower)) {
    const dayMap = { sunday: 'SU', monday: 'MO', tuesday: 'TU', wednesday: 'WE', thursday: 'TH', friday: 'FR', saturday: 'SA' };
    const dayInText = lower.match(/\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?\b/);
    return { frequency: 'WEEKLY', days: dayInText ? [dayMap[dayInText[1]]] : [] };
  }
  // Match "1st Tuesday", "2nd and 4th Friday", etc. — extract ordinal + day
  const ordinalMatch = lower.match(/(\d+)(?:st|nd|rd|th)\s+(?:and\s+\d+(?:st|nd|rd|th)\s+)?(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/);
  if (ordinalMatch) {
    const dayMap = { sunday: 'SU', monday: 'MO', tuesday: 'TU', wednesday: 'WE', thursday: 'TH', friday: 'FR', saturday: 'SA' };
    return { frequency: 'MONTHLY', days: [], ordinal: parseInt(ordinalMatch[1]), monthDay: dayMap[ordinalMatch[2]] };
  }
  // Match word-form ordinals: "first Wednesday", "second Tuesday", "third Friday", "fourth Monday"
  const wordOrdinalMap = { first: 1, second: 2, third: 3, fourth: 4 };
  const wordOrdinalMatch = lower.match(/(first|second|third|fourth)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/);
  if (wordOrdinalMatch) {
    const dayMap = { sunday: 'SU', monday: 'MO', tuesday: 'TU', wednesday: 'WE', thursday: 'TH', friday: 'FR', saturday: 'SA' };
    return { frequency: 'MONTHLY', days: [], ordinal: wordOrdinalMap[wordOrdinalMatch[1]], monthDay: dayMap[wordOrdinalMatch[2]] };
  }
  // Match "biweekly", "monthly"
  if (/\bmonthly\b/.test(lower)) return { frequency: 'MONTHLY', days: [] };
  return null;
}

// Expand enrichments with RRULEs into virtual events within a date range
function expandEnrichments(enrichments, fromDateStr, toDateStr) {
  if (!enrichments || !enrichments.length) return [];

  const fromDate = new Date(fromDateStr);
  const toDate = new Date(toDateStr);
  const virtualEvents = [];

  enrichments.forEach(enrichment => {
    if (!enrichment.rrule || !enrichment.start_time || !enrichment.title) return;

    try {
      // Parse the original start_time to get time-of-day
      const dtstart = new Date(enrichment.start_time);

      // Build the full RRULE string with dtstart
      const ruleStr = enrichment.rrule.startsWith('RRULE:') ? enrichment.rrule : 'RRULE:' + enrichment.rrule;
      const rule = rrule.RRule.fromString(ruleStr);

      // Create new rule with dtstart set
      const ruleWithStart = new rrule.RRule({
        ...rule.origOptions,
        dtstart: dtstart
      });

      // Get occurrences within the date range
      const occurrences = ruleWithStart.between(fromDate, toDate, true);

      occurrences.forEach(date => {
        // Build ISO string preserving the original time-of-day
        const isoDate = date.toISOString();

        virtualEvents.push({
          id: 'enrichment-' + enrichment.id + '-' + isoDate,
          title: enrichment.title,
          start_time: isoDate,
          end_time: enrichment.end_time || null,
          location: enrichment.location || null,
          description: enrichment.description || null,
          url: enrichment.url || null,
          source: 'Picks: ' + (enrichment.curator_name || 'curator'),
          city: enrichment.city || null,
          rrule: enrichment.rrule,
          _enrichment_id: enrichment.id
        });
      });
    } catch (e) {
      console.error('Error expanding enrichment', enrichment.id, e);
    }
  });

  return virtualEvents;
}

// Get the next occurrence of a recurring event from today (or the original date if not recurring)
// enrichments: array of enrichment objects (from enrichments DataSource)
// eventId: the event ID to look up
// originalStartTime: fallback if no rrule
function getNextOccurrence(enrichments, eventId, originalStartTime) {
  if (!originalStartTime) return '';
  if (!enrichments || !Array.isArray(enrichments) || !eventId) return originalStartTime;

  var enrichment = enrichments.find(function(e) { return e.event_id == eventId; });
  if (!enrichment || !enrichment.rrule) return originalStartTime;

  try {
    var ruleStr = enrichment.rrule.startsWith('RRULE:') ? enrichment.rrule : 'RRULE:' + enrichment.rrule;
    var rule = rrule.RRule.fromString(ruleStr);
    var dtstart = new Date(enrichment.start_time || originalStartTime);
    var ruleWithStart = new rrule.RRule({
      ...rule.origOptions,
      dtstart: dtstart
    });
    var now = new Date();
    var next = ruleWithStart.after(now, true);
    console.log('getNextOccurrence', { eventId: eventId, enrichmentsLen: enrichments.length, rrule: enrichment.rrule, next: next ? next.toISOString() : null, original: originalStartTime });
    return next ? next.toISOString() : originalStartTime;
  } catch (e) {
    console.error('getNextOccurrence error', e);
    return originalStartTime;
  }
}

// Export for browser (attach to window)
if (typeof window !== 'undefined') {
  window.toggleDay = toggleDay;
  var _filterEvents = filterEvents;
  window.filterEvents = function(events, term) {
    return window.xsTrace ? window.xsTrace("filterEvents", function() { return _filterEvents(events, term); }) : _filterEvents(events, term);
  };
  window.getPagedEvents = getPagedEvents;
  window.getDescriptionSnippet = getDescriptionSnippet;
  window.formatDayOfWeek = formatDayOfWeek;
  window.formatMonthDay = formatMonthDay;
  window.formatDate = formatDate;
  window.formatTime = formatTime;
  window.truncate = truncate;
  window.getSourceCounts = getSourceCounts;
  var _dedupeEvents = dedupeEvents;
  window.dedupeEvents = function(events) {
    return window.xsTrace ? window.xsTrace("dedupeEvents", function() { return _dedupeEvents(events); }) : _dedupeEvents(events);
  };
  window.collapseLongRunningEvents = collapseLongRunningEvents;
  window.clearDedupeCache = clearDedupeCache;
  window.isEventPicked = isEventPicked;
  window.buildGoogleCalendarUrl = buildGoogleCalendarUrl;
  window.downloadEventICS = downloadEventICS;
  // Enrichment helpers
  window.buildRRule = buildRRule;
  window.parseRRule = parseRRule;
  window.saveEnrichment = saveEnrichment;
  window.loadEnrichment = loadEnrichment;
  window.loadAllEnrichments = loadAllEnrichments;
  window.getEnrichmentFromCache = getEnrichmentFromCache;
  window.expandEnrichments = expandEnrichments;
  window.getNextOccurrence = getNextOccurrence;
  window.formatPickDate = function(enrichments, eventId, startTime) {
    var d = getNextOccurrence(enrichments, eventId, startTime);
    var day = formatDayOfWeek(d);
    var md = formatMonthDay(d);
    var t = formatTime(startTime);
    return day + ' ' + md + (t ? ', ' + t : '');
  };
  window.detectRecurrence = detectRecurrence;
  window.getOrdinalWeekday = getOrdinalWeekday;
}
