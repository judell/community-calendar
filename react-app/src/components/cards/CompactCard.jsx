import React, { useState } from 'react';
import { CalendarPlus, Download, ChevronRight } from 'lucide-react';
import { useEventCardData, SearchSnippet, DetailModal, CategoryIcon } from './shared.jsx';
import { buildGoogleCalendarUrl, downloadEventICS } from '../../lib/helpers.js';

export default function CompactCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-1.5">
        <div
          className="bg-white rounded-lg border border-gray-100 overflow-hidden
                     hover:bg-gray-50 hover:border-gray-200 transition-all duration-150 cursor-pointer"
          onClick={() => (event.description || event.image_url) && setShowDetail(true)}
        >
          <div className="flex items-center gap-3 px-3 py-2.5">
            {/* Category icon */}
            <div className="flex-shrink-0 w-5 flex items-center justify-center" title={event.category || 'Uncategorized'}>
              <CategoryIcon category={event.category} color={colors.label} size={16} className="opacity-60" />
            </div>

            {/* Date column */}
            <div className="flex-shrink-0 w-16 text-center">
              <span className="text-xs font-bold text-gray-800 block leading-none">
                {dateParts.month} {dateParts.day}
              </span>
              <span className="text-[10px] text-gray-400 block mt-0.5">
                {dateParts.weekday}{timeStr ? ` ${timeStr}` : ''}
              </span>
            </div>

            {/* Title + meta */}
            <div className="flex-1 min-w-0">
              {event.url ? (
                <a href={event.url} target="_blank" rel="noopener noreferrer"
                  className="text-sm font-semibold text-gray-900 hover:underline truncate block"
                  onClick={e => e.stopPropagation()}>
                  {event.title}
                </a>
              ) : (
                <span className="text-sm font-semibold text-gray-900 truncate block">{event.title}</span>
              )}
              <span className="text-xs text-gray-400 truncate block">
                {[event.location, event.source].filter(Boolean).join(' \u00B7 ')}
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ opacity: undefined }}>
              <a href={buildGoogleCalendarUrl(event)} target="_blank" rel="noopener noreferrer"
                className="text-gray-300 hover:text-gray-500 transition-colors" title="Add to Google Calendar"
                onClick={e => e.stopPropagation()}>
                <CalendarPlus size={14} />
              </a>
              <button onClick={e => { e.stopPropagation(); downloadEventICS(event); }}
                className="text-gray-300 hover:text-gray-500 transition-colors" title="Download .ics">
                <Download size={14} />
              </button>
            </div>

            {(event.description || event.image_url) && (
              <ChevronRight size={14} className="text-gray-300 flex-shrink-0" />
            )}
          </div>
          <SearchSnippet html={searchSnippetHtml} />
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
