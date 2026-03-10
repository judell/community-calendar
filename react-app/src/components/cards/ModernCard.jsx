import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle } from './shared.jsx';

export default function ModernCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-4">
        <div
          className="rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-gray-100"
          style={{ backgroundColor: `${colors.background}60` }}
        >
          {/* Image with inset rounded corners */}
          {event.image_url && (
            <div className="p-3 pb-0">
              <img src={event.image_url} alt="" className="w-full h-[170px] object-cover rounded-xl" loading="lazy" />
            </div>
          )}

          <div className="p-4">
            {/* Category + date row */}
            <div className="flex items-center gap-2 mb-2">
              {event.category && (
                <span
                  className="text-[11px] font-semibold uppercase tracking-wider cursor-pointer"
                  style={{ color: colors.label }}
                  onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
                >
                  {event.category}
                </span>
              )}
              <span className="text-[11px] text-gray-400">
                {event.category ? '\u00B7 ' : ''}{dateParts.weekday} {dateParts.month} {dateParts.day}
                {timeStr ? ` \u00B7 ${timeStr}` : ''}
              </span>
            </div>

            {/* Title */}
            <EventTitle event={event} className="text-lg font-bold tracking-tight text-gray-900 leading-snug" />

            {/* Meta */}
            {event.location && (
              <p className="text-sm text-gray-500 mt-1.5">{event.location}</p>
            )}
            {event.source && (
              <p className="text-xs text-gray-400 mt-1 italic">{event.source}</p>
            )}

            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 mt-2.5 leading-relaxed cursor-pointer" onClick={() => setShowDetail(true)}>
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
