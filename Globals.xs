// Global variables and functions accessible from all XMLUI components

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
