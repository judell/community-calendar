// Code-behind for Main.xmlui
// All variables and functions here are global (visible to all components)

var categoryColorMap = window.categoryColorMap;

var layoutMode = window.layoutMode;
var showListImages = window.showListImages;

var categoryFilter = window.initialCategory || '';
var pickEvent = null;
var picksData = null;
var enrichmentsData = null;
var refreshCounter = 0;

// Dashboard state — start with one default tile
var _defaultTile = { i: 'tile-1', city: window.getCityList()[0] || 'santarosa', category: window.categoryList[0] || '', search: '' };
var dashboardTiles = [_defaultTile];
var dashboardGridLayout = [{ i: 'tile-1', x: 0, y: 0, w: 6, h: 4 }];
var dashboardSettingsLoaded = false;

function setCategoryFilter(category) {
  categoryFilter = category || '';
  window.syncCategoryParam(categoryFilter);
}

function togglePick(event) {
  if (!authSession) {
    alert('Please sign in to pick events');
    return;
  }
  const headers = {
    apikey: appGlobals.supabasePublishableKey,
    Authorization: 'Bearer ' + authSession?.access_token
  };
  const ids = event.mergedIds || [event.id];
  const existing = Actions.callApi({
    method: 'get',
    url: appGlobals.supabaseUrl + '/rest/v1/picks?select=id&user_id=eq.' + authUser.id + '&event_id=in.(' + ids.join(',') + ')',
    headers,
    invalidates: []
  });
  if (existing?.length > 0) {
    // Unpicking: one-click remove pick + any enrichment for this event
    Actions.callApi({
      method: 'delete',
      url: appGlobals.supabaseUrl + '/rest/v1/picks?id=eq.' + existing[0].id,
      headers,
      invalidates: []
    });
    // Also delete any enrichment the user created for these event IDs
    ids.forEach(function(eid) {
      Actions.callApi({
        method: 'delete',
        url: appGlobals.supabaseUrl + '/rest/v1/event_enrichments?event_id=eq.' + eid + '&curator_id=eq.' + authUser.id,
        headers,
        invalidates: []
      });
    });
    refreshCounter = refreshCounter + 1;
  } else {
    // Picking: set pickEvent to trigger PickEditor via when
    pickEvent = event;
  }
}

function toggleSourceVisibility(source) {
  if (!authSession) return;
  userSettingsData = window.toggleSourceAndSave(source, userSettingsData, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
}


function saveCategoryOverride(eventId, category) {
  if (!authSession) return;
  const headers = {
    apikey: appGlobals.supabasePublishableKey,
    Authorization: 'Bearer ' + authSession?.access_token,
  };
  // Upsert override (on_conflict=event_id)
  // DB trigger on category_overrides automatically updates events.category
  Actions.callApi({
    method: 'post',
    url: appGlobals.supabaseUrl + '/rest/v1/category_overrides?on_conflict=event_id',
    headers: Object.assign({}, headers, {
      'Content-Type': 'application/json',
      Prefer: 'return=minimal,resolution=merge-duplicates',
    }),
    body: {
      event_id: eventId,
      category: category,
      curator_id: authUser.id,
    },
    invalidates: [],
    onSuccess: () => { refreshCounter = refreshCounter + 1; },
  });
}

// Dashboard functions
function addTile() {
  const tile = window.defaultDashboardTile(city);
  const layout = window.defaultDashboardLayout(tile.i);
  dashboardTiles = dashboardTiles.concat([tile]);
  dashboardGridLayout = dashboardGridLayout.concat([layout]);
  persistDashboard();
}

function removeTile(tileId) {
  dashboardTiles = dashboardTiles.filter(t => t.i !== tileId);
  dashboardGridLayout = dashboardGridLayout.filter(l => l.i !== tileId);
  persistDashboard();
}

function updateTile(tileId, field, value) {
  dashboardTiles = dashboardTiles.map(t => {
    if (t.i !== tileId) return t;
    const updated = Object.assign({}, t);
    updated[field] = value;
    return updated;
  });
  persistDashboard();
}

function updateGridLayout(newLayout) {
  // Reconcile layout item IDs with tile IDs — react-grid-layout may
  // report fallback index keys if layout/children are briefly out of sync
  dashboardGridLayout = newLayout.map(function(item, idx) {
    if (dashboardTiles[idx] && item.i !== dashboardTiles[idx].i) {
      return Object.assign({}, item, { i: dashboardTiles[idx].i });
    }
    return item;
  });
  persistDashboard();
}

function persistDashboard() {
  if (!dashboardSettingsLoaded) return;
  window.saveDashboardConfig(dashboardTiles, dashboardGridLayout, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
}

function removePick(pickId) {
  Actions.callApi({
    method: 'delete',
    url: appGlobals.supabaseUrl + '/rest/v1/picks?id=eq.' + pickId,
    headers: {
      apikey: appGlobals.supabasePublishableKey,
      Authorization: 'Bearer ' + authSession?.access_token
    },
    invalidates: []
  });
  refreshCounter = refreshCounter + 1;
}
