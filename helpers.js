// Community Calendar Helper Functions
// Pure functions for filtering, formatting, and deduplication

// --- Categories (derived from categories.json, loaded in index.html) ---
var CATEGORY_NAMES = {};
window.categoryColorMap = {};
window._categories.forEach(function(c) {
  CATEGORY_NAMES[c.name] = true;
  window.categoryColorMap[c.name] = { label: c.label, background: c.background };
});
window.categoryList = window._categories.map(function(c) { return c.name; });
window.getActiveCategories = function(events) {
  var counts = {};
  (events || []).forEach(function(e) { if (e.category) counts[e.category] = (counts[e.category] || 0) + 1; });
  return window.categoryList.filter(function(c) { return counts[c]; }).map(function(c) { return { name: c, label: c + ' (' + counts[c] + ')' }; });
};

// --- URL sync for category filter ---
window.syncCategoryParam = function(category) {
  var url = new URL(window.location);
  if (category) {
    url.searchParams.set('category', category);
  } else {
    url.searchParams.delete('category');
  }
  window.history.replaceState({}, '', url);
};

// --- URL sync for search filter (debounced) ---
var _searchSyncTimer = null;
window.syncSearchParam = function(search) {
  clearTimeout(_searchSyncTimer);
  _searchSyncTimer = setTimeout(function() {
    var url = new URL(window.location);
    if (search) {
      url.searchParams.set('search', search);
    } else {
      url.searchParams.delete('search');
    }
    window.history.replaceState({}, '', url);
  }, 500);
};

// --- Cluster Colors ---
const CLUSTER_COLORS = ['#6b9bd2', '#7bc47f', '#d4a04a'];
window.clusterBorder = function(clusterId, filtered) {
  if (clusterId == null || filtered) return 'none';
  return '3px solid ' + CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
};

// --- Image Resize (client-side, before upload) ---
// Converts any image (including HEIC via browser decode) to JPEG under maxBytes
window.resizeImageFile = function(file, maxBytes) {
  maxBytes = maxBytes || 3500000; // ~3.5MB raw → ~4.8MB base64, under Claude's 5MB limit
  return new Promise(function(resolve, reject) {
    var img = new Image();
    var url = URL.createObjectURL(file);
    img.onload = function() {
      URL.revokeObjectURL(url);
      var canvas = document.createElement('canvas');
      var w = img.width, h = img.height;
      // Try at full resolution first, then scale down
      var scale = 1.0;
      var attempt = function() {
        canvas.width = Math.round(w * scale);
        canvas.height = Math.round(h * scale);
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(function(blob) {
          if (!blob) { reject(new Error('Canvas toBlob failed')); return; }
          if (blob.size <= maxBytes || scale <= 0.2) {
            resolve(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
          } else {
            scale *= 0.7;
            attempt();
          }
        }, 'image/jpeg', 0.85);
      };
      attempt();
    };
    img.onerror = function() {
      URL.revokeObjectURL(url);
      // If browser can't decode (e.g. HEIC on non-Safari), pass through original
      resolve(file);
    };
    img.src = url;
  });
};

// Append UTC offset to a naive datetime string using an IANA timezone.
// E.g., applyTimezoneOffset("2025-01-15T19:00:00", "America/Los_Angeles") → "2025-01-15T19:00:00-08:00"
// Returns the string unchanged if it already has an offset or Z suffix.
window.applyTimezoneOffset = function(naiveDatetime, timezone) {
  if (!timezone || !naiveDatetime) return naiveDatetime;
  if (/[+-]\d{2}(:\d{2})?$/.test(naiveDatetime) || naiveDatetime.endsWith('Z')) {
    return naiveDatetime;
  }
  var fakeUtc = new Date(naiveDatetime + 'Z');
  var inTz = new Date(fakeUtc.toLocaleString('en-US', { timeZone: timezone }));
  var inUtc = new Date(fakeUtc.toLocaleString('en-US', { timeZone: 'UTC' }));
  var offsetMin = (inTz.getTime() - inUtc.getTime()) / 60000;
  var sign = offsetMin >= 0 ? '+' : '-';
  var abs = Math.abs(offsetMin);
  var h = String(Math.floor(abs / 60)).padStart(2, '0');
  var m = String(abs % 60).padStart(2, '0');
  return naiveDatetime + sign + h + ':' + m;
};

// Convert a UTC ISO datetime string to local date/time parts using the city timezone
// Returns { date: 'YYYY-MM-DD', time: 'HH:MM' }
window.utcToLocal = function(isoString, timezone) {
  if (!isoString) return { date: '', time: '' };
  if (!timezone) {
    // Fallback: naive substring (no conversion)
    return { date: isoString.substring(0, 10), time: isoString.substring(11, 16) };
  }
  var d = new Date(isoString);
  if (isNaN(d.getTime())) return { date: '', time: '' };
  var parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false
  }).formatToParts(d);
  var vals = {};
  parts.forEach(function(p) { vals[p.type] = p.value; });
  // Intl hour12:false can return "24" for midnight in some engines; normalize
  var hour = vals.hour === '24' ? '00' : vals.hour;
  return { date: vals.year + '-' + vals.month + '-' + vals.day, time: hour + ':' + vals.minute };
};

