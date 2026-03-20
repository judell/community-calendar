import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle, CategoryIcon, hideOnImgError } from './shared.jsx';

export default function AlwaysImageCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-4">
        <div
          className="flex-1 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 dark:border-gray-700"
          style={{ backgroundColor: `${colors.background}60` }}
        >
          {/* Image or category icon placeholder — inset with rounded corners like Modern */}
          <div className="p-3 pb-0">
            {event.image_url ? (
              <img src={event.image_url} alt="" className="w-full h-[170px] object-cover rounded-xl" loading="lazy" onError={hideOnImgError} />
            ) : (
              <div
                className="w-full h-[120px] flex items-center justify-center rounded-xl"
                style={{ background: `linear-gradient(135deg, ${colors.background}, ${colors.label}20)` }}
              >
                <CategoryIcon category={event.category} color={colors.label} />
              </div>
            )}
          </div>

          <div className="p-4">
            {/* Date row */}
            <div className="mb-2">
              <span className="text-[11px] text-gray-400">
                {dateParts.weekday} {dateParts.month} {dateParts.day}
                {timeStr ? ` \u00B7 ${timeStr}` : ''}
              </span>
            </div>

            {/* Title */}
            <EventTitle event={event} className="text-lg font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-snug" />

            {/* Meta */}
            {event.location && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1.5">{event.location}</p>
            )}
            {event.source && (
              <p className="text-xs text-gray-400 mt-1 italic">{event.source}</p>
            )}

            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2.5 leading-relaxed cursor-pointer" onClick={() => setShowDetail(true)}>
                {snippet}
              </p>
            )}

            {/* Actions */}
            <div className="mt-3 pt-3 border-t" style={{ borderColor: `${colors.label}18` }}>
              <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
            </div>
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
