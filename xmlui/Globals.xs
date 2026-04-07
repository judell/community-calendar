// Code-behind for Main.xmlui
// All variables and functions here are global (visible to all components)

var categoryColorMap = window.categoryColorMap;


var layoutMode = window.layoutMode;
var showListImages = window.showListImages;
var oneClickPick = false;

var categoryFilter = window.initialCategory || '';
var pickEvent = null;
var enrichmentsData = null;
var picksCounter = 0;
var eventsCounter = 0;

// Dashboard state — null means "use server data", non-null means "user has modified"
var dashboardTiles = null;
var dashboardGridLayout = null;


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
    picksCounter = picksCounter + 1;
  } else if (oneClickPick && event.id) {
    // One-click pick: skip the editor and create pick directly
    Actions.callApi({
      method: 'post',
      url: appGlobals.supabaseUrl + '/rest/v1/picks',
      headers: Object.assign({}, headers, {
        'Content-Type': 'application/json',
        Prefer: 'return=minimal'
      }),
      body: {
        user_id: authUser.id,
        event_id: event.id
      },
      invalidates: []
    });
    picksCounter = picksCounter + 1;
  } else {
    // Picking: set pickEvent to trigger PickEditor via when
    pickEvent = event;
  }
}

function toggleSourceVisibility(source) {
  if (!authSession) return;
  userSettingsData = window.toggleSourceAndSave(source, userSettingsData, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
}

function applyHiddenSources(hiddenArray) {
  if (authSession) {
    userSettingsData = window.saveHiddenSources(hiddenArray, userSettingsData, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
  } else {
    localStorage.setItem('hidden_sources', JSON.stringify(hiddenArray));
    userSettingsData = [{ hidden_sources: hiddenArray }];
  }
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
    onSuccess: () => { eventsCounter = eventsCounter + 1; },
  });
}

// Dashboard functions
function addTile() {
  const tile = window.defaultDashboardTile(city);
  const layout = window.defaultDashboardLayout(tile.i);
  const newTiles = (dashboardTiles || []).concat([tile]);
  const newLayout = (dashboardGridLayout || []).concat([layout]);
  dashboardTiles = newTiles;
  dashboardGridLayout = newLayout;
  persistDashboard(newTiles, newLayout);
}

function removeTile(tileId) {
  const newTiles = (dashboardTiles || []).filter(t => t.i !== tileId);
  const newLayout = (dashboardGridLayout || []).filter(l => l.i !== tileId);
  dashboardTiles = newTiles;
  dashboardGridLayout = newLayout;
  persistDashboard(newTiles, newLayout);
}

function updateTile(tileId, field, value) {
  const newTiles = (dashboardTiles || []).map(t => {
    if (t.i !== tileId) return t;
    const updated = Object.assign({}, t);
    updated[field] = value;
    return updated;
  });
  dashboardTiles = newTiles;
  persistDashboard(newTiles, dashboardGridLayout || (dashboardGridLayout || []));
}

function updateGridLayout(newLayout) {
  const tiles = (dashboardTiles || []);
  const newGridLayout = newLayout.map(function(item, idx) {
    if (tiles[idx] && item.i !== tiles[idx].i) {
      return Object.assign({}, item, { i: tiles[idx].i });
    }
    return item;
  });
  dashboardGridLayout = newGridLayout;
  persistDashboard(dashboardTiles || tiles, newGridLayout);
}

function persistDashboard(tiles, layout) {
  window.saveDashboardConfig(tiles, layout, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
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
  picksCounter = picksCounter + 1;
}