// Resize image then upload to capture-event edge function via fetch
// Returns Promise<{ event }> or Promise<{ error }>
window.resizeAndUpload = function(file, supabaseUrl, publishableKey) {
  return window.resizeImageFile(file).then(function(resized) {
    var fd = new FormData();
    fd.append('mode', 'extract');
    // Pass city timezone so Claude uses it as the default for extracted events
    var cityTz = window._cities && window.cityFilter && window._cities[window.cityFilter];
    if (cityTz && cityTz.timezone) {
      fd.append('timezone', cityTz.timezone);
    }
    fd.append('file', resized, resized.name);
    return fetch(supabaseUrl + '/functions/v1/capture-event', {
      method: 'POST',
      headers: { 'apikey': publishableKey },
      body: fd
    });
  }).then(function(resp) {
    if (!resp.ok) {
      return resp.text().then(function(t) { return { error: 'Server error ' + resp.status + ': ' + t }; });
    }
    return resp.json();
  }).catch(function(err) {
    return { error: 'Upload failed: ' + err.message };
  });
};

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

// Pre-compute a lowercase search string per event (call once after events load)
function buildSearchIndex(events) {
  if (!events) return events || [];
  for (var i = 0; i < events.length; i++) {
    var e = events[i];
    if (!e._search) {
      e._search = ((e.title || '') + ' ' + (e.location || '') + ' ' + (e.source || '') + ' ' + (e.description || '')).toLowerCase();
    }
  }
  return events;
}

// Filter events by search term with progressive narrowing
var _prevTerm = '';
var _prevCategory = '';
var _prevFiltered = null;

function filterEvents(events, term, category) {
  if (!events) return events || [];
  var t0 = performance.now();
  var base = category ? events.filter(function(e) { return e.category === category; }) : events;
  if (!term) { _prevTerm = ''; _prevCategory = ''; _prevFiltered = null; return base; }
  var lower = term.toLowerCase();
  // Progressive narrowing: reuse previous result if extending the same search within same category
  var narrowing = (_prevTerm && lower.startsWith(_prevTerm) && category === _prevCategory && _prevFiltered);
  var source = narrowing ? _prevFiltered : base;
  var result = source.filter(function(e) { return e._search && e._search.includes(lower); });
  var t1 = performance.now();
  if (!window._filterLog) window._filterLog = [];
  window._filterLog.push('filterEvents: ' + (t1 - t0).toFixed(1) + 'ms, source=' + source.length + (narrowing ? ' (narrowed)' : ' (full)') + ', results=' + result.length + ', term="' + term + '"');
  _prevTerm = lower;
  _prevCategory = category || '';
  _prevFiltered = result;
  return result;
}

// Return a fixed-size page from a start index.
// Uses one-item overlap so prior page's last item is first on next page.
function getPagedEvents(events, term, startIndex, pageSize, category) {
  const filtered = filterEvents(events, term, category) || [];
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
  // Collapse newlines and extra whitespace into single spaces
  description = description.replace(/[\r\n]+/g, ' ').replace(/ {2,}/g, ' ');
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

// Get the IANA timezone for the current city (e.g. "America/New_York")
function getCityTimezone() {
  var city = window.cityFilter;
  if (city && window._cities && window._cities[city]) {
    return window._cities[city].timezone;
  }
  return undefined; // fall back to browser default
}

// Format day of week
function formatDayOfWeek(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { weekday: 'short', timeZone: getCityTimezone() });
}

