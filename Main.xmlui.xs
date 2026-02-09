// Code-behind for Main.xmlui
// These functions have access to XMLUI globals (appGlobals, Actions)

// Expose refreshPicks globally for CaptureDialog to call after adding an event
window.refreshPicks = function() {
  // Refresh both events and picks DataSources
  if (typeof events !== 'undefined' && events.refresh) {
    events.refresh();
  }
  if (typeof picks !== 'undefined' && picks.refresh) {
    picks.refresh();
  }
};

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
    // Unpicking: one-click remove, no modal
    Actions.callApi({
      method: 'delete',
      url: appGlobals.supabaseUrl + '/rest/v1/picks?id=eq.' + existing[0].id,
      headers,
      invalidates: []
    });
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
}
