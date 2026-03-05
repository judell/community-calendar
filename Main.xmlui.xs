// Code-behind for Main.xmlui
// All variables and functions here are global (visible to all components)

window.categoryColorMap = {
  'Music & Concerts':        { label: '#fff', background: '#8b5cf6' },
  'Sports & Fitness':        { label: '#fff', background: '#059669' },
  'Arts & Culture':          { label: '#fff', background: '#d97706' },
  'Education & Workshops':   { label: '#fff', background: '#2563eb' },
  'Community & Social':      { label: '#fff', background: '#dc2626' },
  'Family & Kids':           { label: '#fff', background: '#ec4899' },
  'Food & Drink':            { label: '#fff', background: '#ea580c' },
  'Health & Wellness':       { label: '#fff', background: '#0d9488' },
  'Nature & Outdoors':       { label: '#fff', background: '#16a34a' },
  'Religion & Spirituality': { label: '#fff', background: '#7c3aed' },
};

var pickEvent = null;
var picksData = null;
var enrichmentsData = null;
var refreshCounter = 0;

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