// Format month and day
function formatMonthDay(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: getCityTimezone() });
}

// Format date for display
function formatDate(isoString) {
  if (!isoString) return '';
  var tz = getCityTimezone();
  return new Date(isoString).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', timeZone: tz });
}

// Format time for display
function formatTime(isoString) {
  if (!isoString) return '';
  var tz = getCityTimezone();
  var d = new Date(isoString);
  var hours = parseInt(d.toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: tz }));
  var mins = parseInt(d.toLocaleString('en-US', { minute: 'numeric', timeZone: tz }));
  // Skip midnight times (likely means time unknown)
  if (hours === 0 && mins === 0) return '';
  // Format as 12-hour time
  var h = hours % 12 || 12;
  var ampm = hours < 12 ? 'AM' : 'PM';
  var m = mins.toString().padStart(2, '0');
  return h + ':' + m + ' ' + ampm;
}

// Extract a short readable snippet from an event description (for always-visible preview)
// Junk line patterns are hardcoded here; see docs/admin-interface.md for plan to make configurable
function formatSourceLinks(source, sourceUrls, hiddenSources) {
  if (!source) return '';
  var sources = source.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
  // Filter out hidden sources, but keep all if all would be removed
  if (hiddenSources && hiddenSources.length) {
    var visible = sources.filter(function(s) { return hiddenSources.indexOf(s) < 0; });
    if (visible.length > 0) sources = visible;
  }
  var parts = sources.map(function(name) {
    var url = sourceUrls && sourceUrls[name];
    return url ? '[' + name + '](' + url + ')' : name;
  });
  return 'Source: ' + parts.join(', ');
}

