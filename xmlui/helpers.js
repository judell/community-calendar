// Community Calendar Helper Functions
// Pure functions for filtering, formatting, and deduplication

// --- Categories (derived from categories.json, loaded in index.html) ---
var CATEGORY_NAMES = {};
window.categoryColorMap = {};
window._categories.forEach(function (c) {
  CATEGORY_NAMES[c.name] = true;
  window.categoryColorMap[c.name] = { label: c.label, background: c.background };
});
window.categoryList = window._categories.map(function (c) {
  return c.name;
});
window.getActiveCategories = function (events) {
  var counts = {};
  (events || []).forEach(function (e) {
    if (e.category) counts[e.category] = (counts[e.category] || 0) + 1;
  });
  return window.categoryList
    .filter(function (c) {
      return counts[c];
    })
    .map(function (c) {
      return { name: c, label: c + ' (' + counts[c] + ')' };
    });
};

// Aggregator list comes from source_priority.json (loaded by shell.js).
// Pipeline reads the same file in scripts/combine_ics.py.
var AGGREGATOR_SOURCES = new Set(
  (window._sourcePriority && window._sourcePriority.aggregators) || []
);

function normalizeVenueToken(value) {
  return (value || '')
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .replace(/\b(the|a|an)\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function sourceMatchesLocation(source, location) {
  if (!source || !location) return false;
  var normalizedLocation = normalizeVenueToken(location);
  if (!normalizedLocation) return false;
  var candidates = [];
  var raw = (source || '').toLowerCase().trim();
  var normalized = normalizeVenueToken(source);
  if (raw) candidates.push(raw);
  if (normalized && candidates.indexOf(normalized) < 0) candidates.push(normalized);
  return candidates.some(function (candidate) {
    return candidate && normalizedLocation.includes(candidate);
  });
}

// --- URL sync for category filter ---
window.syncCategoryParam = function (category) {
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
window.syncSearchParam = function (search) {
  clearTimeout(_searchSyncTimer);
  _searchSyncTimer = setTimeout(function () {
    var url = new URL(window.location);
    if (search) {
      url.searchParams.set('search', search);
    } else {
      url.searchParams.delete('search');
    }
    window.history.replaceState({}, '', url);
  }, 500);
};

// --- URL sync for date tabs (#105) ---
// One committed absolute window per Commit: a preset key syncs as ?date=,
// All strips only the date keys, and every commit preserves sibling params
// (city, search, category, mode, images, embed, cards). history-replace (not
// push) so Back leaves the calendar instead of stepping through tab history.
// Single replace site: syncDateParams/syncCustomParams both route through
// replaceDateUrlParams, which owns the new-URL -> set/delete -> replaceState
// shape. A value of undefined leaves the key untouched, null deletes it, and
// a string sets it.
window.replaceDateUrlParams = function (params) {
  var url = new URL(window.location);
  params = params || {};
  if (params.date !== undefined) {
    if (params.date) url.searchParams.set('date', params.date);
    else url.searchParams.delete('date');
  }
  if (params.from !== undefined) {
    if (params.from) url.searchParams.set('from', params.from);
    else url.searchParams.delete('from');
  }
  if (params.to !== undefined) {
    if (params.to) url.searchParams.set('to', params.to);
    else url.searchParams.delete('to');
  }
  window.history.replaceState({}, '', url);
};
// Single source of truth for preset keys (prio-80): the engine owns the
// canonical list (window.DATE_PRESETS in date-windows.js); the tab strip is
// exactly that list, derived here so adding a preset means editing the
// engine only. The slice freezes a copy with a literal fallback for load
// orders where the engine is absent.
window.DATE_TAB_PRESETS = (
  window.DATE_PRESETS || ['all', 'today', 'tonight', 'tomorrow', 'weekend', 'next7', 'thismonth']
).slice();
window.syncDateParams = function (sel) {
  var preset = sel && sel.preset;
  if (preset && preset !== 'all' && window.DATE_TAB_PRESETS.indexOf(preset) >= 0) {
    window.replaceDateUrlParams({ date: preset, from: null, to: null });
  } else {
    window.replaceDateUrlParams({ date: null, from: null, to: null });
  }
};

// Single window-resolution opts (prio-70 dedup): dateWindowForPreset and
// dateWindowForCustom share this builder for the city-timezone plus
// prefetch-horizon plumbing, so the getCityTimezone -> getToDate ->
// resolve shape lives in exactly one place.
window.dateWindowOpts = function () {
  var opts = { timeZone: getCityTimezone() || 'UTC' };
  try {
    if (typeof window.getToDate === 'function') opts.horizonEnd = window.getToDate();
  } catch (e) {}
  return opts;
};

// Resolve one #105 day preset to its absolute window ({start, end} ISO
// strings, nulls for All) in the city timezone via the #104 engine.
// #108: the prefetch horizon truncates overrunning windows (This month past
// the horizon) and the truncation flag rides along for the label below.
window.dateWindowForPreset = function (preset) {
  if (!preset || preset === 'all') return { start: null, end: null, truncated: false };
  try {
    if (typeof window.resolveDatePreset !== 'function')
      return { start: null, end: null, truncated: false };
    var windowRange = window.resolveDatePreset(preset, window.dateWindowOpts());
    if (!windowRange || !windowRange.start) return { start: null, end: null, truncated: false };
    return { start: windowRange.start, end: windowRange.end, truncated: !!windowRange.truncated };
  } catch (e) {
    return { start: null, end: null, truncated: false };
  }
};

// --- Empty / truncation states (#108) ---
// Human label for the empty state `No events {label}.`, one per preset.
// Unknown keys fail open to the All label so bad links never strand the
// visitor on a baffling empty.
window.dateWindowLabel = function (preset) {
  var labels = {
    all: 'found',
    today: 'today',
    tonight: 'tonight',
    tomorrow: 'tomorrow',
    weekend: 'this weekend',
    next7: 'in the next 7 days',
    thismonth: 'this month',
    custom: 'in this date range',
  };
  return labels[preset] || 'found';
};

// Horizon-truncation copy for the label below the tabs (prio-70 dedup):
// this is a thin delegate — the engine's truncationLabelForWindow owns the
// `Showing through {horizonDate} — the calendar currently ends there.`
// copy plus the inclusive-last-day math, so the Main.xmlui custom confirm
// and the shell boot seed render byte-identical labels through this seam.
// Falls back to the local render only when the engine is absent.
window.dateTruncationText = function (windowRange) {
  if (!windowRange || !windowRange.truncated || !windowRange.end) return null;
  try {
    if (typeof window.truncationLabelForWindow === 'function') {
      return window.truncationLabelForWindow(windowRange, getCityTimezone() || 'UTC');
    }
  } catch (e) {
    return null;
  }
  try {
    var tz = getCityTimezone() || 'UTC';
    var lastMs = new Date(windowRange.end).getTime() - 1;
    if (!isFinite(lastMs)) return null;
    var day = new Intl.DateTimeFormat('en-CA', {
      timeZone: tz,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date(lastMs));
    return 'Showing through ' + day + ' — the calendar currently ends there.';
  } catch (e) {
    return null;
  }
};

// Move focus to the tab-strip heading after the empty-state reset commits
// Next 7, without scrolling the page. True when the heading took focus;
// false (fail loud, never silent) when neither the heading nor the strip
// itself is focusable (the strip fallback covers engines that drop id on
// text components). XMLUI renders a component `id` as the data-xmlui-id
// attribute, never a DOM id, so this queries that attribute (the browser a11y
// spec proves the real DOM contract).
window.focusDateTabHeading = function () {
  try {
    if (typeof document === 'undefined' || !document.querySelector) return false;
    var el =
      document.querySelector('[data-xmlui-id="dateTabHeading"]') ||
      document.querySelector('[data-xmlui-id="dateTabStrip"]');
    if (!el || typeof el.focus !== 'function') return false;
    if (el.hasAttribute && !el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
    return true;
  } catch (e) {
    return false;
  }
};

// Move focus to the Custom tab. The vendored picker's own Escape handler
// closes the popup but leaves focus on <body> (it does not restore the
// trigger), so the spec's "Escape returns focus to the Custom tab" needs this
// explicit move. Fail loud (false) when the tab is not mounted.
window.returnFocusToCustomTab = function () {
  try {
    if (typeof document === 'undefined' || !document.querySelector) return false;
    var tab = document.querySelector('[data-xmlui-id="customDateTab"]');
    if (!tab || typeof tab.focus !== 'function') return false;
    tab.focus({ preventScroll: true });
    return true;
  } catch (e) {
    return false;
  }
};

// True while the Custom range picker popup is showing. The vendored control
// exposes no open/close API; its root carries data-state="open" only while the
// popup is open, which is the one stable signal available.
function customPickerIsOpen() {
  try {
    if (typeof document === 'undefined' || !document.querySelector) return false;
    return !!document.querySelector('[data-xmlui-id="customRangePicker"][data-state="open"]');
  } catch (e) {
    return false;
  }
}

// Escape in the picker returns focus to the Custom tab. Capture phase so the
// picker's own Escape handler cannot close the popup first and hide the open
// state this keys on; the focus move is deferred a tick so it lands after the
// popup has closed.
if (typeof document !== 'undefined' && document.addEventListener) {
  document.addEventListener(
    'keydown',
    function (e) {
      if (e.key !== 'Escape' && e.key !== 'Esc') return;
      if (!customPickerIsOpen()) return;
      setTimeout(function () {
        window.returnFocusToCustomTab();
      }, 0);
    },
    true
  );
}

// --- Custom range picker (#107) ---
// Today in the city timezone as yyyy-MM-dd (the picker's date-only minimum;
// recomputed on every call so boot plus day-rollover stay correct).
window.todayDateOnly = function () {
  try {
    var tz = getCityTimezone() || 'UTC';
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: tz,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date());
  } catch (e) {
    return new Date().toISOString().substring(0, 10);
  }
};

// City timezone for the picker (the stock control resolves its calendar in
// this zone so day boundaries match the committed window). Kept as a named
// window.* seam rather than inlined at the DatePicker binding because (a)
// getCityTimezone is a bare (non-window) function the markup cannot call,
// and (b) the `|| 'UTC'` fallback policy lives here in one place alongside
// dateWindowOpts/todayDateOnly/dateTruncationText instead of being
// duplicated in the declarative binding.
window.customPickerTimezone = function () {
  return getCityTimezone() || 'UTC';
};

// Past dates disabled at the control level: everything before today.
window.customDisabledDates = function () {
  return [{ before: window.todayDateOnly() }];
};

// Resolve an exact Custom range to its committed window ({start, end} ISO
// plus canonical from/to, truncated, clamped) in the city timezone via the
// #104 engine. Null on malformed or partial input (the commit ignores it,
// so nothing filters mid-drag or per tick). End-before-start coerces to a
// single day, over-long ranges cap at 180 days, past starts clamp to today,
// and ends past the prefetch horizon truncate with the truncation label.
// Takes the window shape {from, to} (prio-90 Data Clumps fix); the legacy
// positional (from, to) pair still works so existing harnesses stay green.
window.dateWindowForCustom = function (rangeOrFrom, to) {
  var from = rangeOrFrom;
  if (
    rangeOrFrom != null &&
    typeof rangeOrFrom === 'object' &&
    !Array.isArray(rangeOrFrom) &&
    ('from' in rangeOrFrom || 'to' in rangeOrFrom)
  ) {
    from = rangeOrFrom.from;
    to = rangeOrFrom.to;
  }
  if (from == null || to == null) return null;
  try {
    if (typeof window.resolveCustomRange !== 'function') return null;
    var windowRange = window.resolveCustomRange(from, to, window.dateWindowOpts());
    if (!windowRange || !windowRange.start) return null;
    return {
      start: windowRange.start,
      end: windowRange.end,
      from: windowRange.from,
      to: windowRange.to,
      truncated: !!windowRange.truncated,
      clamped: !!windowRange.clamped,
    };
  } catch (e) {
    return null;
  }
};

// Sync the canonical Custom link: exact from/to only with no preset key,
// preserving sibling params (city, search, category, mode, images, embed,
// cards). history-replace (not push) so Back leaves the calendar instead of
// stepping through filter states. Takes the committed window {from, to}
// (prio-90); the legacy positional (from, to) pair still works.
window.syncCustomParams = function (rangeOrFrom, to) {
  var from = rangeOrFrom;
  if (
    rangeOrFrom != null &&
    typeof rangeOrFrom === 'object' &&
    !Array.isArray(rangeOrFrom) &&
    ('from' in rangeOrFrom || 'to' in rangeOrFrom)
  ) {
    from = rangeOrFrom.from;
    to = rangeOrFrom.to;
  }
  if (from && to) {
    window.replaceDateUrlParams({ date: null, from: from, to: to });
  } else {
    // No-op commit (callers guard on the resolve, so this path only fires on
    // malformed input): rewrite the untouched URL, exactly as before.
    window.replaceDateUrlParams({});
  }
};

// Open the stock range picker popup with a real click, never focus().
// The vendored control opens only from its Control onClick: the exposed
// handle offers focus/setValue/getValue but no open API, openOnClick is
// false, and the onClick ignores input/button targets — so focus() merely
// selects the date text and the popup stays shut. Clicking the Control
// element itself takes the setOpen(true) path on desktop and mobile alike.
// The Control is found by climbing from its input (inner class names are
// hashed; the [data-mode="range"] root attribute is the stable anchor).
// Returns true when the popup was asked to open, false when the picker is
// not mounted (callers keep customOpen=true; the row mounts on that flag).
window.openCustomPicker = function () {
  try {
    var root =
      document.querySelector('[data-xmlui-id="customPickerRow"] [data-mode="range"]') ||
      document.querySelector('[data-mode="range"]');
    if (!root) return false;
    var input = root.querySelector('input');
    if (!input || !input.parentElement) return false;
    var control = input;
    while (
      control !== root &&
      control.parentElement &&
      control.parentElement.parentElement &&
      control.parentElement.parentElement !== root
    ) {
      control = control.parentElement;
    }
    if (control === root || control === input) {
      input.focus();
      return true;
    }
    control.click();
    return true;
  } catch (e) {
    return false;
  }
};

// True when `iso` is midnight (00:00) in `tz`: the pipeline anchors
// time-unknown events there (see formatTime, which renders them dateless),
// so a midnight start means "time unknown", never "plays at midnight".
function startIsMidnightInTz(iso, tz) {
  try {
    var parts = new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).formatToParts(new Date(iso));
    var v = {};
    parts.forEach(function (p) {
      v[p.type] = p.value;
    });
    var hour = v.hour === '24' ? '00' : v.hour;
    return (hour === '00' || hour === '0') && (v.minute === '00' || v.minute === '0');
  } catch (e) {
    return false;
  }
}

// Filter events to the committed absolute window {start, end} (prio-90 Data
// Clumps fix: the window travels as one object, not loose positional
// bounds). The legacy positional (startISO, endISO) form still works so
// existing call sites and harnesses stay green.
// Null bounds (All) return the input by reference so downstream bindings
// keep a stable identity; unparseable bounds fail open to All rather than
// stranding the visitor on an empty list.
// `opts.startTimeOnly` (Tonight per #103) keeps the [start, end) range over
// the start instant but additionally drops flagged all-day events and
// midnight-anchored (time-unknown) starts, which never play at night;
// multi-day events qualify by start day only with the end time ignored.
// `opts.timeZone` overrides the city timezone (tests pin it explicitly).
function filterByDateWindow(events, windowOrStartISO, endISOOrOpts, maybeOpts) {
  var startISO = windowOrStartISO;
  var endISO = endISOOrOpts;
  var opts = maybeOpts;
  if (
    windowOrStartISO != null &&
    typeof windowOrStartISO === 'object' &&
    !Array.isArray(windowOrStartISO) &&
    ('start' in windowOrStartISO || 'end' in windowOrStartISO)
  ) {
    startISO = windowOrStartISO.start;
    endISO = windowOrStartISO.end;
    opts = endISOOrOpts;
  }
  if (!events) return events;
  if (startISO == null || endISO == null) return events;
  var fromMs = new Date(startISO).getTime();
  var toMs = new Date(endISO).getTime();
  if (!isFinite(fromMs) || !isFinite(toMs) || !(toMs > fromMs)) return events;
  var startTimeOnly = !!(opts && opts.startTimeOnly);
  var tz =
    (opts && opts.timeZone) ||
    (typeof getCityTimezone === 'function' ? getCityTimezone() : undefined) ||
    'UTC';
  return events.filter(function (e) {
    var eventStartMs = new Date(e.start_time).getTime();
    if (!(eventStartMs >= fromMs && eventStartMs < toMs)) return false;
    if (!startTimeOnly) return true;
    if (e.all_day || e.allDay) return false;
    if (startIsMidnightInTz(e.start_time, tz)) return false;
    return true;
  });
}
window.filterByDateWindow = filterByDateWindow;

// --- Cluster Colors ---
// The border colour is derived from the route's opaque duplicate_group id, not
// a positional cluster index: the id is stable across a build, so a grouped
// card keeps the same colour while membership is unchanged. A NULL group is a
// Separate row and gets no border.
const CLUSTER_COLORS = ['#6b9bd2', '#7bc47f', '#d4a04a'];
function duplicateGroupColor(duplicateGroup) {
  var s = String(duplicateGroup);
  var h = 0;
  for (var i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) | 0;
  }
  return CLUSTER_COLORS[Math.abs(h) % CLUSTER_COLORS.length];
}
window.clusterBorder = function (duplicateGroup, filtered) {
  if (duplicateGroup == null || duplicateGroup === '' || filtered) return 'none';
  return '3px solid ' + duplicateGroupColor(duplicateGroup);
};

// --- Image Resize (client-side, before upload) ---
// Converts any image (including HEIC via browser decode) to JPEG under maxBytes
window.resizeImageFile = function (file, maxBytes) {
  maxBytes = maxBytes || 3500000; // ~3.5MB raw → ~4.8MB base64, under Claude's 5MB limit
  return new Promise(function (resolve, reject) {
    var img = new Image();
    var url = URL.createObjectURL(file);
    img.onload = function () {
      URL.revokeObjectURL(url);
      var canvas = document.createElement('canvas');
      var w = img.width,
        h = img.height;
      // Try at full resolution first, then scale down
      var scale = 1.0;
      var attempt = function () {
        canvas.width = Math.round(w * scale);
        canvas.height = Math.round(h * scale);
        var ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          function (blob) {
            if (!blob) {
              reject(new Error('Canvas toBlob failed'));
              return;
            }
            if (blob.size <= maxBytes || scale <= 0.2) {
              resolve(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
            } else {
              scale *= 0.7;
              attempt();
            }
          },
          'image/jpeg',
          0.85
        );
      };
      attempt();
    };
    img.onerror = function () {
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
window.applyTimezoneOffset = function (naiveDatetime, timezone) {
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
window.utcToLocal = function (isoString, timezone) {
  if (!isoString) return { date: '', time: '' };
  if (!timezone) {
    // Fallback: naive substring (no conversion)
    return { date: isoString.substring(0, 10), time: isoString.substring(11, 16) };
  }
  var d = new Date(isoString);
  if (isNaN(d.getTime())) return { date: '', time: '' };
  var parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(d);
  var vals = {};
  parts.forEach(function (p) {
    vals[p.type] = p.value;
  });
  // Intl hour12:false can return "24" for midnight in some engines; normalize
  var hour = vals.hour === '24' ? '00' : vals.hour;
  return { date: vals.year + '-' + vals.month + '-' + vals.day, time: hour + ':' + vals.minute };
};

// Resize image then upload to capture-event edge function via fetch
// Returns Promise<{ event }> or Promise<{ error }>
window.resizeAndUpload = function (file, supabaseUrl, publishableKey) {
  var token = window.authSession && window.authSession.access_token;
  if (!token) {
    return Promise.resolve({ error: 'Please sign in again to capture events' });
  }
  return window
    .resizeImageFile(file)
    .then(function (resized) {
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
        headers: { apikey: publishableKey, Authorization: 'Bearer ' + token },
        body: fd,
      });
    })
    .then(function (resp) {
      if (resp.status === 401) {
        return { error: 'Please sign in again to capture events' };
      }
      if (!resp.ok) {
        return resp.text().then(function (t) {
          return { error: 'Server error ' + resp.status + ': ' + t };
        });
      }
      return resp.json();
    })
    .catch(function (err) {
      return { error: 'Upload failed: ' + err.message };
    });
};

// --- Audio Recording ---
window.audioRecorder = null;
window.audioChunks = [];
window.audioBlob = null;
window.audioMimeType = null;

window.startRecording = async function () {
  try {
    var stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    var mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
    window.audioRecorder = new MediaRecorder(stream, { mimeType: mimeType });
    window.audioChunks = [];
    window.audioBlob = null;
    window.audioMimeType = mimeType;
    window.audioRecorder.ondataavailable = function (e) {
      if (e.data.size > 0) {
        window.audioChunks.push(e.data);
        window.audioBlob = new Blob(window.audioChunks, { type: mimeType });
      }
    };
    window.audioRecorder.start(500);
    return true;
  } catch (e) {
    console.error('Failed to start recording:', e);
    return false;
  }
};

window.stopRecording = function () {
  if (window.audioRecorder && window.audioRecorder.state === 'recording') {
    window.audioRecorder.stop();
    window.audioRecorder.stream.getTracks().forEach(function (t) {
      t.stop();
    });
  }
};

window.getRecordingFile = function () {
  if (!window.audioBlob) return null;
  var ext = window.audioMimeType === 'audio/webm' ? 'webm' : 'm4a';
  return new File([window.audioBlob], 'recording.' + ext, { type: window.audioMimeType });
};

// Pre-compute a lowercase search string per event (call once after events load)
function buildSearchIndex(events) {
  if (!events) return events || [];
  var _t0 = performance.now();
  for (var i = 0; i < events.length; i++) {
    var e = events[i];
    e._search = getEventSearchText(e);
  }
  if (!window._pipelineLog) window._pipelineLog = [];
  window._pipelineLog.push(
    'buildSearchIndex: ' + (performance.now() - _t0).toFixed(1) + 'ms, ' + events.length + ' events'
  );
  return events;
}

function getEventSearchText(event) {
  return (
    (event.title || '') +
    ' ' +
    (event.location || '') +
    ' ' +
    (event.source || '') +
    ' ' +
    (event.description || '')
  ).toLowerCase();
}

// Strong content identity for an events payload. shell.js's issue-82
// emission coalescing uses this to decide whether a fresh fetch is
// identical to the paint it would replace. Unlike ccArraySig — kept O(1)
// because memoizeIngest runs it on every evaluation — this runs only a
// handful of times per load (cache paint, fetch compare/store, refetch),
// so it can afford to examine every row. The previous key (length +
// first/last id) called two payloads identical when only the middle
// changed, which let a stale cached paint suppress the fresh emission
// and, after the epoch nudge landed, leave the repaint unfired. Two
// 32-bit multiplicative hashes with independent seeds (an FNV-1a pass and
// a MurmurHash3-style pass) over the same stream give ~64 bits, so an
// accidental collision between distinct payloads is negligible.
function eventsSignature(rows) {
  if (!Array.isArray(rows)) return 'na';
  if (!rows.length) return '0';
  var h1 = 0x811c9dc5; // FNV-1a offset basis
  var h2 = 0x9747b28c; // independent seed
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    var s = row === undefined ? 'undefined' : JSON.stringify(row);
    if (s === undefined) s = 'undefined';
    for (var j = 0; j < s.length; j++) {
      var c = s.charCodeAt(j);
      h1 = Math.imul(h1 ^ c, 0x01000193); // FNV-1a prime
      h2 = Math.imul(h2 ^ c, 0x85ebca6b); // MurmurHash3 constant
    }
    // Row separator: keeps ["ab"] from hashing the same as ["a", "b"].
    h1 = Math.imul(h1 ^ 0x1f, 0x01000193);
    h2 = Math.imul(h2 ^ 0x1f, 0x85ebca6b);
  }
  return rows.length + ':' + (h1 >>> 0).toString(16) + ':' + (h2 >>> 0).toString(16);
}
window.eventsSignature = eventsSignature;

// The issue-82 fresh-emission skip decision, extracted from shell.js so
// test.html can pin the coalescing itself, not just the signature: a fresh
// payload is skipped only when it is identical to the last emission and
// came from the same subscriber and city. Callers pass the precomputed
// eventsSignature so the payload is hashed once per delivery — the same
// signature is then stored for the next comparison. With the old weak key,
// a mid-payload change looked identical and suppressed the fresh emit — and
// therefore the epoch bump that repaints the stale cache.
function shouldSkipFreshEmit(state, freshSig) {
  return !!(
    state.currentEmit &&
    state.currentEmit === state.lastEmitFn &&
    state.city === state.lastEmitCity &&
    freshSig === state.lastEmitSig
  );
}
window.shouldSkipFreshEmit = shouldSkipFreshEmit;

// Filter events by search term with progressive narrowing
var _prevTerm = '';
var _prevCategory = '';
var _prevFiltered = null;

var _prevEventsLen = 0;
var _prevEventsFirst = null;
function filterEvents(events, term, category) {
  if (!events) return events || [];
  var t0 = performance.now();
  var base = category
    ? events.filter(function (e) {
        return e.category === category;
      })
    : events;
  if (!term) {
    _prevTerm = '';
    _prevCategory = '';
    _prevFiltered = null;
    _prevEventsLen = 0;
    _prevEventsFirst = null;
    return base;
  }
  var lower = term.toLowerCase();
  // Progressive narrowing: reuse previous result if extending the same search within same category AND same input
  var sameInput = events.length === _prevEventsLen && events[0] === _prevEventsFirst;
  var narrowing =
    sameInput &&
    _prevTerm &&
    lower.startsWith(_prevTerm) &&
    category === _prevCategory &&
    _prevFiltered;
  var source = narrowing ? _prevFiltered : base;
  _prevEventsLen = events.length;
  _prevEventsFirst = events[0];
  var result = source.filter(function (e) {
    // Use the cache buildSearchIndex populated (after sortSourcesForDisplay's
    // source-merge); fall back to computing only for a straggler that lacks it.
    // Do NOT reintroduce a compute-once guard in buildSearchIndex — its
    // unconditional recompute is what keeps source-name search working (49094c78e).
    var searchText = e._search || getEventSearchText(e);
    return searchText.includes(lower);
  });
  var t1 = performance.now();
  if (!window._filterLog) window._filterLog = [];
  window._filterLog.push(
    'filterEvents: ' +
      (t1 - t0).toFixed(1) +
      'ms, source=' +
      source.length +
      (narrowing ? ' (narrowed)' : ' (full)') +
      ', results=' +
      result.length +
      ', term="' +
      term +
      '"'
  );
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
  const hasMore = index + size < filtered.length;
  const nextIndex = hasMore ? index + step : null;
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

// Pager guards (#146). The Earlier/Later controls must read the SAME list the
// rendered list reads — the date window (filtered upstream) plus search and
// category — or the un-categorized list claims a next page the filtered slice
// does not have (#146: 245 events in the window, 4 in the selected category,
// yet "Later" paged that category into an empty list). Pure functions with
// explicit arguments, because XMLUI reactivity tracks the arguments, not
// mutations of globals (d86627969). The term branch matches getPagedEvents'
// search first-N behavior, where the controls are hidden by markup anyway.
function moreHasMore(events, term, startIndex, pageSize, category) {
  if (term) return false;
  const filtered = filterEvents(events, term, category) || [];
  const size = pageSize || 50;
  const index = Number.isFinite(startIndex) ? Math.max(0, startIndex) : 0;
  return index + size < filtered.length;
}

function moreHasPrev(events, term, startIndex, category) {
  if (term) return false;
  const filtered = filterEvents(events, term, category) || [];
  const index = Number.isFinite(startIndex) ? Math.max(0, startIndex) : 0;
  // "Earlier" is available whenever a nonempty filtered list sits behind a
  // positive index. It deliberately does NOT require the page start to be
  // inside the filtered list: a filtered-input shrink that repaints without
  // resetting paging — a smaller fresh PushSource payload, or a hidden-source
  // toggle — can leave the index past the end, and hiding "Earlier" there
  // would strand the user on an empty page with no controls. Category and date
  // changes reset paging, so the reported case never reaches that state.
  return index > 0 && filtered.length > 0;
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

// Next scheduled build time in the city's local timezone
// Build runs daily at midnight UTC (cron: 0 0 * * *)
window.nextBuildLocalTime = function () {
  var now = new Date();
  var next = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1, 0, 0, 0)
  );
  if (now.getUTCHours() === 0 && now.getUTCMinutes() < 10) {
    next = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 0, 0, 0));
  }
  var tz = getCityTimezone();
  return next.toLocaleString('en-US', {
    timeZone: tz,
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  });
};

// Format day of week
function formatDayOfWeek(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', {
    weekday: 'short',
    timeZone: getCityTimezone(),
  });
}

