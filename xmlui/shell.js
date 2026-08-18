window._xsLogs = [];

(function () {
  var isLocalConfigHost =
    /^(localhost|127(?:\.\d+){3}|0\.0\.0\.0)$/.test(window.location.hostname) ||
    window.location.protocol === 'file:';

  // async-boot-fetches (#82 item 4): the five boot resources download in
  // PARALLEL as fetch() promises (started in index.html so they overlap
  // the CDN scripts; window.__ccBootFetches). The engine scripts are then
  // DOM-inserted with async=false (order preserved) once everything has
  // resolved — the same before-engine guarantees the old sequential
  // sync-XHR chain gave, at max(RTT) instead of sum(RTT). Measured
  // deployed cost of the old chain: ~0.77 s of serial blocking XHRs.
  var isLocalDevHost = /^(localhost|127(?:\.\d+){3}|0\.0\.0\.0)$/.test(window.location.hostname);

  // boot-attribution-marks (cc-* namespace, in-memory Performance
  // timeline only; summarized by window.__ccBootMarks() in helpers.js).
  // DOMContentLoaded now fires long before the engine scripts load, so
  // register (or backfill) the mark immediately.
  if (document.readyState !== 'loading') {
    try { performance.mark('cc-dom-ready'); } catch (e) {}
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      try { performance.mark('cc-dom-ready'); } catch (e) {}
    });
  }

  function ccFetches() {
    if (window.__ccBootFetches) return window.__ccBootFetches;
    // Defensive fallback if index.html didn't start the prefetches.
    var bust = '?_=' + Date.now();
    var j = function (u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); };
    var t = function (u) { return fetch(u).then(function (r) { return r.ok ? r.text() : ''; }).catch(function () { return ''; }); };
    return {
      localConfig: isLocalConfigHost ? t('config.local.js' + bust) : Promise.resolve(''),
      config: j('config.json' + bust),
      version: t('version.txt' + bust),
      categories: j('../categories.json' + bust),
      cities: j('../cities.json' + bust),
      sourcePriority: j('../source_priority.json' + bust),
    };
  }

  function injectScripts(v) {
    function script(src) {
      var s = document.createElement('script');
      s.src = src;
      s.async = false; // preserve execution order across the chain
      document.head.appendChild(s);
      return s;
    }
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'xmlui/xmlui-grid-layout.css?v=' + v;
    document.head.appendChild(link);
    // The bundle bracket now spans download+eval (DOM-inserted scripts
    // have no between-download execution point to mark).
    try { performance.mark('cc-bundle-eval-start'); } catch (e) {}
    var bundle = script('xmlui/xmlui-standalone.umd.js?v=' + v);
    bundle.addEventListener('load', function () {
      try { performance.mark('cc-bundle-eval-end'); } catch (e) {}
    });
    script('xmlui/xmlui-masonry.js?v=' + v);
    script('xmlui/xmlui-grid-layout.js?v=' + v);
    script('helpers.js?v=' + v);
    script('xs-trace.js?v=' + v).addEventListener('load', function () {
      // index-standalone.ts arms startApp on DOMContentLoaded with no
      // readyState fallback, and DCL has long passed by the time the
      // DOM-inserted bundle evaluates — so start the engine explicitly
      // once the whole chain (bundle, extensions, helpers) has run.
      // Injection is gated on DCL below, so the engine's own listener
      // can never fire and double-start. (Upstream ask: a readyState
      // fallback in index-standalone.ts.)
      if (window.xmlui && typeof window.xmlui.startApp === 'function') {
        try { performance.mark('cc-xmlui-start'); } catch (e) {}
        window.xmlui.startApp(undefined, undefined, window.xmlui.standalone);
      }
    });
  }

  var F = ccFetches();
  Promise.all([F.localConfig, F.config, F.version, F.categories, F.cities, F.sourcePriority])
    .then(function (r) {
      var localCfg = r[0], cfg = r[1], fetchedVersion = (r[2] || '').trim();
      // config.local.js applies first, then config.json fills gaps —
      // same precedence as the old sync path.
      if (localCfg) { try { new Function(localCfg)(); } catch (e) {} }
      if (!window.SUPABASE_URL || !window.SUPABASE_KEY) {
        var globals = (cfg && cfg.appGlobals) || {};
        window.SUPABASE_URL = window.SUPABASE_URL || globals.supabaseUrl;
        window.SUPABASE_KEY = window.SUPABASE_KEY || globals.supabasePublishableKey;
      }
      try { performance.mark('cc-config-loaded'); } catch (e) {}

      var baseVersion = isLocalDevHost ? 'local-dev' : 'missing-version';
      if (fetchedVersion) baseVersion = fetchedVersion;
      try {
        var lastSeenVersion = localStorage.getItem('cc-shell-version');
        var hasReloadedForVersion = sessionStorage.getItem('cc-version-reload') === baseVersion;
        if (lastSeenVersion && lastSeenVersion !== baseVersion && !hasReloadedForVersion) {
          sessionStorage.setItem('cc-version-reload', baseVersion);
          localStorage.setItem('cc-shell-version', baseVersion);
          window.location.replace(window.location.pathname + window.location.search);
        } else {
          localStorage.setItem('cc-shell-version', baseVersion);
          if (hasReloadedForVersion) {
            sessionStorage.removeItem('cc-version-reload');
          }
        }
      } catch (e) {}

      var assetVersionSuffix = isLocalDevHost ? '-dev-' + Date.now() : '';
      window.APP_VERSION = baseVersion + assetVersionSuffix;

      window._categories = r[3];
      window._cities = r[4];
      window._sourcePriority = r[5];
      try { performance.mark('cc-static-json-loaded'); } catch (e) {}

      bootShell();
      // Gate injection on DCL so the engine's own DOMContentLoaded
      // listener is guaranteed dead by the time the bundle evaluates —
      // our explicit startApp above is then the only boot path.
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
          injectScripts(window.APP_VERSION);
        });
      } else {
        injectScripts(window.APP_VERSION);
      }
    });

  function bootShell() {

  var params = new URLSearchParams(window.location.search);
  var cityParam = params.get('city');
  window.embed = params.get('embed') === 'true';

  // config.json ships xsVerbose:false (the engine's trace serialization is
  // too slow for production). ?trace=true arms the engine's per-session
  // localStorage override before it boots, so the Inspector and trace
  // capture still work anywhere; ?trace=false disarms it.
  if (params.get('trace') === 'true') {
    try { localStorage.setItem('xmlui:xsVerbose', 'true'); } catch (e) {}
  } else if (params.get('trace') === 'false') {
    try { localStorage.removeItem('xmlui:xsVerbose'); } catch (e) {}
  }

  window.externalExclusions = null;
  var excludeUrl = params.get('exclude');
  if (excludeUrl) {
    try {
      var exhr = new XMLHttpRequest();
      exhr.open('GET', excludeUrl, false);
      if (excludeUrl.indexOf('api.github.com') !== -1) {
        exhr.setRequestHeader('Accept', 'application/vnd.github.v3+json');
      }
      exhr.send();
      if (exhr.status === 200) {
        var resp = JSON.parse(exhr.responseText);
        if (resp.content && resp.encoding === 'base64') {
          window.externalExclusions = JSON.parse(decodeURIComponent(escape(atob(resp.content))));
        } else {
          window.externalExclusions = resp;
        }
      }
    } catch (e) {}
  }

  window.hasLayoutModeParam = params.has('mode');
  window.layoutMode = params.get('mode') || 'list';
  window.setLayoutMode = function (val) {
    window.layoutMode = val;
    var url = new URL(window.location);
    if (val === 'multicol' || val === 'dashboard') {
      url.searchParams.set('mode', val);
    } else {
      url.searchParams.delete('mode');
    }
    window.history.replaceState({}, '', url);
  };

  window.hasImagesParam = params.has('images');
  window.showListImages = params.get('images') !== 'preview';
  window.setShowListImages = function (val) {
    window.showListImages = val !== 'preview';
    var url = new URL(window.location);
    if (val === 'preview') {
      url.searchParams.set('images', 'preview');
    } else {
      url.searchParams.delete('images');
    }
    window.history.replaceState({}, '', url);
  };

  window.initialCategory = params.get('category') || '';
  window.initialSearch = params.get('search') || '';

  // ?cards=N overrides the browse page size (default 50, clamped 1..500).
  // Boot-time constant, same pattern as initialSearch. Search-mode paging
  // stays at 10 regardless; pageSizeFor is the one place that rule lives.
  var cardsParam = parseInt(params.get('cards'), 10);
  window.cardPageSize = cardsParam >= 1 && cardsParam <= 500 ? cardsParam : 50;
  window.pageSizeFor = function (term) {
    return term ? 10 : window.cardPageSize;
  };

  var cityNameOverrides = {
    santarosa: 'Santa Rosa',
    raleighdurham: 'Raleigh-Durham',
  };

  window.toDisplayName = function (slug) {
    if (!slug) return '';
    var name = cityNameOverrides[slug] || slug.charAt(0).toUpperCase() + slug.slice(1);
    return name + ' Now';
  };

  window.cityFilter = cityParam || null;
  window.cityName = window.toDisplayName(cityParam);
  if (cityParam) {
    document.title = window.cityName + ' Community Calendar';
  }

  window.selectCity = function (slug) {
    var url = new URL(window.location);
    url.searchParams.set('city', slug);
    window.history.pushState({}, '', url);
    window.cityFilter = slug;
    window.cityName = window.toDisplayName(slug);
    document.title = window.cityName + ' Community Calendar';
  };

  var SUPABASE_URL = window.SUPABASE_URL;
  var SUPABASE_KEY = window.SUPABASE_KEY;
  var sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

  window.authUser = null;
  window.authSession = null;
  try {
    var projRef = new URL(SUPABASE_URL).hostname.split('.')[0];
    var stored = localStorage.getItem('sb-' + projRef + '-auth-token');
    if (stored) {
      var parsed = JSON.parse(stored);
      if (parsed.user && parsed.expires_at) {
        var nowSec = Math.floor(Date.now() / 1000);
        if (parsed.expires_at > nowSec) {
          window.authUser = parsed.user;
          window.authSession = parsed;
        }
      }
    }
  } catch (e) {}

  window.signIn = function (provider) {
    var returnTo = window.location.origin + window.location.pathname + window.location.search;
    window.location.href =
      SUPABASE_URL +
      '/auth/v1/authorize?provider=' +
      (provider || 'github') +
      '&redirect_to=' +
      encodeURIComponent(returnTo);
  };

  window.signInWithEmail = async function (email, onSuccess) {
    var result = await sb.auth.signInWithOtp({
      email: email,
      options: { emailRedirectTo: window.location.origin + window.location.pathname + window.location.search },
    });
    if (result.error) alert('Error: ' + result.error.message);
    else if (onSuccess) onSuccess();
  };

  window.verifyEmailOtp = async function (email, token, onSuccess) {
    var result = await sb.auth.verifyOtp({ email: email, token: token, type: 'email' });
    if (result.error) alert('Error: ' + result.error.message);
    else if (onSuccess) onSuccess();
  };

  window.signOut = function () {
    console.log('signOut called');
    localStorage.removeItem('sb-dzpdualvwspgqghrysyz-auth-token');
    console.log('localStorage cleared, reloading...');
    window.location.reload();
  };

  sb.auth.onAuthStateChange(async function (event, session) {
    window.authSession = session;
    window.authUser = session && session.user ? session.user : null;
    console.log('Auth state changed:', event, window.authUser && window.authUser.email);

    if (session && session.user) {
      try {
        var headers = {
          apikey: SUPABASE_KEY,
          Authorization: 'Bearer ' + session.access_token,
          'Content-Type': 'application/json',
          Prefer: 'return=minimal',
        };

        var checkUrl = SUPABASE_URL + '/rest/v1/feed_tokens?select=token&user_id=eq.' + session.user.id;
        var checkRes = await fetch(checkUrl, { headers: headers });
        if (!checkRes.ok) {
          console.warn('Feed token check failed:', checkRes.status);
          return;
        }
        var existing = await checkRes.json();
        console.log('Feed token check:', existing);

        if (!existing || existing.length === 0) {
          var insertUrl = SUPABASE_URL + '/rest/v1/feed_tokens';
          var insertRes = await fetch(insertUrl, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ user_id: session.user.id }),
          });
          if (insertRes.ok) {
            console.log('Created feed token for new user, reloading...');
            window.location.reload();
          } else {
            console.error('Error creating feed token:', insertRes.status);
          }
        }
      } catch (err) {
        console.warn('Feed token bootstrap skipped:', (err && err.message) || err);
      }
    }
  });

  if (window.location.hash.includes('access_token')) {
    sb.auth.getSession().then(function () {
      window.location.replace(window.location.pathname + window.location.search);
    });
  }

  window.togglePick = async function (eventId) {
    console.log('togglePick called with eventId:', eventId);
    if (!window.authSession) {
      alert('Please sign in to pick events');
      return;
    }
    var headers = {
      apikey: SUPABASE_KEY,
      Authorization: 'Bearer ' + window.authSession.access_token,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
    };
    var userId = window.authUser.id;

    var checkUrl = SUPABASE_URL + '/rest/v1/picks?select=id&user_id=eq.' + userId + '&event_id=eq.' + eventId;
    var checkRes = await fetch(checkUrl, { headers: headers });
    var existing = await checkRes.json();
    console.log('Existing picks:', existing);

    if (existing && existing.length > 0) {
      console.log('Removing pick:', existing[0].id);
      var deleteUrl = SUPABASE_URL + '/rest/v1/picks?id=eq.' + existing[0].id;
      var deleteRes = await fetch(deleteUrl, { method: 'DELETE', headers: headers });
      console.log('Delete response:', deleteRes.status);
      if (window.xsTraceEvent) window.xsTraceEvent('unpick', { eventId: eventId, status: deleteRes.status });
    } else {
      console.log('Adding pick for event:', eventId);
      var insertUrl = SUPABASE_URL + '/rest/v1/picks';
      var insertRes = await fetch(insertUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ user_id: userId, event_id: eventId }),
      });
      console.log('Insert response:', insertRes.status);
      if (window.xsTraceEvent) window.xsTraceEvent('pick', { eventId: eventId, status: insertRes.status });
    }
  };

  (function () {
    var now = new Date();
    var oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    var threeMonthsLater = new Date(now.getTime() + 90 * 24 * 60 * 60 * 1000);
    window.fromDate = oneHourAgo.toISOString();
    window.toDate = threeMonthsLater.toISOString();
    console.log('Date range initialized:', window.fromDate, 'to', window.toDate);
  })();

  window.getFromDate = function () {
    return window.fromDate;
  };
  window.getToDate = function () {
    return window.toDate;
  };
  window.getQueryMonths = function () {
    var from = new Date(window.fromDate);
    var to = new Date(window.toDate);
    return Math.round((to - from) / (30 * 24 * 60 * 60 * 1000));
  };

  // Events prefetch + cache. The events fetch starts here, at boot, instead
  // of waiting ~500ms for the XMLUI engine to evaluate a DataSource. The
  // last payload per city is kept in IndexedDB so repeat visits paint
  // immediately from cache while the network fetch refreshes in the
  // background. Main.xmlui consumes this through a PushSource bound to
  // window.subscribeEvents; window.refetchEvents replaces events.refetch().
  (function () {
    var STORE = 'payloads';
    function idbOpen() {
      return new Promise(function (resolve, reject) {
        var req = indexedDB.open('cc-events-cache', 1);
        req.onupgradeneeded = function () { req.result.createObjectStore(STORE); };
        req.onsuccess = function () { resolve(req.result); };
        req.onerror = function () { reject(req.error); };
      });
    }
    function idbGet(key) {
      return idbOpen().then(function (db) {
        return new Promise(function (resolve, reject) {
          var req = db.transaction(STORE, 'readonly').objectStore(STORE).get(key);
          req.onsuccess = function () { resolve(req.result); };
          req.onerror = function () { reject(req.error); };
        });
      });
    }
    function idbSet(key, val) {
      return idbOpen().then(function (db) {
        return new Promise(function (resolve, reject) {
          var tx = db.transaction(STORE, 'readwrite');
          tx.objectStore(STORE).put(val, key);
          tx.oncomplete = function () { resolve(); };
          tx.onerror = function () { reject(tx.error); };
        });
      });
    }

    var fetchPromise = null;
    var fetchCity = null;
    var currentEmit = null;
    var cachedPromise = null;
    var cachedCity = null;
    // issue-82 emission coalescing state. lastEmitFn tracks WHICH
    // subscriber received the last emission — an identical-data skip is
    // only safe for a subscriber that already has the data; a fresh
    // subscriber (resubscribe after a city round-trip) must always get
    // its first emit.
    var fetchResolvedCity = null;
    var lastEmitFn = null;
    var lastEmitCity = null;
    var lastEmitSig = null;

    function rowsSig(rows) {
      return rows.length + ':' +
        (rows.length ? rows[0].id + ':' + rows[rows.length - 1].id : '');
    }

    function eventsUrl(city) {
      return window.SUPABASE_URL + '/rest/v1/deduplicated_events' +
        '?select=id,title,start_time,end_time,url,location,description,source,transcript,cluster_id,source_urls,category,image_url,all_day,merged_ids,city' +
        '&order=start_time.asc&limit=6000' +
        '&start_time=gte.' + window.fromDate +
        '&start_time=lte.' + window.toDate +
        '&city=eq.' + encodeURIComponent(city);
    }

    function startFetch(city) {
      fetchCity = city;
      fetchResolvedCity = null;
      fetchPromise = fetch(eventsUrl(city), {
        headers: {
          apikey: window.SUPABASE_KEY,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }).then(function (res) { return res.json(); }).then(function (rows) {
        if (Array.isArray(rows)) {
          fetchResolvedCity = city;
          // True network completion, independent of any subscriber —
          // cc-events-emit-fresh records delivery, which collapses to
          // subscription time when the response wins that race.
          try { performance.mark('cc-events-fetch-resolved'); } catch (e) {}
        }
        return rows;
      });
      return fetchPromise;
    }

    function deliverFresh(promise, city) {
      return promise.then(function (rows) {
        if (!Array.isArray(rows)) return false;
        // rows are genuinely `city`'s rows — cache them even if the user has
        // switched away, but only emit if this city is still current.
        idbSet('events:' + city, rows).catch(function () {});
        if (city !== window.cityFilter) return false;  // stale-city race guard (#76)
        // issue-82: skip the replacement when this same subscriber already
        // holds identical data — the emit would only trigger a re-render.
        if (currentEmit && currentEmit === lastEmitFn &&
            city === lastEmitCity && rowsSig(rows) === lastEmitSig) {
          performance.mark('cc-events-skip-fresh-identical');
          return true;
        }
        performance.mark('cc-events-emit-fresh');
        if (currentEmit) {
          lastEmitFn = currentEmit;
          lastEmitCity = city;
          lastEmitSig = rowsSig(rows);
          currentEmit(rows);
        }
        return true;
      }).catch(function () { return false; });
    }

    function startCacheRead(city) {
      cachedCity = city;
      cachedPromise = idbGet('events:' + city).catch(function () { return null; });
      return cachedPromise;
    }

    window.subscribeEvents = function (emit) {
      currentEmit = emit;
      var city = window.cityFilter;
      if (!city) return;
      var gotFresh = false;
      // Cached copy paints first, unless the network won the race. The read
      // was started at boot, so by subscribe time it has usually resolved
      // and the emit fires immediately.
      var c = (cachedPromise && cachedCity === city) ? cachedPromise : startCacheRead(city);
      c.then(function (cached) {
        if (Array.isArray(cached) && !gotFresh) {
          if (city !== window.cityFilter) return;  // stale-city guard (#76)
          // issue-82: when the network fetch has already resolved, the
          // fresh emit is imminent — a cached paint would only add a
          // full ingest+render that is immediately redone.
          if (fetchResolvedCity === city) {
            performance.mark('cc-events-skip-cached-superseded');
            return;
          }
          performance.mark('cc-events-emit-cached');
          lastEmitFn = emit;
          lastEmitCity = city;
          lastEmitSig = rowsSig(cached);
          emit(cached);
        }
      });
      var p = (fetchPromise && fetchCity === city) ? fetchPromise : startFetch(city);
      deliverFresh(p, city).then(function (ok) { if (ok) gotFresh = true; });
      return function () { if (currentEmit === emit) currentEmit = null; };
    };

    window.refetchEvents = function () {
      var city = window.cityFilter;
      if (!city) return;
      deliverFresh(startFetch(city), city);
    };

    if (window.cityFilter) {
      startCacheRead(window.cityFilter);
      startFetch(window.cityFilter);
    }
  })();

  window.ccAutoHeight = new URLSearchParams(location.search).get('autoheight') === 'true';
  if (window.ccAutoHeight && window.parent !== window) {
    (function () {
      var lastH = 0;
      var observer = null;

      function report(el) {
        var h = Math.ceil(el.getBoundingClientRect().height);
        if (h === lastH || h === 0) return;
        lastH = h;
        window.parent.postMessage({ type: 'cc-embed-resize', height: h }, '*');
      }

      function findAndObserve() {
        var el = document.querySelector('[data-xmlui-app-fit-content]');
        if (!el) return false;
        if ('ResizeObserver' in window) {
          observer = new ResizeObserver(function () {
            report(el);
          });
          observer.observe(el);
        }
        report(el);
        return true;
      }

      var tries = 0;
      var findIv = setInterval(function () {
        if (findAndObserve() || ++tries > 80) clearInterval(findIv);
      }, 50);
    })();
  }
  } // end bootShell
})();
