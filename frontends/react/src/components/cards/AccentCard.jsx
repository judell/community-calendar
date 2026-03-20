import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle, hideOnImgError } from './shared.jsx';

export default function AccentCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <div
          className="grow bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-600 overflow-hidden hover:shadow-lg transition-all duration-200"
          style={{ borderLeftWidth: '3px', borderLeftColor: colors.label }}
        >
          {event.image_url ? (
            <div className="relative">
              <img src={event.image_url} alt="" className="w-full h-[180px] object-cover" loading="lazy" onError={hideOnImgError} />
              <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-white dark:from-gray-800 to-transparent" />
            </div>
          ) : (
            <div className="h-2 w-full" style={{ background: `linear-gradient(135deg, ${colors.label}30, ${colors.background})` }} />
          )}

          <div className="p-4 pt-3">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-12 h-14 rounded-lg flex flex-col items-center justify-center text-center"
                style={{ backgroundColor: colors.background, color: colors.label }}>
                <span className="text-[10px] font-semibold leading-none tracking-wide">{dateParts.month}</span>
                <span className="text-xl font-bold leading-tight">{dateParts.day}</span>
                <span className="text-[10px] leading-none opacity-70">{dateParts.weekday}</span>
              </div>
              <div className="flex-1 min-w-0">
                <EventTitle event={event} />
                {timeStr && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{timeStr}</p>}
                {event.location && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{event.location}</p>}
                {event.source && <p className="text-xs text-gray-400 italic mt-0.5 truncate">{event.source}</p>}
              </div>
            </div>
            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 cursor-pointer leading-snug" onClick={() => setShowDetail(true)}>{snippet}</p>
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
