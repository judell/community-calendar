window._xsLogs = [];

(function () {
  var isLocalConfigHost =
    /^(localhost|127(?:\.\d+){3}|0\.0\.0\.0)$/.test(window.location.hostname) ||
    window.location.protocol === 'file:';

  function loadJsonFallback() {
    try {
      var cfgXhr = new XMLHttpRequest();
      cfgXhr.open('GET', 'config.json?_=' + Date.now(), false);
      cfgXhr.send();
      if (cfgXhr.status === 200) {
        var cfg = JSON.parse(cfgXhr.responseText);
        var globals = (cfg && cfg.appGlobals) || {};
        window.SUPABASE_URL = window.SUPABASE_URL || globals.supabaseUrl;
        window.SUPABASE_KEY = window.SUPABASE_KEY || globals.supabasePublishableKey;
      }
    } catch (e) {}
  }

  if (isLocalConfigHost) {
    try {
      var localXhr = new XMLHttpRequest();
      localXhr.open('GET', 'config.local.js?_=' + Date.now(), false);
      localXhr.send();
      if (localXhr.status === 200 && localXhr.responseText) {
        new Function(localXhr.responseText)();
      }
    } catch (e) {}
  }

  if (!window.SUPABASE_URL || !window.SUPABASE_KEY) {
    loadJsonFallback();
  }

  var versionProbe = Date.now();
  var vxhr = new XMLHttpRequest();
  vxhr.open('GET', 'version.txt?_=' + versionProbe, false);
  var isLocalDevHost = /^(localhost|127(?:\.\d+){3}|0\.0\.0\.0)$/.test(window.location.hostname);
  var baseVersion = isLocalDevHost ? 'local-dev' : 'missing-version';
  try {
    vxhr.send();
    if (vxhr.status >= 200 && vxhr.status < 300) {
      var fetchedVersion = (vxhr.responseText || '').trim();
      if (fetchedVersion) {
        baseVersion = fetchedVersion;
      }
    }
  } catch (e) {}
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
  var v = window.APP_VERSION;

  document.write('<script src="xmlui/xmlui-standalone.umd.js?v=' + v + '"><\/script>');
  document.write('<script src="xmlui/xmlui-masonry.js?v=' + v + '"><\/script>');
  document.write('<link rel="stylesheet" href="xmlui/xmlui-grid-layout.css?v=' + v + '">');
  document.write('<script src="xmlui/xmlui-grid-layout.js?v=' + v + '"><\/script>');

  var xhr = new XMLHttpRequest();
  xhr.open('GET', '../categories.json?v=' + window.APP_VERSION, false);
  xhr.send();
  window._categories = JSON.parse(xhr.responseText);

  var cxhr = new XMLHttpRequest();
  cxhr.open('GET', '../cities.json?v=' + window.APP_VERSION, false);
  cxhr.send();
  window._cities = JSON.parse(cxhr.responseText);

  var spxhr = new XMLHttpRequest();
  spxhr.open('GET', '../source_priority.json?v=' + window.APP_VERSION, false);
  spxhr.send();
  window._sourcePriority = JSON.parse(spxhr.responseText);

  document.write('<script src="helpers.js?v=' + window.APP_VERSION + '"><\/script>');
  document.write('<script src="xs-trace.js?v=' + window.APP_VERSION + '"><\/script>');

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

  var cityNameOverrides = {
    santarosa: 'Santa Rosa',
    raleighdurham: 'Raleigh-Durham',
    tetonvalley: 'Teton Valley',
    'dc-music': 'DC Music',
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
      fetchPromise = fetch(eventsUrl(city), {
        headers: {
          apikey: window.SUPABASE_KEY,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
        },
      }).then(function (res) { return res.json(); });
      return fetchPromise;
    }

    function deliverFresh(promise, city) {
      return promise.then(function (rows) {
        if (!Array.isArray(rows)) return false;
        performance.mark('cc-events-emit-fresh');
        if (currentEmit) currentEmit(rows);
        idbSet('events:' + city, rows).catch(function () {});
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
          performance.mark('cc-events-emit-cached');
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
})();
