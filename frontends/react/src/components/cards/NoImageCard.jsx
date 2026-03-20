import React, { useState } from 'react';
import { useEventCardData, ActionBar, DetailModal, EventTitle } from './shared.jsx';

export default function NoImageCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div data-grid-card className="h-full mb-3 flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-600 overflow-hidden hover:shadow-lg transition-all duration-200">
        <div className="flex-1 min-h-0 flex flex-col justify-start p-3">
          <div className="flex gap-2.5 flex-1 min-h-0">
            {/* Date badge */}
            <div className="flex-shrink-0 w-11 h-12 rounded-lg flex flex-col items-center justify-center text-center"
              style={{ backgroundColor: colors.background, color: colors.label }}>
              <span className="text-[9px] font-semibold leading-none tracking-wide">{dateParts.month}</span>
              <span className="text-lg font-bold leading-tight">{dateParts.day}</span>
            </div>

            {/* Text content */}
            <div className="flex-1 min-w-0">
              <EventTitle event={event} className="text-sm font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-snug line-clamp-2" />
              {timeStr && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{timeStr}</p>}
              {event.location && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{event.location}</p>}
              {snippet && <p className="text-xs text-gray-400 mt-1">{snippet}</p>}
            </div>
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
