// Community Calendar Helper Functions — ES module port
// Ported from root helpers.js, removing window.* assignments

import { RRule } from 'rrule';
import { categoryList } from './categories.js';

// --- Active categories from events ---
export function getActiveCategories(events) {
  const counts = {};
  (events || []).forEach(e => {
    if (e.category) counts[e.category] = (counts[e.category] || 0) + 1;
  });
  return categoryList
    .filter(c => counts[c])
    .map(c => ({ name: c, label: c + ' (' + counts[c] + ')' }));
}

// --- Filter events by search term and category ---
export function filterEvents(events, term, category) {
  if (!events) return [];
  let result = events;
  if (category) {
    result = result.filter(e => e.category === category);
  }
  if (!term) return result;
  const lower = term.toLowerCase();
  return result.filter(e =>
    (e.title && e.title.toLowerCase().includes(lower)) ||
    (e.location && e.location.toLowerCase().includes(lower)) ||
    (e.source && e.source.toLowerCase().includes(lower)) ||
    (e.description && e.description.toLowerCase().includes(lower))
  );
}

// --- Cumulative events (for cards view infinite scroll) ---
// Returns { events, hasMore }
export function getCumulativeEvents(events, term, count, category) {
  const filtered = filterEvents(events, term, category);
  const n = (Number.isFinite(count) && count > 0) ? count : 50;
  if (!filtered.length) {
    return { events: [], hasMore: false };
  }
  if (term) {
    return { events: filtered, hasMore: false };
  }
  return {
    events: filtered.slice(0, n),
    hasMore: filtered.length > n,
  };
}

