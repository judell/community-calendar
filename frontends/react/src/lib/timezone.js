/**
 * Timezone-aware display utilities.
 *
 * After the timezone migration, event times are stored as real UTC in timestamptz
 * columns, with a `timezone` text field containing the IANA timezone.
 */

/**
 * Format a time string in a specific timezone.
 * Returns empty string for midnight (all-day events).
 */
export function formatTimeInZone(isoString, timezone) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const parts = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: timezone,
  }).formatToParts(d);

  const hour = parts.find(p => p.type === 'hour')?.value;
  const minute = parts.find(p => p.type === 'minute')?.value;
  const dayPeriod = parts.find(p => p.type === 'dayPeriod')?.value;

  if (hour === '12' && minute === '00' && dayPeriod?.toUpperCase() === 'AM') return '';
  return `${hour}:${minute} ${dayPeriod?.toUpperCase() || ''}`.trim();
}

/**
 * Format date parts (month, day, weekday) in a specific timezone.
 */
export function formatDateInZone(isoString, timezone) {
  if (!isoString) return { month: '', day: '', weekday: '' };
  const d = new Date(isoString);
  return {
    month: d.toLocaleDateString('en-US', { month: 'short', timeZone: timezone }).toUpperCase(),
    day: d.toLocaleDateString('en-US', { day: 'numeric', timeZone: timezone }),
    weekday: d.toLocaleDateString('en-US', { weekday: 'short', timeZone: timezone }),
  };
}

/**
 * Format day of week in a specific timezone.
 */
export function formatDayOfWeekInZone(isoString, timezone) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { weekday: 'short', timeZone: timezone });
}

/**
 * Format month + day in a specific timezone.
 */
export function formatMonthDayInZone(isoString, timezone) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: timezone });
}

/**
 * Determine the display timezone for an event.
 * - City views: use the event's stored timezone (or the city's timezone)
 * - publisher-resources: use the viewer's browser timezone
 */
export function getDisplayTimezone(event, citySlug) {
  if (citySlug === 'publisher-resources') {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  }
  return event?.timezone || 'America/Los_Angeles';
}

/**
 * Get a short timezone abbreviation for display (e.g., "PDT", "EST").
 */
export function getTimezoneAbbr(isoString, timezone) {
  if (!isoString || !timezone) return '';
  const d = new Date(isoString);
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'short',
    timeZone: timezone,
  }).formatToParts(d);
  return parts.find(p => p.type === 'timeZoneName')?.value || '';
}
