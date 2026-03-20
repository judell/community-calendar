import React, { useMemo } from 'react';
import { formatDayOfWeek, formatMonthDay } from '../lib/helpers.js';
import { getDisplayTimezone } from '../lib/timezone.js';

/**
 * A minimal by-date list view: date headings followed by linked event titles.
 */
export default function DateListView({ events, city }) {
  const grouped = useMemo(() => {
    const groups = [];
    let currentDate = null;
    let currentEvents = [];

    for (const event of events) {
      const tz = getDisplayTimezone(event, city);
      const dateKey = formatDayOfWeek(event.start_time, tz) + ' ' + formatMonthDay(event.start_time, tz);

      if (dateKey !== currentDate) {
        if (currentDate !== null) {
          groups.push({ date: currentDate, events: currentEvents });
        }
        currentDate = dateKey;
        currentEvents = [event];
      } else {
        currentEvents.push(event);
      }
    }
    if (currentDate !== null) {
      groups.push({ date: currentDate, events: currentEvents });
    }

    return groups;
  }, [events, city]);

  if (events.length === 0) {
    return <p className="text-center text-gray-400 py-12">No events to display.</p>;
  }

  return (
    <div className="max-w-[600px] mx-auto">
      {grouped.map(group => (
        <div key={group.date} className="mb-6">
          <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">{group.date}</h3>
          {group.events.map(event => (
            <p key={event.id || event.source_uid} className="text-sm text-gray-700 dark:text-gray-300 mb-1">
              {event.url ? (
                <a href={event.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                  {event.title}
                </a>
              ) : (
                event.title
              )}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}