function getSnippet(description, title) {
  if (!description) return null;

  var text = String(description);

  // Preserve line breaks from HTML before stripping tags
  if (/<[a-z][\s\S]*>/i.test(text)) {
    text = text.replace(/<\s*br\s*\/?>/gi, '\n');
    text = text.replace(/<\s*\/p\s*>/gi, '\n');
    text = text.replace(/<\s*li\s*>/gi, '\n');
    text = text.replace(/<\s*\/li\s*>/gi, '\n');
    // Replace all other closing tags with a space to prevent word smashing
    text = text.replace(/<\/[^>]+>/g, ' ');
    var doc = new DOMParser().parseFromString(text, 'text/html');
    text = doc.body.textContent || '';
  }

  // Strip URLs, markdown artifacts
  text = text.replace(/https?:\/\/\S+/g, '');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/\\([*_\[\](){}+#>|`~])/g, '$1');

  // Fix smashed words from bad HTML cleanup (e.g. "ZwiftJoin" → "Zwift Join")
  text = text.replace(/([a-z])([A-Z])/g, '$1 $2');

  // Normalize whitespace
  text = text.replace(/[\t\r]+/g, ' ').replace(/ {2,}/g, ' ');

  var lines = text.split('\n').map(function(l) { return l.trim(); }).filter(Boolean);

  // General patterns
  var labelPrefix = /^\w+(\s+\w+){0,2}\s*:\s*/;
  var ctaPrefix = /^(back to|buy|register|sign up|rsvp|tickets?|click|tap|view|see all|read more|get|call or text|call or email)\b/i;
  var badAnywhere = /\b(zoom|meeting id|passcode|one tap|meeting url|webex|microsoft teams|google meet|agenda|packet|minutes|prohibited|not permitted|are not allowed|from almost anywhere in the world|from anywhere in the world)\b/i;
  var moneyOrPrice = /(\$\s*\d|\bprice\b|\bfee\b|\badmission\b|\bfree but\b)/i;

  // Normalize title for comparison
  var normTitle = title ? title.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() : null;
  function normText(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim(); }

  // Salvage text after a label prefix if the remainder is a real sentence
  function salvageLabel(line) {
    if (!labelPrefix.test(line)) return line;
    var rest = line.replace(labelPrefix, '').trim();
    // Remainder must be substantial and sentence-like (has function words)
    if (rest.length < 30) return '';
    if (!/\b(the|a|an|and|or|for|with|to|from|at|in|on|by|is|are|was|will|this|that)\b/i.test(rest)) return '';
    // If remainder itself starts with a label, reject
    if (labelPrefix.test(rest)) return '';
    return rest;
  }

  function scoreLine(line) {
    if (line.length < 15) return -999;

    // Salvage from label prefix
    line = salvageLabel(line);
    if (!line) return -999;

    // Hard rejects
    if (ctaPrefix.test(line)) return -999;
    if (badAnywhere.test(line)) return -999;

    var score = 0;

    // Sentence-like signals (articles, prepositions, common verbs)
    if (/[.!?]/.test(line)) score += 3;
    if (/\b(the|a|an|and|or|but|for|with|to|from|at|in|on|by)\b/i.test(line)) score += 2;
    if (/\b(join|learn|discover|explore|enjoy|experience|celebrate|meet|hear|watch|featuring|presents)\b/i.test(line)) score += 2;

    // Penalize admin/pricing/digit-heavy/boilerplate
    if (moneyOrPrice.test(line)) score -= 3;
    var digitCount = (line.match(/\d/g) || []).length;
    if (digitCount >= 6) score -= 3;
    // Penalize very short lines that aren't sentences
    if (line.length < 25 && !/[.!?]/.test(line)) score -= 3;
    // Penalize lines that are just an institution/venue name (no verb or article)
    if (!/\b(the|a|an|is|are|was|will|has|have|can|do|and|but|for|with|from)\b/i.test(line) && line.length < 40) score -= 3;

    // Penalize title repetition
    if (normTitle) {
      var nt = normText(line);
      if (nt === normTitle) score -= 6;
      else if (nt.indexOf(normTitle) >= 0 && nt.length - normTitle.length < 15) score -= 4;
    }

    // Prefer real length
    if (line.length >= 40) score += 1;
    if (line.length > 220) score -= 2;

    return score;
  }

  // Score all candidates, including sentence splits within long lines
  var best = null;
  var bestScore = -999;
  for (var i = 0; i < lines.length; i++) {
    var parts = lines[i].split(/(?<=[.!?])\s+/);
    for (var j = 0; j < parts.length; j++) {
      var part = parts[j].trim();
      if (!part) continue;
      var s = scoreLine(part);
      if (s > bestScore) {
        bestScore = s;
        best = part;
      }
    }
  }

  if (!best || bestScore < 0) return null;

  // Truncate to ~100 chars at a word boundary
  if (best.length <= 100) return best;
  var cut = best.lastIndexOf(' ', 100);
  if (cut < 40) cut = 100;
  var snippet = best.substring(0, cut).replace(/[\s(,\-;:]+$/, '');
  return snippet + '...';
}

// Truncate text with ellipsis
function truncate(text, maxLen) {
  if (!text) return '';
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trim() + '...';
}

// Toggle a source's visibility and persist to Supabase. Returns updated userSettingsData.
function toggleSourceAndSave(source, userSettingsData, supabaseUrl, supabaseKey) {
  var current = (userSettingsData && userSettingsData[0] && userSettingsData[0].hidden_sources) || [];
  var idx = current.indexOf(source);
  var updated = idx >= 0
    ? current.filter(function(s) { return s !== source; })
    : current.concat([source]);

  // Persist to Supabase (fire-and-forget)
  fetch(supabaseUrl + '/rest/v1/user_settings?on_conflict=user_id,city', {
    method: 'POST',
    headers: {
      apikey: supabaseKey,
      Authorization: 'Bearer ' + window.authSession.access_token,
      'Content-Type': 'application/json',
      'Prefer': 'resolution=merge-duplicates'
    },
    body: JSON.stringify({
      user_id: window.authUser.id,
      city: window.cityFilter,
      hidden_sources: updated,
      updated_at: new Date().toISOString()
    })
  });

  // Return optimistic update
  if (userSettingsData && userSettingsData[0]) {
    return [Object.assign({}, userSettingsData[0], { hidden_sources: updated })];
  }
  return [{ hidden_sources: updated }];
}

// Toggle one-click-pick and persist to Supabase. Returns updated userSettingsData.
function toggleOneClickPickAndSave(userSettingsData, supabaseUrl, supabaseKey) {
  var current = (userSettingsData && userSettingsData[0] && userSettingsData[0].one_click_pick) || false;
  var updated = !current;

  fetch(supabaseUrl + '/rest/v1/user_settings?on_conflict=user_id,city', {
    method: 'POST',
    headers: {
      apikey: supabaseKey,
      Authorization: 'Bearer ' + window.authSession.access_token,
      'Content-Type': 'application/json',
      'Prefer': 'resolution=merge-duplicates'
    },
    body: JSON.stringify({
      user_id: window.authUser.id,
      city: window.cityFilter,
      one_click_pick: updated,
      updated_at: new Date().toISOString()
    })
  });

  if (userSettingsData && userSettingsData[0]) {
    return [Object.assign({}, userSettingsData[0], { one_click_pick: updated })];
  }
  return [{ one_click_pick: updated }];
}

// Check if a source is in the hidden sources list
function isSourceHidden(source, hiddenSources) {
  if (!hiddenSources || !hiddenSources.length) return false;
  return hiddenSources.indexOf(source) >= 0;
}

// Filter out events where ALL sources are hidden
function filterHiddenSources(events, hiddenSources) {
  if (!hiddenSources || !hiddenSources.length) return events;
  if (!events) return [];
  return events.filter(function(e) {
    if (!e.source) return true;
    var sources = e.source.split(',').map(function(s) { return s.trim(); }).filter(Boolean);
    return !sources.every(function(s) { return hiddenSources.indexOf(s) >= 0; });
  });
}

// Aggregate events by source, return sorted array of {source, count}
function getSourceCounts(events) {
  if (!events || !events.length) return [];
  const counts = {};
  events.forEach(e => {
    const sources = (e.source || 'Unknown').split(', ');
    sources.forEach(src => {
      counts[src] = (counts[src] || 0) + 1;
    });
  });
  return Object.entries(counts)
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count);
}

// Deduplicate events: merge events with same title + start_time, combine sources
// Cache variables (module-level for browser, will be on window)
let _dedupedEventsCache = null;
let _dedupedEventsLastInput = null;

function dedupeEvents(events) {
  if (!events || !events.length) return [];

  // Use cache if events array reference hasn't changed
  // (refetch returns a new array, so reference check busts cache correctly)
  if (events === _dedupedEventsLastInput && _dedupedEventsCache) {
    return _dedupedEventsCache;
  }
  _dedupedEventsLastInput = events;

  const groups = {};
  events.forEach(e => {
    // Normalize start_time to ISO string for consistent dedup across formats
    // e.g. '2026-02-11T18:00:00+00:00' and '2026-02-11T18:00:00.000Z' are the same instant
    const normalizedTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    const key = (e.title || '').trim().toLowerCase() + '|' + normalizedTime;
    if (!groups[key]) {
      groups[key] = { ...e, sources: new Set((e.source || '').split(',').map(s => s.trim()).filter(Boolean)), mergedIds: [e.id] };
    } else {
      // Track all merged event IDs (for picks to work across sources)
      groups[key].mergedIds.push(e.id);
      // Add individual sources (split comma-separated values before deduping)
      (e.source || '').split(',').map(s => s.trim()).filter(Boolean).forEach(s => groups[key].sources.add(s));
      // Prefer non-empty values for other fields
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      if (!groups[key].description && e.description) groups[key].description = e.description;
      if (!groups[key].rrule && e.rrule) groups[key].rrule = e.rrule;
      if (!groups[key].cluster_id && e.cluster_id) groups[key].cluster_id = e.cluster_id;
    }
  });
  // Convert sources Set to comma-separated string, with authoritative source first.
  // Known aggregators sort to the end; among non-aggregators, a source whose name
  // appears in the event location is promoted to the front.
  // Filter mergedIds to only include numeric IDs (exclude synthetic enrichment IDs)
  var AGGREGATORS = new Set([
    'North Bay Bohemian', 'Press Democrat', 'Creative Sonoma', 'GoLocal Cooperative',
    'NOW Toronto', 'Toronto Events (Tockify)', 'Montclair Local News',
    'LancasterPA.com', "Let's Go! Bloomington", 'BloomingtonOnline Events',
    'BloomingtonOnline Food & Drink', 'BloomingtonOnline Shopping',
    'Show Up Toronto'
  ]);
  let result = Object.values(groups).map(e => {
    const sourcesArr = Array.from(e.sources).sort((a, b) => {
      var aAgg = AGGREGATORS.has(a) ? 1 : 0;
      var bAgg = AGGREGATORS.has(b) ? 1 : 0;
      if (aAgg !== bAgg) return aAgg - bAgg;
      return a.localeCompare(b);
    });
    const loc = (e.location || '').toLowerCase();
    if (loc) {
      // Among non-aggregators, promote a source whose name appears in the location
      const authIdx = sourcesArr.findIndex(s => !AGGREGATORS.has(s) && loc.includes(s.toLowerCase()));
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
  }).sort((a, b) => {
    const timeCmp = (a.start_time || '').localeCompare(b.start_time || '');
    if (timeCmp !== 0) return timeCmp;
    // Within same timeslot, group clustered events together by cluster_id, then title
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

  // Collapse long-running events (exhibitions, recurring services)
  result = collapseLongRunningEvents(result);

  // Cache the result
  _dedupedEventsCache = result;
  return result;
}

// For long-running events (exhibitions, recurring services), show only once per week.
// This reduces clutter while keeping events visible throughout their run.
// Weeks are anchored to "today" so the first occurrence shown is today or later,
// then subsequent occurrences appear ~7 days apart.
function collapseLongRunningEvents(events) {
  const MIN_OCCURRENCES = 5;  // Need at least this many to consider "long-running"
  const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

  // Get start of today (midnight local)
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Helper: get week number relative to today (0 = this week, 1 = next week, etc.)
  function getWeekFromToday(dateStr) {
    const d = new Date(dateStr);
    const eventDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const daysDiff = Math.floor((eventDay - todayStart) / (24 * 60 * 60 * 1000));
    return Math.floor(daysDiff / 7);
  }

  // Get time-of-day string in city timezone
  const tz = getCityTimezone();
  function getTimeOfDay(dateStr) {
    const d = new Date(dateStr);
    const h = String(parseInt(d.toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: tz }))).padStart(2, '0');
    const m = String(parseInt(d.toLocaleString('en-US', { minute: 'numeric', timeZone: tz }))).padStart(2, '0');
    return h + ':' + m;
  }

  // Group by title + location + time-of-day to identify long-running events
  const groups = {};
  events.forEach(e => {
    const timeOfDay = getTimeOfDay(e.start_time);
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
    const timeOfDay = getTimeOfDay(e.start_time);
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
  _dedupedEventsLastInput = null;
}

// Check if an event is picked (supports merged IDs from cross-source duplicates)
function isEventPicked(mergedIds, picks) {
  if (!picks || !Array.isArray(picks)) return false;
  if (!mergedIds) return false;
  // mergedIds can be an array (from dedupe) or a single ID
  const ids = Array.isArray(mergedIds) ? mergedIds : [mergedIds];
  return picks.some(p => ids.some(id => p.event_id == id));
}

// Stamp each event with _picked boolean so List items change when picks change
function stampPicked(events, picks) {
  if (!events) return events;
  return events.map(function(e) {
    var picked = isEventPicked(e.mergedIds || e.id, picks);
    if (e._picked === picked) return e;
    return Object.assign({}, e, { _picked: picked });
  });
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
function buildRRule(frequency, selectedDays, ordinal, monthDay, until) {
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

  if (until) {
    // Parse yyyy-MM-dd or MM/dd/yyyy format and set to end of day UTC
    var parts = until.includes('-') ? until.split('-') : null;
    if (parts && parts.length === 3) {
      options.until = new Date(Date.UTC(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 23, 59, 59));
    }
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
  // Exclude "on Monday February 16" or "on Monday, Jan 5" (specific dates, not recurrence)
  const everyDay = lower.match(/(?:every|on)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?(?![,\s]+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b)/);
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
    // Use city timezone to convert dtstart to local wall-clock time for rrule.js
    // rrule.js works in UTC internally, so we pass local time as if it were UTC
    var tz = getCityTimezone();
    var srcTime = enrichment.start_time || originalStartTime;
    var localParts = tz ? utcToLocal(srcTime, tz) : { date: srcTime.substring(0, 10), time: srcTime.substring(11, 16) };
    var dtstart = new Date(localParts.date + 'T' + (localParts.time || '00:00') + ':00Z');
    var ruleWithStart = new rrule.RRule({
      ...rule.origOptions,
      dtstart: dtstart
    });
    // Compare against "now" in the same local-as-UTC convention
    var nowLocal = tz
      ? new Date(new Date().toLocaleString('en-US', { timeZone: tz }))
      : new Date();
    var nowFake = new Date(Date.UTC(nowLocal.getFullYear(), nowLocal.getMonth(), nowLocal.getDate(), nowLocal.getHours(), nowLocal.getMinutes()));
    var next = ruleWithStart.after(nowFake, true);
    console.log('getNextOccurrence', { eventId: eventId, enrichmentsLen: enrichments.length, rrule: enrichment.rrule, next: next ? next.toISOString() : null, original: originalStartTime });
    return next ? next.toISOString() : originalStartTime;
  } catch (e) {
    console.error('getNextOccurrence error', e);
    return originalStartTime;
  }
}

// Convert events to react-big-calendar format, with optional search filter
// Parse a timestamp string into a Date object.
function parseLocalTime(ts) {
  if (!ts) return new Date();
  return new Date(ts.replace(' ', 'T'));
}

function toBigCalendarEvents(events, term, category) {
  var filtered = filterEvents(events, term, category) || [];
  return filtered.map(function(e) {
    return {
      title: e.title || '',
      start: parseLocalTime(e.start_time),
      end: parseLocalTime(e.end_time || e.start_time),
      allDay: false,
      resource: e
    };
  });
}

// Export for browser (attach to window)
if (typeof window !== 'undefined') {
  window.toggleDay = toggleDay;
  var _filterEvents = filterEvents;
  window.filterEvents = function(events, term, category) {
    return window.xsTraceWith
      ? window.xsTraceWith("filterEvents", function() { return _filterEvents(events, term, category); },
          function(result) { return { term: term || '', category: category || '', resultCount: result.length }; })
      : _filterEvents(events, term, category);
  };
  window.buildSearchIndex = buildSearchIndex;
  window.getPagedEvents = getPagedEvents;
  window.getDescriptionSnippet = getDescriptionSnippet;
  window.formatDayOfWeek = formatDayOfWeek;
  window.formatMonthDay = formatMonthDay;
  window.formatDate = formatDate;
  window.formatTime = formatTime;
  window.getSnippet = getSnippet;
  window.truncate = truncate;
  window.formatSourceLinks = formatSourceLinks;
  window.toggleSourceAndSave = toggleSourceAndSave;
  window.isSourceHidden = isSourceHidden;
  window.filterHiddenSources = filterHiddenSources;
  window.getSourceCounts = getSourceCounts;
  var _dedupeEvents = dedupeEvents;
  window.dedupeEvents = function(events) {
    return window.xsTraceWith
      ? window.xsTraceWith("dedupeEvents", function() { return _dedupeEvents(events); },
          function(result) { return { inputCount: (events || []).length, outputCount: result.length }; })
      : _dedupeEvents(events);
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
  window.toBigCalendarEvents = toBigCalendarEvents;

  // --- Dashboard helpers ---
  window.filterTileEvents = function(events, category, search) {
    if (!events || !Array.isArray(events)) return [];
    var result = events;
    if (category) {
      result = result.filter(function(e) { return e.category === category; });
    }
    if (search) {
      var term = search.toLowerCase();
      result = result.filter(function(e) {
        return (e.title && e.title.toLowerCase().indexOf(term) >= 0) ||
               (e.description && e.description.toLowerCase().indexOf(term) >= 0) ||
               (e.location && e.location.toLowerCase().indexOf(term) >= 0);
      });
    }
    return result;
  };

  window.getCityList = function() {
    return Object.keys(window._cities).sort();
  };

  window.defaultDashboardTile = function(city) {
    var id = 'tile-' + Date.now();
    return { i: id, city: city || window.cityFilter || window.getCityList()[0] || '', category: '', search: '' };
  };

  window.defaultDashboardLayout = function(tileId) {
    return { i: tileId, x: 0, y: 0, w: 6, h: 4 };
  };

  window.saveDashboardConfig = function(tiles, gridLayout, supabaseUrl, supabaseKey) {
    if (!window.authSession) return;
    var config = { tiles: tiles, gridLayout: gridLayout };
    fetch(supabaseUrl + '/rest/v1/user_settings?on_conflict=user_id,city', {
      method: 'POST',
      headers: {
        apikey: supabaseKey,
        Authorization: 'Bearer ' + window.authSession.access_token,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
      },
      body: JSON.stringify({
        user_id: window.authUser.id,
        city: '_dashboard',
        dashboard: config,
        updated_at: new Date().toISOString()
      })
    });
  };
}
