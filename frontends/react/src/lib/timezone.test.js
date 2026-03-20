import { formatTimeInZone, formatDateInZone, getDisplayTimezone } from './timezone.js';

// A Portland event: 7pm PDT = 2026-03-18T02:00:00Z stored as timestamptz
const portlandEvent = {
  start_time: '2026-03-18T02:00:00+00:00',
  timezone: 'America/Los_Angeles',
  city: 'portland',
};

// A Boston event: 7pm EDT = 2026-03-17T23:00:00Z
const bostonEvent = {
  start_time: '2026-03-17T23:00:00+00:00',
  timezone: 'America/New_York',
  city: 'boston',
};

test('formatTimeInZone shows local time for event timezone', () => {
  expect(formatTimeInZone(portlandEvent.start_time, 'America/Los_Angeles')).toBe('7:00 PM');
  expect(formatTimeInZone(bostonEvent.start_time, 'America/New_York')).toBe('7:00 PM');
});

test('formatTimeInZone converts across timezones', () => {
  // Boston 7pm EDT viewed from Portland (PDT) = 4pm
  expect(formatTimeInZone(bostonEvent.start_time, 'America/Los_Angeles')).toBe('4:00 PM');
});

test('formatTimeInZone returns empty string for midnight', () => {
  const midnightEvent = { start_time: '2026-03-17T07:00:00+00:00' }; // midnight PDT
  expect(formatTimeInZone(midnightEvent.start_time, 'America/Los_Angeles')).toBe('');
});

test('formatDateInZone shows correct date in timezone', () => {
  // This event is March 18 in UTC but March 17 in LA
  const result = formatDateInZone(portlandEvent.start_time, 'America/Los_Angeles');
  expect(result.day).toBe('17');
  expect(result.weekday).toBe('Tue');
});

test('getDisplayTimezone returns event timezone for city views', () => {
  expect(getDisplayTimezone(portlandEvent, 'city')).toBe('America/Los_Angeles');
});

test('getDisplayTimezone returns browser timezone for publisher-resources', () => {
  const pubEvent = { ...portlandEvent, city: 'publisher-resources' };
  const result = getDisplayTimezone(pubEvent, 'publisher-resources');
  expect(result).toBeTruthy();
});