// --- Description snippet with search highlight ---
export function getDescriptionSnippet(description, term) {
  if (!description || !term) return null;
  description = description.replace(/[\r\n]+/g, ' ').replace(/ {2,}/g, ' ');
  const lower = description.toLowerCase();
  const termLower = term.toLowerCase();
  const idx = lower.indexOf(termLower);
  if (idx === -1) return null;

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

// --- Date/time formatting ---
// Times are stored as local times with +00:00 marker — use UTC values directly
export function formatDayOfWeek(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' });
}

export function formatMonthDay(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

// Return separate month/day/weekday parts for date chip rendering
export function formatDateParts(isoString) {
  if (!isoString) return { month: '', day: '', weekday: '' };
  const d = new Date(isoString);
  return {
    month: d.toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' }).toUpperCase(),
    day: String(d.getUTCDate()),
    weekday: d.toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' }),
  };
}

export function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const hours = d.getUTCHours();
  const mins = d.getUTCMinutes();
  if (hours === 0 && mins === 0) return '';
  const h = hours % 12 || 12;
  const ampm = hours < 12 ? 'AM' : 'PM';
  const m = mins.toString().padStart(2, '0');
  return `${h}:${m} ${ampm}`;
}

// --- Snippet extraction ---
export function getSnippet(description, title) {
  if (!description) return null;

  let text = String(description);

  // Preserve line breaks from HTML before stripping tags
  if (/<[a-z][\s\S]*>/i.test(text)) {
    text = text.replace(/<\s*br\s*\/?>/gi, '\n');
    text = text.replace(/<\s*\/p\s*>/gi, '\n');
    text = text.replace(/<\s*li\s*>/gi, '\n');
    text = text.replace(/<\s*\/li\s*>/gi, '\n');
    text = text.replace(/<\/[^>]+>/g, ' ');
    const doc = new DOMParser().parseFromString(text, 'text/html');
    text = doc.body.textContent || '';
  }

  text = text.replace(/https?:\/\/\S+/g, '');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/\\([*_\[\](){}+#>|`~])/g, '$1');
  text = text.replace(/([a-z])([A-Z])/g, '$1 $2');
  text = text.replace(/[\t\r]+/g, ' ').replace(/ {2,}/g, ' ');

  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

  const labelPrefix = /^\w+(\s+\w+){0,2}\s*:\s*/;
  const ctaPrefix = /^(back to|buy|register|sign up|rsvp|tickets?|click|tap|view|see all|read more|get|call or text|call or email)\b/i;
  const badAnywhere = /\b(zoom|meeting id|passcode|one tap|meeting url|webex|microsoft teams|google meet|agenda|packet|minutes|prohibited|not permitted|are not allowed|from almost anywhere in the world|from anywhere in the world)\b/i;
  const moneyOrPrice = /(\$\s*\d|\bprice\b|\bfee\b|\badmission\b|\bfree but\b)/i;

  const normTitle = title ? title.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() : null;
  function normText(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }

  function salvageLabel(line) {
    if (!labelPrefix.test(line)) return line;
    const rest = line.replace(labelPrefix, '').trim();
    if (rest.length < 30) return '';
    if (!/\b(the|a|an|and|or|for|with|to|from|at|in|on|by|is|are|was|will|this|that)\b/i.test(rest)) return '';
    if (labelPrefix.test(rest)) return '';
    return rest;
  }

  function scoreLine(line) {
    if (line.length < 15) return -999;
    line = salvageLabel(line);
    if (!line) return -999;
    if (ctaPrefix.test(line)) return -999;
    if (badAnywhere.test(line)) return -999;

    let score = 0;
    if (/[.!?]/.test(line)) score += 3;
    if (/\b(the|a|an|and|or|but|for|with|to|from|at|in|on|by)\b/i.test(line)) score += 2;
    if (/\b(join|learn|discover|explore|enjoy|experience|celebrate|meet|hear|watch|featuring|presents)\b/i.test(line)) score += 2;
    if (moneyOrPrice.test(line)) score -= 3;
    const digitCount = (line.match(/\d/g) || []).length;
    if (digitCount >= 6) score -= 3;
    if (line.length < 25 && !/[.!?]/.test(line)) score -= 3;
    if (!/\b(the|a|an|is|are|was|will|has|have|can|do|and|but|for|with|from)\b/i.test(line) && line.length < 40) score -= 3;

    if (normTitle) {
      const nt = normText(line);
      if (nt === normTitle) score -= 6;
      else if (nt.indexOf(normTitle) >= 0 && nt.length - normTitle.length < 15) score -= 4;
    }

    if (line.length >= 40) score += 1;
    if (line.length > 220) score -= 2;

    return score;
  }

  let best = null;
  let bestScore = -999;
  for (let i = 0; i < lines.length; i++) {
    const parts = lines[i].split(/(?<=[.!?])\s+/);
    for (let j = 0; j < parts.length; j++) {
      const part = parts[j].trim();
      if (!part) continue;
      const s = scoreLine(part);
      if (s > bestScore) {
        bestScore = s;
        best = part;
      }
    }
  }

  if (!best || bestScore < 0) return null;

  if (best.length <= 100) return best;
  let cut = best.lastIndexOf(' ', 100);
  if (cut < 40) cut = 100;
  const snippet = best.substring(0, cut).replace(/[\s(,\-;:]+$/, '');
  return snippet + '...';
}

// --- Deduplication ---
let _dedupedEventsCache = null;
let _dedupedEventsLastInput = null;

export function dedupeEvents(events) {
  if (!events || !events.length) return [];

  if (events === _dedupedEventsLastInput && _dedupedEventsCache) {
    return _dedupedEventsCache;
  }
  _dedupedEventsLastInput = events;

  const groups = {};
  events.forEach(e => {
    const normalizedTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    const key = (e.title || '').trim().toLowerCase() + '|' + normalizedTime;
    if (!groups[key]) {
      groups[key] = { ...e, sources: new Set((e.source || '').split(',').map(s => s.trim()).filter(Boolean)), mergedIds: [e.id] };
    } else {
      groups[key].mergedIds.push(e.id);
      (e.source || '').split(',').map(s => s.trim()).filter(Boolean).forEach(s => groups[key].sources.add(s));
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      if (!groups[key].description && e.description) groups[key].description = e.description;
      if (!groups[key].rrule && e.rrule) groups[key].rrule = e.rrule;
      if (!groups[key].cluster_id && e.cluster_id) groups[key].cluster_id = e.cluster_id;
    }
  });

  let result = Object.values(groups).map(e => {
    const sourcesArr = Array.from(e.sources).sort();
    const loc = (e.location || '').toLowerCase();
    if (loc) {
      const authIdx = sourcesArr.findIndex(s => loc.includes(s.toLowerCase()));
      if (authIdx > 0) {
        const [auth] = sourcesArr.splice(authIdx, 1);
        sourcesArr.unshift(auth);
      }
    }
    return {
      ...e,
      source: sourcesArr.join(', '),
      mergedIds: e.mergedIds.filter(id => typeof id === 'number' || /^\d+$/.test(id)),
    };
  }).sort((a, b) => {
    const timeCmp = (a.start_time || '').localeCompare(b.start_time || '');
    if (timeCmp !== 0) return timeCmp;
    const ca = a.cluster_id != null ? a.cluster_id : null;
    const cb = b.cluster_id != null ? b.cluster_id : null;
    if (ca != null && cb != null) {
      if (ca !== cb) return ca - cb;
      return (a.title || '').localeCompare(b.title || '');
    }
    if (ca != null) return -1;
    if (cb != null) return 1;
    return (a.title || '').localeCompare(b.title || '');
  });

  result = collapseLongRunningEvents(result);
  _dedupedEventsCache = result;
  return result;
}

// --- Collapse long-running events ---
export function collapseLongRunningEvents(events) {
  const MIN_OCCURRENCES = 5;

  const now = new Date();
  const todayStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));

  function getWeekFromToday(dateStr) {
    const d = new Date(dateStr);
    const eventDay = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
    const daysDiff = Math.floor((eventDay - todayStart) / (24 * 60 * 60 * 1000));
    return Math.floor(daysDiff / 7);
  }

  const groups = {};
  events.forEach(e => {
    const d = new Date(e.start_time);
    const timeOfDay = String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
    const key = (e.title || '').trim().toLowerCase() + '|' + (e.location || '').trim().toLowerCase() + '|' + timeOfDay;
    if (!groups[key]) groups[key] = [];
    groups[key].push(e);
  });

  const longRunningKeys = new Set();
  for (const [key, groupEvents] of Object.entries(groups)) {
    if (groupEvents.length >= MIN_OCCURRENCES) {
      longRunningKeys.add(key);
    }
  }

  const seenWeeks = {};
  const result = [];

  events.forEach(e => {
    const d = new Date(e.start_time);
    const timeOfDay = String(d.getUTCHours()).padStart(2, '0') + ':' + String(d.getUTCMinutes()).padStart(2, '0');
    const key = (e.title || '').trim().toLowerCase() + '|' + (e.location || '').trim().toLowerCase() + '|' + timeOfDay;

    if (longRunningKeys.has(key)) {
      const weekNum = getWeekFromToday(e.start_time);
      if (!seenWeeks[key]) seenWeeks[key] = new Set();
      if (!seenWeeks[key].has(weekNum)) {
        seenWeeks[key].add(weekNum);
        result.push({ ...e, isRecurring: true });
      }
    } else {
      result.push(e);
    }
  });

  return result.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
}

// --- Filter hidden sources ---
export function filterHiddenSources(events, hiddenSources) {
  if (!hiddenSources || !hiddenSources.length) return events;
  if (!events) return [];
  return events.filter(e => {
    if (!e.source) return true;
    const sources = e.source.split(',').map(s => s.trim()).filter(Boolean);
    return !sources.every(s => hiddenSources.indexOf(s) >= 0);
  });
}

// --- Expand enrichments with RRULEs into virtual events ---
export function expandEnrichments(enrichments, fromDateStr, toDateStr) {
  if (!enrichments || !enrichments.length) return [];

  const fromDate = new Date(fromDateStr);
  const toDate = new Date(toDateStr);
  const virtualEvents = [];

  enrichments.forEach(enrichment => {
    if (!enrichment.rrule || !enrichment.start_time || !enrichment.title) return;

    try {
      const dtstart = new Date(enrichment.start_time);
      const ruleStr = enrichment.rrule.startsWith('RRULE:') ? enrichment.rrule : 'RRULE:' + enrichment.rrule;
      const rule = RRule.fromString(ruleStr);

      const ruleWithStart = new RRule({
        ...rule.origOptions,
        dtstart,
      });

      const occurrences = ruleWithStart.between(fromDate, toDate, true);

      occurrences.forEach(date => {
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
          _enrichment_id: enrichment.id,
        });
      });
    } catch (e) {
      // skip bad enrichments
    }
  });

  return virtualEvents;
}

