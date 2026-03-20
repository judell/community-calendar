import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle, hideOnImgError } from './shared.jsx';

export default function TicketCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <div className="flex-1 flex bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-all duration-200 border border-gray-200 dark:border-gray-600">

          {/* Stub — date section */}
          <div
            className="flex-shrink-0 w-20 flex flex-col items-center justify-center text-center px-2 py-4 relative"
            style={{ backgroundColor: colors.background, color: colors.label }}
          >
            <span className="text-[10px] font-bold tracking-wider uppercase leading-none">{dateParts.month}</span>
            <span className="text-3xl font-bold leading-tight">{dateParts.day}</span>
            <span className="text-[11px] leading-none opacity-70">{dateParts.weekday}</span>
            {timeStr && <span className="text-[10px] mt-1.5 font-medium opacity-80">{timeStr}</span>}

            {/* Perforated edge */}
            <div className="absolute top-0 bottom-0 right-0 w-px"
              style={{ backgroundImage: `repeating-linear-gradient(to bottom, ${colors.label}30 0px, ${colors.label}30 4px, transparent 4px, transparent 8px)` }}
            />
          </div>

          {/* Main ticket body */}
          <div className="flex-1 p-4 min-w-0">
            {/* Image thumbnail if available */}
            {event.image_url && (
              <img src={event.image_url} alt="" className="w-full h-[120px] object-cover rounded mb-2" loading="lazy" onError={hideOnImgError} />
            )}

            <EventTitle event={event} />

            {event.location && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{event.location}</p>}
            {event.source && <p className="text-xs text-gray-400 italic mt-0.5 truncate">{event.source}</p>}

            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1.5 leading-snug cursor-pointer" onClick={() => setShowDetail(true)}>
                {snippet}
              </p>
            )}

            <div className="mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
              <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
            </div>
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
