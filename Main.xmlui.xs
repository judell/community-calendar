// Code-behind for Main.xmlui
// All variables and functions here are global (visible to all components)

var categoryColorMap = window.categoryColorMap;

var categoryFilter = window.initialCategory || '';
var pickEvent = null;
var picksData = null;
var enrichmentsData = null;
var refreshCounter = 0;

function setCategoryFilter(category) {
  categoryFilter = category || '';
  window.syncCategoryParam(categoryFilter);
}

function togglePick(event) {
  if (!window.authSession) {
    alert('Please sign in to pick events');
    return;
  }
  const headers = {
    apikey: appGlobals.supabasePublishableKey,
    Authorization: 'Bearer ' + window.authSession?.access_token
  };
  const ids = event.mergedIds || [event.id];
  const existing = Actions.callApi({
    method: 'get',
    url: appGlobals.supabaseUrl + '/rest/v1/picks?select=id&user_id=eq.' + window.authUser.id + '&event_id=in.(' + ids.join(',') + ')',
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
        url: appGlobals.supabaseUrl + '/rest/v1/event_enrichments?event_id=eq.' + eid + '&curator_id=eq.' + window.authUser.id,
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
  if (!window.authSession) return;
  userSettingsData = window.toggleSourceAndSave(source, userSettingsData, appGlobals.supabaseUrl, appGlobals.supabasePublishableKey);
}


function saveCategoryOverride(eventId, category) {
  if (!window.authSession) return;
  const headers = {
    apikey: appGlobals.supabasePublishableKey,
    Authorization: 'Bearer ' + window.authSession?.access_token,
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
      curator_id: window.authUser.id,
    },
    invalidates: [],
    onSuccess: () => { refreshCounter = refreshCounter + 1; },
  });
}

function removePick(pickId) {
  Actions.callApi({
    method: 'delete',
    url: appGlobals.supabaseUrl + '/rest/v1/picks?id=eq.' + pickId,
    headers: {
      apikey: appGlobals.supabasePublishableKey,
      Authorization: 'Bearer ' + window.authSession?.access_token
    },
    invalidates: []
  });
  refreshCounter = refreshCounter + 1;
}