// --- Masonry layout ---
export function getResponsiveColumnCount(width) {
  const w = width || (typeof window !== 'undefined' ? window.innerWidth : 1400);
  if (w >= 1100) return 4;
  if (w >= 800) return 3;
  if (w >= 500) return 2;
  return 1;
}

export function getMasonryColumns(events, numColumns) {
  const n = numColumns || 4;
  const columns = [];
  const heights = [];
  for (let i = 0; i < n; i++) { columns.push([]); heights.push(0); }
  if (!events || !events.length) return columns;

  for (let j = 0; j < events.length; j++) {
    const ev = events[j];
    let h = 70;
    if (ev.image_url) h += 170;
    h += Math.ceil(((ev.title || '').length) / 28) * 20;
    if (ev.location) h += 20;
    if (ev.source) h += 18;
    if (ev.description) {
      const plainDesc = ev.description.replace(/<[^>]+>/g, '');
      h += Math.min(80, Math.ceil(plainDesc.length / 35) * 18);
    }

    let minH = heights[0], minIdx = 0;
    for (let k = 1; k < n; k++) {
      if (heights[k] < minH) { minH = heights[k]; minIdx = k; }
    }
    columns[minIdx].push(ev);
    heights[minIdx] += h;
  }
  return columns;
}

// --- Google Calendar URL ---
export function buildGoogleCalendarUrl(event) {
  if (!event) return '';

  function formatGoogleDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  }

  const startDate = formatGoogleDate(event.start_time);
  const endDate = event.end_time ? formatGoogleDate(event.end_time) : startDate;

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title || '',
    dates: startDate + '/' + endDate,
    location: event.location || '',
    details: event.description || '',
  });

  if (event.rrule) {
    const rruleStr = event.rrule.startsWith('RRULE:') ? event.rrule : 'RRULE:' + event.rrule;
    params.set('recur', rruleStr);
  }

  return 'https://calendar.google.com/calendar/render?' + params.toString();
}

// --- ICS download ---
function formatICSDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
}

function escapeICS(text) {
  if (!text) return '';
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n');
}

export function downloadEventICS(event) {
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
    `DTSTART:${formatICSDate(event.start_time)}`,
  ];

  if (event.end_time) lines.push(`DTEND:${formatICSDate(event.end_time)}`);
  if (event.rrule) {
    const rruleStr = event.rrule.startsWith('RRULE:') ? event.rrule : 'RRULE:' + event.rrule;
    lines.push(rruleStr);
  }

  lines.push(`SUMMARY:${escapeICS(event.title)}`);
  if (event.location) lines.push(`LOCATION:${escapeICS(event.location)}`);
  if (event.description) lines.push(`DESCRIPTION:${escapeICS(event.description)}`);
  if (event.url) lines.push(`URL:${event.url}`);

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