// Format month and day
function formatMonthDay(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: getCityTimezone(),
  });
}

// Format date for display
function formatDate(isoString) {
  if (!isoString) return '';
  var tz = getCityTimezone();
  return new Date(isoString).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone: tz,
  });
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

function uniqueSourceNames(source) {
  if (!source) return [];
  var seen = new Set();
  return source
    .split(',')
    .map(function (s) {
      return s.trim();
    })
    .filter(function (s) {
      if (!s || seen.has(s)) return false;
      seen.add(s);
      return true;
    });
}

// Structured source names from the view, falling back to the legacy split.
// The view's `source_names` is authoritative: a human source name may contain
// a comma, so splitting the compatibility `source` string would fabricate
// names (spec amendment L402). Every client site that derives names uses this.
function eventSourceNames(e) {
  if (e && Array.isArray(e.source_names) && e.source_names.length) {
    var seen = new Set();
    return e.source_names
      .map(function (s) {
        return String(s).trim();
      })
      .filter(function (s) {
        if (!s || seen.has(s)) return false;
        seen.add(s);
        return true;
      });
  }
  return uniqueSourceNames((e && e.source) || '');
}

// Extract a short readable snippet from an event description (for always-visible preview)
// Junk line patterns are hardcoded here; see docs/admin-interface.md for plan to make configurable
function formatSourceLinks(source, sourceUrls, hiddenSources, sourceNames) {
  var sources = eventSourceNames({ source: source, source_names: sourceNames });
  if (!sources.length) return '';
  // Filter out hidden sources, but keep all if all would be removed
  if (hiddenSources && hiddenSources.length) {
    var visible = sources.filter(function (s) {
      return hiddenSources.indexOf(s) < 0;
    });
    if (visible.length > 0) sources = visible;
  }
  var parts = sources.map(function (name) {
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
  text = text.replace(/\\([*_[\](){}+#>|`~])/g, '$1');

  // Fix smashed words from bad HTML cleanup (e.g. "ZwiftJoin" → "Zwift Join")
  text = text.replace(/([a-z])([A-Z])/g, '$1 $2');

  // Normalize whitespace
  text = text.replace(/[\t\r]+/g, ' ').replace(/ {2,}/g, ' ');

  var lines = text
    .split('\n')
    .map(function (l) {
      return l.trim();
    })
    .filter(Boolean);

  // General patterns
  var labelPrefix = /^\w+(\s+\w+){0,2}\s*:\s*/;
  var ctaPrefix =
    /^(back to|buy|register|sign up|rsvp|tickets?|click|tap|view|see all|read more|get|call or text|call or email)\b/i;
  var badAnywhere =
    /\b(zoom|meeting id|passcode|one tap|meeting url|webex|microsoft teams|google meet|agenda|packet|minutes|prohibited|not permitted|are not allowed|from almost anywhere in the world|from anywhere in the world)\b/i;
  var moneyOrPrice = /(\$\s*\d|\bprice\b|\bfee\b|\badmission\b|\bfree but\b)/i;

  // Normalize title for comparison
  var normTitle = title
    ? title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim()
    : null;
  function normText(s) {
    return s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  // Salvage text after a label prefix if the remainder is a real sentence
  function salvageLabel(line) {
    if (!labelPrefix.test(line)) return line;
    var rest = line.replace(labelPrefix, '').trim();
    // Remainder must be substantial and sentence-like (has function words)
    if (rest.length < 30) return '';
    if (!/\b(the|a|an|and|or|for|with|to|from|at|in|on|by|is|are|was|will|this|that)\b/i.test(rest))
      return '';
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
    if (
      /\b(join|learn|discover|explore|enjoy|experience|celebrate|meet|hear|watch|featuring|presents)\b/i.test(
        line
      )
    )
      score += 2;

    // Penalize admin/pricing/digit-heavy/boilerplate
    if (moneyOrPrice.test(line)) score -= 3;
    var digitCount = (line.match(/\d/g) || []).length;
    if (digitCount >= 6) score -= 3;
    // Penalize very short lines that aren't sentences
    if (line.length < 25 && !/[.!?]/.test(line)) score -= 3;
    // Penalize lines that are just an institution/venue name (no verb or article)
    if (
      !/\b(the|a|an|is|are|was|will|has|have|can|do|and|but|for|with|from)\b/i.test(line) &&
      line.length < 40
    )
      score -= 3;

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

// Save user setting fields to Supabase (fire-and-forget). Returns updated userSettingsData.
function saveUserSetting(fields, userSettingsData, supabaseUrl, supabaseKey) {
  fetch(supabaseUrl + '/rest/v1/user_settings?on_conflict=user_id,city', {
    method: 'POST',
    headers: {
      apikey: supabaseKey,
      Authorization: 'Bearer ' + window.authSession.access_token,
      'Content-Type': 'application/json',
      Prefer: 'resolution=merge-duplicates',
    },
    body: JSON.stringify(
      Object.assign(
        {
          user_id: window.authUser.id,
          city: window.cityFilter,
          updated_at: new Date().toISOString(),
        },
        fields
      )
    ),
  });

  if (userSettingsData && userSettingsData[0]) {
    return [Object.assign({}, userSettingsData[0], fields)];
  }
  return [fields];
}

// Toggle a source's visibility and persist. Returns updated userSettingsData.
function toggleSourceAndSave(source, userSettingsData, supabaseUrl, supabaseKey) {
  var current =
    (userSettingsData && userSettingsData[0] && userSettingsData[0].hidden_sources) || [];
  var idx = current.indexOf(source);
  var updated =
    idx >= 0
      ? current.filter(function (s) {
          return s !== source;
        })
      : current.concat([source]);
  return saveUserSetting({ hidden_sources: updated }, userSettingsData, supabaseUrl, supabaseKey);
}

// Apply a complete hidden_sources array and persist. Returns updated userSettingsData.
function saveHiddenSources(hiddenArray, userSettingsData, supabaseUrl, supabaseKey) {
  return saveUserSetting(
    { hidden_sources: hiddenArray },
    userSettingsData,
    supabaseUrl,
    supabaseKey
  );
}

// Check if a source is in the hidden sources list
function isSourceHidden(source, hiddenSources) {
  if (!hiddenSources || !hiddenSources.length) return false;
  return hiddenSources.indexOf(source) >= 0;
}

// Filter out events where ALL sources are hidden, or where ANY hidden source
// is an aggregator (unchecking an aggregator hides everything it covers)
function filterHiddenSources(events, hiddenSources) {
  if (!hiddenSources || !hiddenSources.length) return events;
  if (!events) return [];
  return events.filter(function (e) {
    var sources = eventSourceNames(e);
    if (!sources.length) return true;
    if (
      sources.some(function (s) {
        return hiddenSources.indexOf(s) >= 0 && AGGREGATOR_SOURCES.has(s);
      })
    )
      return false;
    return !sources.every(function (s) {
      return hiddenSources.indexOf(s) >= 0;
    });
  });
}

// Aggregate events by source, return sorted array of {source, count}
function getSourceCounts(events) {
  if (!events || !events.length) return [];
  const counts = {};
  events.forEach((e) => {
    var sources = eventSourceNames(e);
    if (!sources.length) sources = ['Unknown'];
    sources.forEach((src) => {
      counts[src] = (counts[src] || 0) + 1;
    });
  });
  return Object.entries(counts)
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count);
}

// True when the source name is a known aggregator (from source_priority.json)
function isAggregatorSource(name) {
  return AGGREGATOR_SOURCES.has(name);
}

// Per-source counts over the currently visible events, with a row for every
// source in the full list so hidden rows persist (count 0 when fully hidden)
function getVisibleSourceCounts(events, hiddenSources) {
  var all = getSourceCounts(events);
  if (!hiddenSources || !hiddenSources.length) {
    return all.map(function (item) {
      return { source: item.source, count: item.count, total: item.count, hiddenViaAggregator: 0 };
    });
  }
  var counts = {};
  var aggHidden = {};
  (events || []).forEach(function (e) {
    var sources = eventSourceNames(e);
    if (!sources.length) sources = ['Unknown'];
    var viaAgg = sources.some(function (s) {
      return hiddenSources.indexOf(s) >= 0 && AGGREGATOR_SOURCES.has(s);
    });
    if (viaAgg) {
      sources.forEach(function (src) {
        aggHidden[src] = (aggHidden[src] || 0) + 1;
      });
      return;
    }
    if (
      sources.length &&
      sources.every(function (s) {
        return hiddenSources.indexOf(s) >= 0;
      })
    )
      return;
    sources.forEach(function (src) {
      counts[src] = (counts[src] || 0) + 1;
    });
  });
  return all.map(function (item) {
    return {
      source: item.source,
      count: counts[item.source] || 0,
      total: item.count,
      hiddenViaAggregator: aggHidden[item.source] || 0,
    };
  });
}

// Tooltip for a source-count row: explains why visible < total
function sourceCountTooltip(row, hiddenSources) {
  if (!row) return '';
  var hidden = hiddenSources || [];
  if (hidden.indexOf(row.name) >= 0 && AGGREGATOR_SOURCES.has(row.name)) {
    return 'Hidden aggregator: all ' + row.total_count + ' events it carries are hidden';
  }
  if (!row.agg_hidden) return '';
  return (
    row.agg_hidden +
    ' of ' +
    row.total_count +
    ' events also arrive via a hidden aggregator (*) and are hidden with it'
  );
}

// Deduplicate route rows by stored duplicate_group. Attach each enrichment's
// original occurrence through its event_id; titles never provide a fallback key.
// Cache variables (module-level for browser, will be on window)
let _dedupedEventsCache = null;
let _dedupedEventsLastLen = 0;
let _dedupedEventsLastFirst = null;
let _dedupedEventsLastLast = null;

function dedupeEvents(events) {
  if (!events || !events.length) return [];

  // Use cache if the data is unchanged.
  // The combined array is always a new reference (spread), so check
  // length + first/last element identity as a fast proxy.
  if (
    _dedupedEventsCache &&
    events.length === _dedupedEventsLastLen &&
    events[0] === _dedupedEventsLastFirst &&
    events[events.length - 1] === _dedupedEventsLastLast
  ) {
    return _dedupedEventsCache;
  }
  _dedupedEventsLastLen = events.length;
  _dedupedEventsLastFirst = events[0];
  _dedupedEventsLastLast = events[events.length - 1];

  // Recurring enrichment occurrences have synthetic ids. Link only the
  // original RRULE occurrence to its stored event; future occurrences remain
  // separate virtual rows. The event_id comes from the enrichment foreign key.
  const routeGroupByMember = new Map();
  events.forEach((e) => {
    if (e._enrichment_event_id != null) return;
    const normalizedTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    const routeGroup =
      e.duplicate_group != null && e.duplicate_group !== ''
        ? 'g:' + e.duplicate_group
        : 'r:' + e.id;
    const memberIds = Array.isArray(e.merged_ids) && e.merged_ids.length ? e.merged_ids : [e.id];
    memberIds.forEach((id) => {
      routeGroupByMember.set(String(id), { group: routeGroup, startTime: normalizedTime });
    });
  });

  const groups = {};
  events.forEach((e) => {
    // Normalize start_time to ISO string for consistent dedup across formats
    // e.g. '2026-02-11T18:00:00+00:00' and '2026-02-11T18:00:00.000Z' are the same instant
    const virtualTime = e.start_time ? new Date(e.start_time).toISOString() : '';
    // The route's stored decision is authoritative for calendar rows. The
    // original recurrence uses its linked row's stored time; other NULL-group
    // rows keep their own row key and virtual occurrence time.
    const linkedRoute =
      e._enrichment_event_id != null && e._enrichment_is_original_occurrence
        ? routeGroupByMember.get(String(e._enrichment_event_id))
        : null;
    const normalizedTime = linkedRoute ? linkedRoute.startTime : virtualTime;
    const group =
      (linkedRoute && linkedRoute.group) ||
      (e.duplicate_group != null && e.duplicate_group !== ''
        ? 'g:' + e.duplicate_group
        : 'r:' + e.id);
    const key = group + '|' + normalizedTime;
    // Seed membership from the view's merged_ids so a pick on the card lights
    // up every member; fall back to the row id for raw rows.
    const seedIds =
      Array.isArray(e.merged_ids) && e.merged_ids.length ? e.merged_ids.slice() : [e.id];
    // The view's `source_names` is structured and already ordered by the route's
    // representative rule. Only a raw row without it falls back to splitting the
    // legacy comma-joined `source` string (spec amendment L402).
    const names = eventSourceNames(e);
    const structured = Array.isArray(e.source_names) && e.source_names.length ? names : null;
    if (!groups[key]) {
      groups[key] = {
        ...e,
        sourceNames: names.slice(),
        structuredSources: structured != null,
        source_urls: Object.assign({}, e.source_urls || {}),
        mergedIds: seedIds,
      };
    } else {
      // Track all merged event IDs (for picks to work across sources)
      seedIds.forEach((id) => {
        if (groups[key].mergedIds.indexOf(id) < 0) groups[key].mergedIds.push(id);
      });
      // Union member source names, representative row's order first
      names.forEach((s) => {
        if (groups[key].sourceNames.indexOf(s) < 0) groups[key].sourceNames.push(s);
      });
      groups[key].structuredSources = groups[key].structuredSources || structured != null;
      // Union per-source links so every member source stays reachable
      Object.assign(groups[key].source_urls, e.source_urls || {});
      // Prefer non-empty values for other fields
      if (!groups[key].url && e.url) groups[key].url = e.url;
      if (!groups[key].location && e.location) groups[key].location = e.location;
      if (!groups[key].description && e.description) groups[key].description = e.description;
      if (!groups[key].rrule && e.rrule) groups[key].rrule = e.rrule;
    }
  });
  // Render the ordered names as the compatibility comma string. When the names
  // are structured the view's order is authoritative; only the raw-row fallback
  // applies the legacy aggregator/location ordering. Filter mergedIds to only
  // include numeric IDs (exclude synthetic enrichment IDs).
  let result = Object.values(groups)
    .map((e) => {
      let sourcesArr;
      if (e.structuredSources) {
        sourcesArr = e.sourceNames.slice();
      } else {
        sourcesArr = e.sourceNames.slice().sort((a, b) => {
          var aAgg = AGGREGATOR_SOURCES.has(a) ? 1 : 0;
          var bAgg = AGGREGATOR_SOURCES.has(b) ? 1 : 0;
          if (aAgg !== bAgg) return aAgg - bAgg;
          return a.localeCompare(b);
        });
        if (e.location) {
          // Among non-aggregators, promote a source whose name appears in the location
          const authIdx = sourcesArr.findIndex(
            (s) => !AGGREGATOR_SOURCES.has(s) && sourceMatchesLocation(s, e.location)
          );
          if (authIdx > 0) {
            const [auth] = sourcesArr.splice(authIdx, 1);
            sourcesArr.unshift(auth);
          }
        }
      }
      const out = {
        ...e,
        source: sourcesArr.join(', '),
        source_names: sourcesArr,
        mergedIds: e.mergedIds.filter((id) => typeof id === 'number' || /^\d+$/.test(id)),
      };
      delete out.sourceNames;
      delete out.structuredSources;
      delete out._enrichment_event_id;
      delete out._enrichment_is_original_occurrence;
      return out;
    })
    .sort((a, b) => {
      const timeCmp = (a.start_time || '').localeCompare(b.start_time || '');
      if (timeCmp !== 0) return timeCmp;
      // Within the same instant, keep a group's row ahead of Separate rows and
      // order deterministically by group id then title.
      const ga = a.duplicate_group || '';
      const gb = b.duplicate_group || '';
      if (ga && gb) {
        if (ga !== gb) return ga.localeCompare(gb);
        return (a.title || '').localeCompare(b.title || '');
      }
      if (ga) return -1;
      if (gb) return 1;
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
var _collapseCache = null;
var _collapseLastLen = 0;
var _collapseLastFirstId = null;
var _collapseLastLastId = null;
var _collapseLastEmitSig = null;
var _collapseRun = 0;

function collapseLongRunningEvents(events) {
  if (!events || !events.length) return [];
  var _t0 = performance.now();
  _collapseRun++;
  // Content-based cache key (event ids), not object identity: the PushSource
  // network emit has different object *references* than the cached emit but the
  // same content, so an identity check always missed on the 2nd pipeline run
  // and recomputed (~300ms spike). See issue #77.
  //
  // The id triple alone is too weak (#86): a payload differing only in the
  // middle matches it, and this returns _collapseCache BY REFERENCE, so the
  // fresh rows are swallowed here even after the outer memoizeIngest key is
  // fixed — the outer memo misses, calls through, and gets the stale array
  // back. The emission signature shell.js publishes closes that: it changes
  // iff the emitted content changed, and stays constant within one emission,
  // so the repeated pipeline runs this cache exists for still hit.
  var firstId = events[0] && events[0].id;
  var lastId = events[events.length - 1] && events[events.length - 1].id;
  var emitSig = window.__ccEmitSig || '';
  if (
    _collapseCache &&
    events.length === _collapseLastLen &&
    firstId === _collapseLastFirstId &&
    lastId === _collapseLastLastId &&
    emitSig === _collapseLastEmitSig
  ) {
    if (!window._pipelineLog) window._pipelineLog = [];
    window._pipelineLog.push(
      'collapseLong run#' +
        _collapseRun +
        ': ' +
        (performance.now() - _t0).toFixed(1) +
        'ms (cache HIT), ' +
        events.length +
        ' events'
    );
    return _collapseCache;
  }
  _collapseLastLen = events.length;
  _collapseLastFirstId = firstId;
  _collapseLastLastId = lastId;
  _collapseLastEmitSig = emitSig;

  const MIN_OCCURRENCES = 5; // Need at least this many to consider "long-running"

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

  // Get time-of-day string in city timezone (cached to avoid expensive toLocaleString calls)
  const tz = getCityTimezone();
  var _todCache = {};
  function getTimeOfDay(dateStr) {
    if (_todCache[dateStr]) return _todCache[dateStr];
    const d = new Date(dateStr);
    const h = String(
      parseInt(d.toLocaleString('en-US', { hour: 'numeric', hour12: false, timeZone: tz }))
    ).padStart(2, '0');
    const m = String(
      parseInt(d.toLocaleString('en-US', { minute: 'numeric', timeZone: tz }))
    ).padStart(2, '0');
    var result = h + ':' + m;
    _todCache[dateStr] = result;
    return result;
  }

  // Group by title + location + time-of-day to identify long-running events
  const groups = {};
  events.forEach((e) => {
    const timeOfDay = getTimeOfDay(e.start_time);
    const key =
      (e.title || '').trim().toLowerCase() +
      '|' +
      (e.location || '').trim().toLowerCase() +
      '|' +
      timeOfDay;
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

  events.forEach((e) => {
    const timeOfDay = getTimeOfDay(e.start_time);
    const key =
      (e.title || '').trim().toLowerCase() +
      '|' +
      (e.location || '').trim().toLowerCase() +
      '|' +
      timeOfDay;

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

  _collapseCache = result.sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
  if (!window._pipelineLog) window._pipelineLog = [];
  window._pipelineLog.push(
    'collapseLong run#' +
      _collapseRun +
      ': ' +
      (performance.now() - _t0).toFixed(1) +
      'ms (cache MISS, computed), ' +
      events.length +
      ' events'
  );
  return _collapseCache;
}

function sortSourcesForDisplay(events) {
  if (!events) return [];
  return events.map(function (e) {
    // A structured row already carries the view's representative ordering;
    // re-sorting the compatibility string would undo it (spec amendment L402).
    if (e && Array.isArray(e.source_names) && e.source_names.length) return e;
    if (!e.source) return e;
    var sourcesArr = uniqueSourceNames(e.source);
    if (sourcesArr.length <= 1) return e;
    sourcesArr.sort(function (a, b) {
      var aAgg = AGGREGATOR_SOURCES.has(a) ? 1 : 0;
      var bAgg = AGGREGATOR_SOURCES.has(b) ? 1 : 0;
      if (aAgg !== bAgg) return aAgg - bAgg;
      return a.localeCompare(b);
    });
    if (e.location) {
      var authIdx = sourcesArr.findIndex(function (s) {
        return !AGGREGATOR_SOURCES.has(s) && sourceMatchesLocation(s, e.location);
      });
      if (authIdx > 0) {
        var auth = sourcesArr.splice(authIdx, 1)[0];
        sourcesArr.unshift(auth);
      }
    }
    return Object.assign({}, e, { source: sourcesArr.join(', ') });
  });
}

// Clear dedupe cache (useful for testing)
// Also resets the collapse stage: dedupeEvents feeds its grouped output into
// collapseLongRunningEvents, whose content-blind key (len + first/last id)
// would otherwise return the previous test's object for a same-shaped but
// different-content input.
function clearDedupeCache() {
  _dedupedEventsCache = null;
  _dedupedEventsLastLen = 0;
  _dedupedEventsLastFirst = null;
  _dedupedEventsLastLast = null;
  _collapseCache = null;
  _collapseLastLen = 0;
  _collapseLastFirstId = null;
  _collapseLastLastId = null;
  _collapseLastEmitSig = null;
  // Also reset the issue-82 memo layer on collapseLongRunningEvents: in the
  // browser the global identifier is rebound to the memoized wrapper, so the
  // inner call inside dedupeEvents hits that cache (keyed len + endpoint
  // ids) rather than _collapseCache directly. Without this, same-shaped but
  // different-content inputs falsely hit across clearDedupeCache() calls.
  if (
    typeof window !== 'undefined' &&
    window.__ccMemoClear &&
    window.__ccMemoClear.collapseLongRunningEvents
  ) {
    window.__ccMemoClear.collapseLongRunningEvents();
  }
}

// Check if an event is picked (supports merged IDs from cross-source duplicates)
function isEventPicked(mergedIds, picks) {
  if (!picks || !Array.isArray(picks)) return false;
  if (!mergedIds) return false;
  // mergedIds can be an array (from dedupe) or a single ID
  const ids = Array.isArray(mergedIds) ? mergedIds : [mergedIds];
  return picks.some((p) => ids.some((id) => p.event_id == id));
}

// The complete membership of the card an event belongs to. Prefers the
// client-computed camelCase `mergedIds`; otherwise reads the view's `merged_ids`
// column; otherwise the event is its own single-member group. Picks and
// unpicks route through here so one card covers every stored member.
function eventMergedIds(event) {
  if (!event) return [];
  if (Array.isArray(event.mergedIds) && event.mergedIds.length) return event.mergedIds;
  if (Array.isArray(event.merged_ids) && event.merged_ids.length) return event.merged_ids;
  return event.id != null ? [event.id] : [];
}

// My Picks shows one row per stored Group, not one per picked member. Rows
// without a group (NULL) stay separate. When several members of one group are
// picked, the route's canonical representative wins so the displayed fields
// match the card; otherwise the smallest member event id wins for determinism.
// When the representative is not among the picked events (a pick stored before
// the route, or a representative that changed between builds), that fallback
// runs — the same ordering as the my-picks ICS feed (ADR 0013), so the list and
// the feed cannot pick different members.
// Cached by input identity so the List binding returns a stable reference
// between renders (picks are replaced wholesale on refetch).
var _dedupePicksLast = null;
var _dedupePicksResult = null;
function dedupePicks(picks) {
  if (!Array.isArray(picks)) return [];
  if (picks === _dedupePicksLast) return _dedupePicksResult;
  var best = {};
  var order = [];
  picks.forEach(function (p) {
    var ev = (p && p.events) || {};
    var key =
      ev.duplicate_group != null && ev.duplicate_group !== ''
        ? 'g:' + ev.duplicate_group
        : 'r:' + (ev.id != null ? ev.id : 'p:' + (p && p.id));
    var candidate = {
      isRep:
        ev.duplicate_group_representative != null &&
        ev.source_uid === ev.duplicate_group_representative
          ? 0
          : 1,
      eventId: ev.id != null ? Number(ev.id) : 0,
    };
    if (!best[key]) {
      best[key] = { pick: p, rank: candidate };
      order.push(key);
      return;
    }
    var cur = best[key].rank;
    if (
      candidate.isRep !== cur.isRep ? candidate.isRep < cur.isRep : candidate.eventId < cur.eventId
    ) {
      best[key] = { pick: p, rank: candidate };
    }
  });
  _dedupePicksLast = picks;
  _dedupePicksResult = order.map(function (key) {
    return best[key].pick;
  });
  return _dedupePicksResult;
}

// Build Google Calendar URL for an event
function buildGoogleCalendarUrl(event) {
  if (!event) return '';

  // Format date for Google Calendar (YYYYMMDDTHHMMSSZ format)
  // Must parse as Date first to handle timezone offset properly
  function formatGoogleDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d
      .toISOString()
      .replace(/[-:]/g, '')
      .replace(/\.\d{3}/, '');
  }

  const startDate = formatGoogleDate(event.start_time);
  const endDate = event.end_time ? formatGoogleDate(event.end_time) : startDate;

  var params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title || '',
    dates: startDate + '/' + endDate,
    location: event.location || '',
    details: event.description || '',
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
  return d
    .toISOString()
    .replace(/[-:]/g, '')
    .replace(/\.\d{3}/, '');
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
    `DTSTART:${formatICSDate(event.start_time)}`,
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
    SU: rrule.RRule.SU,
    MO: rrule.RRule.MO,
    TU: rrule.RRule.TU,
    WE: rrule.RRule.WE,
    TH: rrule.RRule.TH,
    FR: rrule.RRule.FR,
    SA: rrule.RRule.SA,
  };

  const options = {
    freq: frequency === 'WEEKLY' ? rrule.RRule.WEEKLY : rrule.RRule.MONTHLY,
  };

  if (frequency === 'WEEKLY' && selectedDays && selectedDays.length > 0) {
    options.byweekday = selectedDays.map((d) => dayMap[d]).filter(Boolean);
  }

  if (frequency === 'MONTHLY' && monthDay && ordinal) {
    options.byweekday = [dayMap[monthDay].nth(ordinal)];
  }

  if (until) {
    // Parse yyyy-MM-dd or MM/dd/yyyy format and set to end of day UTC
    var parts = until.includes('-') ? until.split('-') : null;
    if (parts && parts.length === 3) {
      options.until = new Date(
        Date.UTC(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 23, 59, 59)
      );
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
      [rrule.RRule.YEARLY]: 'YEARLY',
    };

    const dayCodeMap = {
      0: 'MO',
      1: 'TU',
      2: 'WE',
      3: 'TH',
      4: 'FR',
      5: 'SA',
      6: 'SU',
    };

    const frequency = freqMap[rule.options.freq] || 'none';
    const days = (rule.options.byweekday || [])
      .map((d) => {
        // byweekday can be Weekday objects or numbers
        const dayNum = typeof d === 'number' ? d : d.weekday;
        return dayCodeMap[dayNum];
      })
      .filter(Boolean);

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
    apikey: window.SUPABASE_KEY,
    Authorization: 'Bearer ' + window.authSession.access_token,
    'Content-Type': 'application/json',
    Prefer: 'resolution=merge-duplicates,return=representation',
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
    updated_at: new Date().toISOString(),
  };

  const url = `${window.SUPABASE_URL}/rest/v1/event_enrichments`;
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
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
    apikey: window.SUPABASE_KEY,
    Authorization: 'Bearer ' + window.authSession.access_token,
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
    apikey: window.SUPABASE_KEY,
    Authorization: 'Bearer ' + window.authSession.access_token,
  };

  const url = `${window.SUPABASE_URL}/rest/v1/event_enrichments?curator_id=eq.${window.authUser.id}`;
  const res = await fetch(url, { headers });

  if (res.ok) {
    const data = await res.json();
    // Populate cache
    data.forEach((e) => {
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
  return days.includes(day) ? days.filter((d) => d !== day) : [...days, day];
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
        var dayMap = {
          sunday: 'SU',
          monday: 'MO',
          tuesday: 'TU',
          wednesday: 'WE',
          thursday: 'TH',
          friday: 'FR',
          saturday: 'SA',
        };
        for (var j = 0; j < allArgs.length; j++) {
          if (allArgs[j]) {
            var dayMatch = allArgs[j]
              .toLowerCase()
              .match(/\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?\b/);
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
  const everyDay = lower.match(
    /(?:every|on)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?(?![,\s]+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b)/
  );
  if (everyDay) {
    const dayMap = {
      sunday: 'SU',
      monday: 'MO',
      tuesday: 'TU',
      wednesday: 'WE',
      thursday: 'TH',
      friday: 'FR',
      saturday: 'SA',
    };
    return { frequency: 'WEEKLY', days: [dayMap[everyDay[1]]] };
  }
  // Match "weekly", "every week" — also look for a day name in the same text
  if (/\bevery\s+week\b|\bweekly\b/.test(lower)) {
    const dayMap = {
      sunday: 'SU',
      monday: 'MO',
      tuesday: 'TU',
      wednesday: 'WE',
      thursday: 'TH',
      friday: 'FR',
      saturday: 'SA',
    };
    const dayInText = lower.match(
      /\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?\b/
    );
    return { frequency: 'WEEKLY', days: dayInText ? [dayMap[dayInText[1]]] : [] };
  }
  // Match "1st Tuesday", "2nd and 4th Friday", etc. — extract ordinal + day
  const ordinalMatch = lower.match(
    /(\d+)(?:st|nd|rd|th)\s+(?:and\s+\d+(?:st|nd|rd|th)\s+)?(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/
  );
  if (ordinalMatch) {
    const dayMap = {
      sunday: 'SU',
      monday: 'MO',
      tuesday: 'TU',
      wednesday: 'WE',
      thursday: 'TH',
      friday: 'FR',
      saturday: 'SA',
    };
    return {
      frequency: 'MONTHLY',
      days: [],
      ordinal: parseInt(ordinalMatch[1]),
      monthDay: dayMap[ordinalMatch[2]],
    };
  }
  // Match word-form ordinals: "first Wednesday", "second Tuesday", "third Friday", "fourth Monday"
  const wordOrdinalMap = { first: 1, second: 2, third: 3, fourth: 4 };
  const wordOrdinalMatch = lower.match(
    /(first|second|third|fourth)\s+(sunday|monday|tuesday|wednesday|thursday|friday|saturday)/
  );
  if (wordOrdinalMatch) {
    const dayMap = {
      sunday: 'SU',
      monday: 'MO',
      tuesday: 'TU',
      wednesday: 'WE',
      thursday: 'TH',
      friday: 'FR',
      saturday: 'SA',
    };
    return {
      frequency: 'MONTHLY',
      days: [],
      ordinal: wordOrdinalMap[wordOrdinalMatch[1]],
      monthDay: dayMap[wordOrdinalMatch[2]],
    };
  }
  // Match "biweekly", "monthly"
  if (/\bmonthly\b/.test(lower)) return { frequency: 'MONTHLY', days: [] };
  return null;
}

// Expand enrichments with RRULEs into virtual events within a date range
function expandEnrichments(enrichments, fromDateStr, toDateStr) {
  if (!enrichments || !enrichments.length) return [];

  // Use city timezone to handle UTC→local conversion (same trick as getNextOccurrence)
  const tz = getCityTimezone();

  // Convert from/to range to local-as-UTC for rrule.js comparison
  function toLocalFakeUTC(dateStr) {
    if (tz) {
      const d = new Date(dateStr);
      const local = new Date(d.toLocaleString('en-US', { timeZone: tz }));
      return new Date(
        Date.UTC(
          local.getFullYear(),
          local.getMonth(),
          local.getDate(),
          local.getHours(),
          local.getMinutes()
        )
      );
    }
    return new Date(dateStr);
  }

  const fromDate = toLocalFakeUTC(fromDateStr);
  const toDate = toLocalFakeUTC(toDateStr);
  const virtualEvents = [];

  enrichments.forEach((enrichment) => {
    if (!enrichment.rrule || !enrichment.start_time || !enrichment.title) return;

    try {
      // Convert stored UTC time to local wall-clock, then treat as UTC for rrule.js
      // This ensures day-of-week is correct in the city's timezone
      const localParts = tz
        ? window.utcToLocal(enrichment.start_time, tz)
        : {
            date: enrichment.start_time.substring(0, 10),
            time: enrichment.start_time.substring(11, 16),
          };
      const dtstart = new Date(localParts.date + 'T' + (localParts.time || '00:00') + ':00Z');

      // Build the full RRULE string with dtstart
      const ruleStr = enrichment.rrule.startsWith('RRULE:')
        ? enrichment.rrule
        : 'RRULE:' + enrichment.rrule;
      const rule = rrule.RRule.fromString(ruleStr);

      // Create new rule with dtstart set
      const ruleWithStart = new rrule.RRule({
        ...rule.origOptions,
        dtstart: dtstart,
      });

      // Get occurrences within the date range
      const occurrences = ruleWithStart.between(fromDate, toDate, true);

      occurrences.forEach((date) => {
        // Convert local-as-UTC back to a display-friendly ISO string
        // The date from rrule.js is in fake-UTC (actually local time), use as-is for display
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
          _enrichment_event_id: enrichment.event_id,
          _enrichment_is_original_occurrence: date.getTime() === dtstart.getTime(),
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

  var enrichment = enrichments.find(function (e) {
    return e.event_id == eventId;
  });
  if (!enrichment || !enrichment.rrule) return originalStartTime;

  try {
    var ruleStr = enrichment.rrule.startsWith('RRULE:')
      ? enrichment.rrule
      : 'RRULE:' + enrichment.rrule;
    var rule = rrule.RRule.fromString(ruleStr);
    // Use city timezone to convert dtstart to local wall-clock time for rrule.js
    // rrule.js works in UTC internally, so we pass local time as if it were UTC
    var tz = getCityTimezone();
    var srcTime = enrichment.start_time || originalStartTime;
    var localParts = tz
      ? window.utcToLocal(srcTime, tz)
      : { date: srcTime.substring(0, 10), time: srcTime.substring(11, 16) };
    var dtstart = new Date(localParts.date + 'T' + (localParts.time || '00:00') + ':00Z');
    var ruleWithStart = new rrule.RRule({
      ...rule.origOptions,
      dtstart: dtstart,
    });
    // Compare against "now" in the same local-as-UTC convention
    var nowLocal = tz ? new Date(new Date().toLocaleString('en-US', { timeZone: tz })) : new Date();
    var nowFake = new Date(
      Date.UTC(
        nowLocal.getFullYear(),
        nowLocal.getMonth(),
        nowLocal.getDate(),
        nowLocal.getHours(),
        nowLocal.getMinutes()
      )
    );
    var next = ruleWithStart.after(nowFake, true);
    console.log('getNextOccurrence', {
      eventId: eventId,
      enrichmentsLen: enrichments.length,
      rrule: enrichment.rrule,
      next: next ? next.toISOString() : null,
      original: originalStartTime,
    });
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

function normalizeTimeValue(value) {
  if (!value) return '';
  var s = String(value).trim();
  var m = s.match(/^(\d{1,2}):(\d{2})/);
  if (!m) return s.substring(0, 5);
  return m[1].padStart(2, '0') + ':' + m[2];
}

function extractIsoDateValue(value) {
  if (!value) return '';
  var s = String(value).trim();
  var m = s.match(/^(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : '';
}

function extractHmTimeValue(value, fallback) {
  if (!value) return fallback || '';
  var s = String(value).trim();
  var m = s.match(/[T ](\d{1,2}:\d{2})(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?$/);
  if (m) return normalizeTimeValue(m[1]);
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return fallback || '';
  return normalizeTimeValue(s);
}

function validateIsoDateInput(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(String(value || '').trim()) ? null : 'Use YYYY-MM-DD';
}

function validateHmTimeInput(value) {
  return /^\d{1,2}:\d{2}$/.test(String(value || '').trim()) ? null : 'Use HH:MM';
}

function toBigCalendarEvents(events, term, category) {
  var filtered = filterEvents(events, term, category) || [];
  return filtered.map(function (e) {
    return {
      title: e.title || '',
      start: parseLocalTime(e.start_time),
      end: parseLocalTime(e.end_time || e.start_time),
      allDay: false,
      resource: e,
    };
  });
}

// Export for browser (attach to window)
if (typeof window !== 'undefined') {
  window.toggleDay = toggleDay;
  var _filterEvents = filterEvents;
  window.filterEvents = function (events, term, category) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'filterEvents',
          function () {
            return _filterEvents(events, term, category);
          },
          function (result) {
            return { term: term || '', category: category || '', resultCount: result.length };
          }
        )
      : _filterEvents(events, term, category);
  };
  var _buildSearchIndex = buildSearchIndex;
  window.buildSearchIndex = function (events) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'buildSearchIndex',
          function () {
            return _buildSearchIndex(events);
          },
          function (result) {
            return { count: result.length };
          }
        )
      : _buildSearchIndex(events);
  };
  window.getPagedEvents = getPagedEvents;
  window.moreHasMore = moreHasMore;
  window.moreHasPrev = moreHasPrev;
  window.getDescriptionSnippet = getDescriptionSnippet;
  window.formatDayOfWeek = formatDayOfWeek;
  window.formatMonthDay = formatMonthDay;
  window.formatDate = formatDate;
  window.formatTime = formatTime;
  window.normalizeTimeValue = normalizeTimeValue;
  window.extractIsoDateValue = extractIsoDateValue;
  window.extractHmTimeValue = extractHmTimeValue;
  window.validateIsoDateInput = validateIsoDateInput;
  window.validateHmTimeInput = validateHmTimeInput;
  window.getSnippet = getSnippet;
  window.truncate = truncate;
  window.formatSourceLinks = formatSourceLinks;
  window.saveUserSetting = saveUserSetting;
  window.toggleSourceAndSave = toggleSourceAndSave;
  window.saveHiddenSources = saveHiddenSources;
  window.isSourceHidden = isSourceHidden;
  var _filterHiddenSources = filterHiddenSources;
  window.filterHiddenSources = function (events, hidden) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'filterHiddenSources',
          function () {
            return _filterHiddenSources(events, hidden);
          },
          function (result) {
            return { inputCount: (events || []).length, outputCount: result.length };
          }
        )
      : _filterHiddenSources(events, hidden);
  };

  // Seed hidden sources from localStorage for unauthenticated users
  try {
    var stored = localStorage.getItem('hidden_sources');
    if (stored) {
      window._localHiddenSources = JSON.parse(stored);
    }
  } catch (e) {}

  var _filterExternalExclusions = function (events) {
    var exc = window.externalExclusions;
    if (!exc) return events;
    if (!events) return [];
    var exSources = exc.excludedSources || [];
    var exCategories = exc.excludedCategories || [];
    var rejSet = {};
    (exc.excludedEvents || []).forEach(function (uid) {
      rejSet[uid] = true;
    });
    var requireApproval = exc.requireApproval && exc.lastReviewed;
    var lastReviewed = exc.lastReviewed || null;
    return events.filter(function (e) {
      // Structured source_names first (spec amendment L402): splitting the
      // legacy comma-joined `source` would fabricate names for a human source
      // such as "Taste, Inc." and fail to exclude it.
      var parts = eventSourceNames(e);
      for (var i = 0; i < parts.length; i++) {
        if (exSources.indexOf(parts[i]) >= 0) return false;
      }
      if (e.category && exCategories.indexOf(e.category) >= 0) return false;
      if (e.source_uid && rejSet[e.source_uid]) return false;
      if (requireApproval && (e.created_at || e.start_time) > lastReviewed) return false;
      return true;
    });
  };
  window.filterExternalExclusions = function (events) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'filterExternalExclusions',
          function () {
            return _filterExternalExclusions(events);
          },
          function (result) {
            return { inputCount: (events || []).length, outputCount: result.length };
          }
        )
      : _filterExternalExclusions(events);
  };
  window.getSourceCounts = getSourceCounts;
  window.isAggregatorSource = isAggregatorSource;
  window.getVisibleSourceCounts = getVisibleSourceCounts;
  window.sourceCountTooltip = sourceCountTooltip;
  var _dedupeEvents = dedupeEvents;
  window.dedupeEvents = function (events) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'dedupeEvents',
          function () {
            return _dedupeEvents(events);
          },
          function (result) {
            return { inputCount: (events || []).length, outputCount: result.length };
          }
        )
      : _dedupeEvents(events);
  };
  var _collapseLongRunning = collapseLongRunningEvents;
  window.collapseLongRunningEvents = function (events) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'collapseLongRunningEvents',
          function () {
            return _collapseLongRunning(events);
          },
          function (result) {
            return { inputCount: (events || []).length, outputCount: result.length };
          }
        )
      : _collapseLongRunning(events);
  };
  var _sortSourcesForDisplay = sortSourcesForDisplay;
  window.sortSourcesForDisplay = function (events) {
    return window.xsTraceWith
      ? window.xsTraceWith(
          'sortSourcesForDisplay',
          function () {
            return _sortSourcesForDisplay(events);
          },
          function (result) {
            return { count: result.length };
          }
        )
      : _sortSourcesForDisplay(events);
  };
  // issue-82 ingest instrumentation (observe-only). Wraps the transform
  // chain exports with performance marks and running totals so a boot's
  // recompute count and per-stage cost are readable without console.log
  // (disabled in index.html): the cc:* measures land on the Timings
  // track of a DevTools Performance recording, and window.__ccIngestStats
  // holds {calls, totalMs, rows} per function for console inspection.
  window.__ccIngestStats = {};
  function instrumentIngest(name) {
    var orig = window[name];
    if (!orig) return;
    window[name] = function () {
      var t0 = performance.now();
      try {
        performance.mark('cc:' + name + ':start');
      } catch (e) {}
      var result = orig.apply(this, arguments);
      var ms = performance.now() - t0;
      try {
        performance.measure('cc:' + name, 'cc:' + name + ':start');
      } catch (e) {}
      var s =
        window.__ccIngestStats[name] ||
        (window.__ccIngestStats[name] = { calls: 0, totalMs: 0, rows: 0 });
      s.calls += 1;
      s.totalMs += ms;
      if (result && result.length !== undefined) s.rows = result.length;
      return result;
    };
  }
  // issue-82 memoization: the instrumented boot showed the chain running
  // 10x with reference-identical input. A single-entry cache per function
  // returns the previous result BY REFERENCE on a hit, so downstream
  // XMLUI consumers see unchanged data and skip re-rendering; one entry
  // (not a WeakMap history) avoids retaining superseded 4.6 MB arrays.
  // Applied before instrumentIngest so the stats wrappers stay outermost:
  // calls keeps counting invocations, hits show up as ~0 ms.
  // Keyed on a content signature (length + first/last ids), not the input
  // reference: the __ccRefStats probe showed boundary refs are mostly
  // stable, yet ref-keyed memos still missed at engine-mediated stage
  // boundaries — the engine gives intermediate expression results fresh
  // identities per evaluation. Signatures sidestep identity entirely.
  // ccArraySig alone is blind to a mid-array content change with identical
  // length and endpoint ids (#86), so the key also carries the emission
  // signature shell.js publishes. That is constant between emissions, so the
  // within-emission reuse this memo exists for still hits; it changes on a new
  // emission, so a genuinely different payload is never served the stale array.
  window.__ccMemoStats = {};
  window.__ccMemoClear = {};
  function memoizeIngest(name, extraKey) {
    var orig = window[name];
    if (!orig) return;
    var lastKey = null,
      lastResult = null;
    var stats = (window.__ccMemoStats[name] = { hits: 0, misses: 0 });
    window.__ccMemoClear[name] = function () {
      lastKey = null;
      lastResult = null;
    };
    window[name] = function () {
      var key = [ccArraySig(arguments[0]), window.__ccEmitSig || ''];
      if (extraKey) key = key.concat(extraKey.apply(null, arguments));
      if (
        lastKey !== null &&
        key.length === lastKey.length &&
        key.every(function (k, i) {
          return k === lastKey[i];
        })
      ) {
        stats.hits += 1;
        return lastResult;
      }
      stats.misses += 1;
      var result = orig.apply(this, arguments);
      lastKey = key;
      lastResult = result;
      return result;
    };
  }
  memoizeIngest('filterExternalExclusions', function () {
    return [window.externalExclusions];
  });
  memoizeIngest('sortSourcesForDisplay');
  memoizeIngest('collapseLongRunningEvents');
  // hiddenSources may be a fresh small array each evaluation, so key on
  // its content, not its reference.
  memoizeIngest('filterHiddenSources', function (events, hidden) {
    return [JSON.stringify(hidden || null)];
  });
  memoizeIngest('buildSearchIndex');
  // getPagedEvents is not memoized: it is cheap and its scalar arguments
  // (page index, filter term) legitimately change.

  // Head of the chain: Main.xmlui's combinedEvents was an inline spread,
  // building a NEW array on every binding evaluation and defeating every
  // memo downstream (verified: 8 full-price collapseLongRunningEvents
  // runs after memoization landed). This memoized combiner returns a
  // stable reference while both inputs are reference-unchanged.
  // Reference keying fails at the engine boundary: the readouts showed 8
  // full-price chain runs even after ref memoization, i.e. the engine
  // presents a different events.value/enrichments.value identity per
  // binding evaluation. So the boundary memo keys on a cheap content
  // signature instead (the ccArraySig length + first/last id test) plus the
  // emission signature shell.js publishes (#86), and __ccRefStats counts the
  // identity churn as evidence for the upstream XMLUI finding.
  function ccArraySig(a, includeEnrichmentLinkage) {
    if (!Array.isArray(a)) return 'na';
    if (!a.length) return '0';
    var signature = a.length + ':' + a[0].id + ':' + a[a.length - 1].id;
    if (includeEnrichmentLinkage) {
      signature +=
        ':' +
        a
          .map(function (e) {
            return [
              e._enrichment_id,
              e._enrichment_event_id,
              e._enrichment_is_original_occurrence,
            ].join('|');
          })
          .join(',');
    }
    return signature;
  }
  window.__ccRefStats = { combineCalls: 0, eventsRefChanges: 0, enrichRefChanges: 0 };
  var _combineLastARef = null,
    _combineLastBRef = null;
  var _combineLastASig = null,
    _combineLastBSig = null,
    _combineLastEmitSig = null,
    _combineResult = null;
  window.combineEvents = function (events, enrichments) {
    var s = window.__ccRefStats;
    s.combineCalls += 1;
    if (events !== _combineLastARef) {
      s.eventsRefChanges += 1;
      _combineLastARef = events;
    }
    if (enrichments !== _combineLastBRef) {
      s.enrichRefChanges += 1;
      _combineLastBRef = enrichments;
    }
    var aSig = ccArraySig(events),
      bSig = ccArraySig(enrichments, true),
      emitSig = window.__ccEmitSig || '';
    if (
      aSig === _combineLastASig &&
      bSig === _combineLastBSig &&
      emitSig === _combineLastEmitSig &&
      _combineResult !== null
    ) {
      return _combineResult;
    }
    _combineLastASig = aSig;
    _combineLastBSig = bSig;
    _combineLastEmitSig = emitSig;
    var combined = (Array.isArray(events) ? events : []).concat(
      Array.isArray(enrichments) ? enrichments : []
    );
    var hasLinkedEnrichment =
      Array.isArray(enrichments) &&
      enrichments.some(function (event) {
        return event && event._enrichment_event_id != null;
      });
    _combineResult = hasLinkedEnrichment ? dedupeEvents(combined) : combined;
    return _combineResult;
  };

  [
    'filterExternalExclusions',
    'sortSourcesForDisplay',
    'collapseLongRunningEvents',
    'filterHiddenSources',
    'buildSearchIndex',
    'getPagedEvents',
  ].forEach(instrumentIngest);

  // issue-83: single named entry points keep Main.xmlui bindings tiny. The
  // engine re-parses inline {...} expressions on every render (no parse
  // cache), so parse cost scales with expression size; a short call
  // expression parses in microseconds. Each stage below is the
  // memoized + instrumented window.* wrapper installed above.
  var _chainFirstDone = false;
  window.processEvents = function (combined, hidden) {
    var result = window.buildSearchIndex(
      window.filterHiddenSources(
        window.collapseLongRunningEvents(
          window.sortSourcesForDisplay(window.filterExternalExclusions(combined))
        ),
        hidden
      )
    );
    if (!_chainFirstDone && result && result.length) {
      _chainFirstDone = true;
      try {
        performance.mark('cc-chain-first-done');
      } catch (e) {}
    }
    return result;
  };

  // boot-attribution-marks: one-read summary of every cc-* mark as ms
  // since navigation start, in fired order. In-memory only — marks live
  // in the page's Performance timeline and vanish on reload.
  window.__ccBootMarks = function () {
    var out = {};
    performance
      .getEntriesByType('mark')
      .filter(function (m) {
        return m.name.indexOf('cc') === 0;
      })
      .sort(function (a, b) {
        return a.startTime - b.startTime;
      })
      .forEach(function (m) {
        out[m.name] = Math.round(m.startTime);
      });
    return out;
  };

  // Date-tab window filter (#105): absolute {start, end} committed window
  // (prio-90: one object, not loose bounds). Null bounds (All) return the
  // input by reference, and the memo below keeps that stable identity so
  // downstream bindings skip re-rendering while the window is unchanged.
  memoizeIngest('filterByDateWindow', function (events, windowOrStartISO, endISOOrOpts, maybeOpts) {
    var startISO = windowOrStartISO;
    var endISO = endISOOrOpts;
    var opts = maybeOpts;
    if (
      windowOrStartISO != null &&
      typeof windowOrStartISO === 'object' &&
      !Array.isArray(windowOrStartISO) &&
      ('start' in windowOrStartISO || 'end' in windowOrStartISO)
    ) {
      startISO = windowOrStartISO.start;
      endISO = windowOrStartISO.end;
      opts = endISOOrOpts;
    }
    return [startISO, endISO, opts && opts.startTimeOnly ? 1 : 0, (opts && opts.timeZone) || ''];
  });

  window.clearDedupeCache = clearDedupeCache;
  window.isEventPicked = isEventPicked;
  window.eventMergedIds = eventMergedIds;
  window.dedupePicks = dedupePicks;
  window.buildGoogleCalendarUrl = buildGoogleCalendarUrl;
  window.downloadEventICS = downloadEventICS;
  // Enrichment helpers
  window.buildRRule = buildRRule;
  window.parseRRule = parseRRule;
  window.saveEnrichment = saveEnrichment;
  window.loadEnrichment = loadEnrichment;
  window.loadAllEnrichments = loadAllEnrichments;
  window.getEnrichmentFromCache = getEnrichmentFromCache;
  // issue-82: memoized export — Main.xmlui:139 evaluates this on every
  // binding pass, and an unstable result reference here cascades memo
  // misses through the whole processedEvents chain. Returning a stable
  // (always-array) result also neutralizes the markup's `|| []` fallback,
  // which would otherwise mint a fresh empty array per evaluation.
  // Capture the original first — reassigning window.expandEnrichments
  // rebinds the top-level function's own global identifier, so calling
  // `expandEnrichments` from inside the wrapper would recurse into the
  // wrapper itself (the file's other _-prefixed captures exist for the
  // same reason).
  var _expandEnrichmentsOrig = expandEnrichments;
  var _expandLastKey = null,
    _expandResult = null;
  window.expandEnrichments = function (enrichments, fromDateStr, toDateStr) {
    // Content-signature key, not reference: the engine's per-evaluation
    // value identities defeat ref keying (see combineEvents above), and
    // the rrule expansion inside is worth skipping.
    // The key must include enrichment content, not just length + endpoint
    // ids: same-shaped inputs with different fields (e.g. edited
    // description/location) must miss, otherwise stale virtual events leak
    // across edits. Enrichment lists are small (curator picks), so a JSON
    // signature over the expansion-relevant fields is cheap.
    var sig = Array.isArray(enrichments)
      ? enrichments.length +
        ':' +
        (enrichments.length
          ? enrichments[0].id + ':' + enrichments[enrichments.length - 1].id
          : '') +
        ':' +
        JSON.stringify(
          enrichments.map(function (e) {
            return [
              e.id,
              e.event_id,
              e.rrule,
              e.start_time,
              e.title,
              e.location,
              e.description,
              e.url,
              e.curator_name,
              e.city,
              e.end_time,
            ];
          })
        )
      : 'na';
    var key = sig + '|' + fromDateStr + '|' + toDateStr;
    if (key === _expandLastKey && _expandResult !== null) {
      return _expandResult;
    }
    _expandLastKey = key;
    _expandResult = _expandEnrichmentsOrig(enrichments, fromDateStr, toDateStr);
    return _expandResult;
  };
  window.getNextOccurrence = getNextOccurrence;
  window.formatPickDate = function (enrichments, eventId, startTime) {
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
  window.filterTileEvents = function (events, category, search) {
    if (!events || !Array.isArray(events)) return [];
    var result = events;
    if (category) {
      result = result.filter(function (e) {
        return e.category === category;
      });
    }
    if (search) {
      var term = search.toLowerCase();
      result = result.filter(function (e) {
        return (
          (e.title && e.title.toLowerCase().indexOf(term) >= 0) ||
          (e.description && e.description.toLowerCase().indexOf(term) >= 0) ||
          (e.location && e.location.toLowerCase().indexOf(term) >= 0)
        );
      });
    }
    return result;
  };

  window.getCityList = function () {
    return Object.keys(window._cities).sort();
  };

  window.defaultDashboardTile = function (city) {
    var id = 'tile-' + Date.now();
    return {
      i: id,
      city: city || window.cityFilter || window.getCityList()[0] || '',
      category: '',
      search: '',
    };
  };

  window.defaultDashboardLayout = function (tileId) {
    return { i: tileId, x: 0, y: 0, w: 6, h: 4 };
  };

  window.saveDashboardConfig = function (tiles, gridLayout, supabaseUrl, supabaseKey) {
    if (!window.authSession) return;
    var config = { tiles: tiles, gridLayout: gridLayout };
    fetch(supabaseUrl + '/rest/v1/user_settings?on_conflict=user_id,city', {
      method: 'POST',
      headers: {
        apikey: supabaseKey,
        Authorization: 'Bearer ' + window.authSession.access_token,
        'Content-Type': 'application/json',
        Prefer: 'resolution=merge-duplicates',
      },
      body: JSON.stringify({
        user_id: window.authUser.id,
        city: '_dashboard',
        dashboard: config,
        updated_at: new Date().toISOString(),
      }),
    });
  };
}
