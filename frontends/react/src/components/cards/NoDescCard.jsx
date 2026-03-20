import React, { useState } from 'react';
import { useEventCardData, ActionBar, DetailModal, EventTitle, hideOnImgError } from './shared.jsx';

export default function NoDescCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div data-grid-card className="h-full mb-3 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-600 overflow-hidden hover:shadow-lg transition-all duration-200">
        {/* Image area */}
        <div className="h-[140px] flex-shrink-0 overflow-hidden bg-gray-100 dark:bg-gray-700">
          {event.image_url ? (
            <img src={event.image_url} alt="" className="w-full h-full object-cover" loading="lazy" onError={hideOnImgError} />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ backgroundColor: colors.background, color: colors.label }}>
                <span className="text-lg font-bold">{dateParts.day}</span>
              </div>
            </div>
          )}
        </div>

        {/* Content area — fills remaining space in grid */}
        <div className="flex-1 min-h-0 flex flex-col justify-start p-3">
          <div className="flex-1 min-h-0 overflow-hidden">
            <EventTitle event={event} className="text-sm font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-snug line-clamp-2" />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {dateParts.weekday} {dateParts.month} {dateParts.day}{timeStr ? ` · ${timeStr}` : ''}
            </p>
            {event.location && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{event.location}</p>
            )}
          </div>
          <div className="flex-shrink-0 mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
            <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
