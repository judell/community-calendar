/**
 * Generic app-level timing for XMLUI inspector traces.
 *
 * Include this script in any XMLUI app to time expensive functions
 * and have them appear in the xs-diff.html inspector timeline.
 *
 * Usage:
 *   <script src="trace-tools/xs-trace.js"></script>
 *
 * Then wrap expensive calls:
 *   window.xsTrace("filterEvents", () => filterEvents(events, term))
 *
 * Entries appear as "app:timing" in the inspector alongside
 * handler:start/complete and api:start/complete entries.
 */
(function () {
  window.xsTrace = function (label, fn) {
    var logs = window._xsLogs;
    if (!logs) return fn();
    var traceId = logs.length > 0 ? logs[logs.length - 1].traceId : undefined;
    var start = performance.now();
    var result = fn();
    var duration = performance.now() - start;
    logs.push({
      kind: "app:timing",
      label: label,
      traceId: traceId,
      perfTs: start,
      duration: duration,
    });
    return result;
  };
})();
