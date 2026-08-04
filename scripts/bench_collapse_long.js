#!/usr/bin/env node
// Adopted verbatim from the B-Square-Bulletin/community-calendar fork
// (their scripts/bench_collapse_long.js, per their ADR 0004 "Upstream Sync
// Verification Protocol"). Brought upstream so this regression is caught in
// our PRs instead of after a fork has merged it. Thanks to the B-Square team.
//
// bench_collapse_long.js — verify the content-key cache in collapseLongRunningEvents
//
// Regression scenario (upstream issue judell/community-calendar#77, mirrored in
// the fork's issue doc): with the PushSource + IndexedDB pattern, the
// processedEvents pipeline runs TWICE on page load — first with cached data,
// then with network data. The two arrays have the same content but different
// object *references*. collapseLongRunningEvents used to key its cache on
// object identity (events[0] === _collapseLastFirst), so the second run always
// missed and recomputed (~254-336ms for ~3,200 events), blocking the main
// thread exactly when the user starts typing.
//
// The fix (upstream dff810892) keys the cache on content (events.length +
// first/last event id). This benchmark loads the MERGED xmlui/helpers.js,
// runs the function twice with fresh object references, and asserts:
//   1. run #2 is a cache HIT (logged via window._pipelineLog)
//   2. run #2 is ~0ms (the regression was 254-336ms)
//   3. run #2 returns identical results to run #1
//
// Usage:
//   node scripts/bench_collapse_long.js                 # synthetic events
//   node scripts/bench_collapse_long.js --events data.json  # real events
//
// Exit code 0 = verified, 1 = regression detected.

'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');

// --- Window shim (helpers.js is browser-global code) -----------------------
// helpers.js reads window._categories at load and window._cities / cityFilter
// inside getCityTimezone(). Mirror what xmlui/test.html and index.html set up.
const categories = JSON.parse(fs.readFileSync(path.join(ROOT, 'categories.json'), 'utf8'));
const sourcePriority = JSON.parse(fs.readFileSync(path.join(ROOT, 'source_priority.json'), 'utf8'));

const windowObj = {
  _categories: categories,
  _sourcePriority: sourcePriority,
  _cities: { bloomington: { timezone: 'America/Indiana/Indianapolis' } },
  cityFilter: 'bloomington',
  _pipelineLog: [],
  performance: performance, // Node global
};
windowObj.window = windowObj; // some code paths reference window.window
windowObj.self = windowObj;
windowObj.globalThis = globalThis;

const sandbox = { window: windowObj, performance, console, setTimeout, Date, Set, URLSearchParams, location: { search: '' } };
sandbox.global = sandbox;
vm.createContext(sandbox);

const helpersSrc = fs.readFileSync(path.join(ROOT, 'xmlui', 'helpers.js'), 'utf8');
vm.runInContext(helpersSrc, sandbox, { filename: 'xmlui/helpers.js' });

// --- Event generation -------------------------------------------------------
function syntheticEvents(count, opts = {}) {
  const rng = opts.rng || (() => Math.random());
  const titles = [
    'Gallery Opening Reception', 'Farmers Market', 'Book Club Discussion',
    'Yoga in the Park', 'Live Jazz Night', 'Film Screening Series',
    'Art Exhibition', 'Community Cleanup', 'Poetry Slam', 'Craft Workshop',
  ];
  const locations = [
    'Buskirk-Chumley Theater', 'WonderLab Museum', 'Monroe County Public Library',
    'Switchyard Park', 'B-Line Trail', 'IU Auditorium', 'The Bishop Bar',
  ];
  const sources = ['visitbloomington.com', 'buskirkchumley.org', 'monroe.lib.in.us',
    'wfhb.org', 'bloomington.in.gov', 'iub.edu', 'eventbrite.com'];

  const now = Date.now();
  const events = [];
  // ~15% long-running series (same title+location+time-of-day, weekly) so the
  // collapse logic has real work to do, like the production payload.
  for (let i = 0; i < count; i++) {
    const isSeries = rng() < 0.15;
    const title = titles[Math.floor(rng() * titles.length)];
    const location = locations[Math.floor(rng() * locations.length)];
    const source = sources[Math.floor(rng() * sources.length)];
    const startMs = isSeries
      ? now + (7 * 24 * 3600 * 1000) * Math.floor(rng() * 8) // weekly, next 8 weeks
      : now + (24 * 3600 * 1000) * Math.floor(rng() * 90);    // any day, next 90 days
    events.push({
      id: 'evt-' + String(i).padStart(6, '0'),
      title: isSeries ? title + (rng() < 0.5 ? ' (Series)' : '') : title,
      location,
      source,
      start_time: new Date(startMs).toISOString(),
      end_time: new Date(startMs + 2 * 3600 * 1000).toISOString(),
      description: 'Synthetic event ' + i + ' for collapseLongRunningEvents benchmark.',
      category: categories[Math.floor(rng() * categories.length)].name,
      city: 'bloomington',
      url: 'https://example.com/events/' + i,
    });
  }
  // The pipeline keeps events sorted by start_time; match that so first/last
  // ids are stable across runs (as in production).
  events.sort((a, b) => (a.start_time < b.start_time ? -1 : a.start_time > b.start_time ? 1 : 0));
  return events;
}

