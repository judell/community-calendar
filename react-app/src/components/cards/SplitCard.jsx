import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle } from './shared.jsx';

export default function SplitCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden
                        hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">
          <div className="flex">
            {/* Left — image */}
            {event.image_url && (
              <div className="w-2/5 flex-shrink-0">
                <img src={event.image_url} alt="" className="w-full h-full min-h-[160px] object-cover" loading="lazy" />
              </div>
            )}

            {/* Right — content */}
            <div className={`flex-1 p-4 flex flex-col ${event.image_url ? 'w-3/5' : 'w-full'}`}>
              {/* Date */}
              <p className="text-xs text-gray-400 mb-1">
                {dateParts.weekday} {dateParts.month} {dateParts.day}
                {timeStr ? ` \u00B7 ${timeStr}` : ''}
              </p>

              {/* Title */}
              <EventTitle event={event} />

              {/* Meta */}
              {event.location && <p className="text-xs text-gray-500 mt-1 truncate">{event.location}</p>}
              {event.source && <p className="text-xs text-gray-400 italic mt-0.5 truncate">{event.source}</p>}

              <SearchSnippet html={searchSnippetHtml} />
              {snippet && (
                <p className="text-sm text-gray-600 mt-1.5 leading-snug cursor-pointer line-clamp-2" onClick={() => setShowDetail(true)}>
                  {snippet}
                </p>
              )}

              {/* Actions — pushed to bottom */}
              <div className="mt-auto pt-2">
                <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
              </div>
            </div>
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
