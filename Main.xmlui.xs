// Code-behind for Main.xmlui
// Note: window.refreshPicks must live here (not in Globals.xs) because
// referencing DataSource IDs inside Globals.xs functions triggers reactive loops.

window.refreshPicks = function() {
  if (typeof events !== 'undefined' && events.refresh) {
    events.refresh();
  }
  if (typeof picks !== 'undefined' && picks.refresh) {
    picks.refresh();
  }
  if (typeof enrichments !== 'undefined' && enrichments.refetch) {
    enrichments.refetch();
  }
};
