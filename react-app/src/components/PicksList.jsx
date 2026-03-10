import React, { useState } from 'react';
import { X, CalendarPlus, Download, ExternalLink, Settings2 } from 'lucide-react';
import { usePicks } from '../hooks/usePicks.jsx';
import { formatDayOfWeek, formatMonthDay, formatTime, buildGoogleCalendarUrl, downloadEventICS } from '../lib/helpers.js';
import EnrichmentEditor from './EnrichmentEditor.jsx';

export default function PicksList() {
  const { picks, removePick } = usePicks();
  const [enrichPick, setEnrichPick] = useState(null);

  if (!picks.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg font-medium mb-1">No picks yet</p>
        <p className="text-sm">Bookmark events from the cards to save them here.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-2">
        {picks.map(pick => {
          const event = pick.events;
          if (!event) return null;

          const dateStr = formatDayOfWeek(event.start_time) + ' ' + formatMonthDay(event.start_time);
          const timeStr = formatTime(event.start_time);

          return (
            <div key={pick.id} className="flex items-start gap-3 p-3 rounded-lg bg-white border border-gray-100 hover:border-gray-200 transition-colors group">
              <div className="flex-1 min-w-0">
                {event.url ? (
                  <a href={event.url} target="_blank" rel="noopener noreferrer"
                    className="text-sm font-semibold text-gray-900 hover:underline flex items-center gap-1">
                    {event.title}
                    <ExternalLink size={12} className="text-gray-300 flex-shrink-0" />
                  </a>
                ) : (
                  <p className="text-sm font-semibold text-gray-900">{event.title}</p>
                )}
                <p className="text-xs text-gray-500 mt-0.5">
                  {dateStr}{timeStr ? ` \u00B7 ${timeStr}` : ''}
                  {event.location ? ` \u00B7 ${event.location}` : ''}
                </p>
              </div>

              <div className="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setEnrichPick(pick)}
                  className="text-gray-300 hover:text-gray-500 transition-colors p-1"
                  title="Edit enrichment"
                >
                  <Settings2 size={14} />
                </button>
                <a
                  href={buildGoogleCalendarUrl(event)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-300 hover:text-gray-500 transition-colors p-1"
                  title="Add to Google Calendar"
                >
                  <CalendarPlus size={14} />
                </a>
                <button
                  onClick={() => downloadEventICS(event)}
                  className="text-gray-300 hover:text-gray-500 transition-colors p-1"
                  title="Download .ics"
                >
                  <Download size={14} />
                </button>
                <button
                  onClick={() => removePick(pick.id)}
                  className="text-gray-300 hover:text-red-400 transition-colors p-1"
                  title="Remove pick"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {enrichPick && (
        <EnrichmentEditor
          event={enrichPick.events}
          pick={enrichPick}
          mode="enrich"
          onClose={() => setEnrichPick(null)}
          onSaved={() => setEnrichPick(null)}
        />
      )}
    </div>
  );
}