// --- Benchmark --------------------------------------------------------------
function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function run(events, label) {
  const t0 = performance.now();
  const result = windowObj.collapseLongRunningEvents(events);
  const ms = performance.now() - t0;
  return { ms, result };
}

function main() {
  const argv = process.argv.slice(2);
  const eventsIdx = argv.indexOf('--events');
  let events;
  if (eventsIdx >= 0 && argv[eventsIdx + 1]) {
    events = JSON.parse(fs.readFileSync(path.resolve(argv[eventsIdx + 1]), 'utf8'));
    if (!Array.isArray(events)) throw new Error('--events file must contain a JSON array of events');
  } else {
    events = syntheticEvents(3202); // issue-doc scale: ~3,200 events
  }

  console.log('collapseLongRunningEvents benchmark');
  console.log('events: ' + events.length + (eventsIdx >= 0 ? ' (real data: ' + argv[eventsIdx + 1] + ')' : ' (synthetic)'));
  console.log('');

  // Run #1 — cached emit. Cold cache: computes.
  const run1 = run(events, 'run#1 (cached emit, cold cache)');
  console.log('run#1: ' + run1.ms.toFixed(1) + 'ms');

  // Run #2 — network emit. Same content, but fresh object references (the
  // PushSource pattern re-parses JSON, so identity checks must fail).
  const freshRefs = JSON.parse(JSON.stringify(events));
  if (freshRefs[0] === events[0]) {
    console.error('ERROR: fresh reference array not actually fresh — test is broken');
    process.exit(2);
  }
  const run2 = run(freshRefs, 'run#2 (network emit, fresh refs)');
  console.log('run#2: ' + run2.ms.toFixed(1) + 'ms');

  // Run #3 — repeat to confirm the cache stays warm.
  const run3 = run(JSON.parse(JSON.stringify(events)), 'run#3 (repeat)');
  console.log('run#3: ' + run3.ms.toFixed(1) + 'ms');

  console.log('');
  console.log('window._pipelineLog:');
  windowObj._pipelineLog.forEach(function (line) { console.log('  ' + line); });
  console.log('');

  // --- Assertions -----------------------------------------------------------
  const failures = [];
  const HIT_THRESHOLD_MS = 5; // cache hits take microseconds; 5ms is generous

  const run2Hit = /cache HIT/.test(windowObj._pipelineLog[windowObj._pipelineLog.length - 2] || '');
  if (!run2Hit) {
    failures.push('run#2 was not a cache HIT (expected content-key cache hit on fresh references)');
  }
  if (run2.ms > HIT_THRESHOLD_MS) {
    failures.push('run#2 took ' + run2.ms.toFixed(1) + 'ms (expected < ' + HIT_THRESHOLD_MS + 'ms; regression was 254-336ms)');
  }
  if (!deepEqual(run1.result, run2.result)) {
    failures.push('run#2 results differ from run#1 (cache returned wrong data)');
  }
  if (run3.ms > HIT_THRESHOLD_MS) {
    failures.push('run#3 took ' + run3.ms.toFixed(1) + 'ms (expected cache hit)');
  }
  if (run1.ms < run2.ms) {
    // Cold compute should dominate; a cache hit must be much faster.
    failures.push('run#1 (' + run1.ms.toFixed(1) + 'ms) was not slower than run#2 (' + run2.ms.toFixed(1) + 'ms) — suspicious');
  }

  if (failures.length) {
    console.error('FAIL — regression detected:');
    failures.forEach(function (f) { console.error('  ✗ ' + f); });
    process.exit(1);
  }
  console.log('PASS — content-key cache verified: run#2 hits on fresh references at ' + run2.ms.toFixed(1) + 'ms.');
  process.exit(0);
}

main();
