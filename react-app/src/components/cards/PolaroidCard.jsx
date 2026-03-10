import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle, CategoryIcon } from './shared.jsx';

export default function PolaroidCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-4">
        <div className="bg-white rounded-sm shadow-md hover:shadow-xl hover:-rotate-0 transition-all duration-300
                        p-3 pb-4"
             style={{ transform: 'rotate(-0.5deg)' }}>
          {/* Photo area with white border (polaroid frame) */}
          <div className="border border-gray-100">
            {event.image_url ? (
              <img src={event.image_url} alt="" className="w-full h-[200px] object-cover" loading="lazy" />
            ) : (
              <div
                className="w-full h-[140px] flex items-center justify-center"
                style={{ background: `linear-gradient(135deg, ${colors.background}, ${colors.label}15)` }}
              >
                <CategoryIcon category={event.category} color={colors.label} size={48} />
              </div>
            )}
          </div>

          {/* Caption area — like writing below a polaroid */}
          <div className="mt-3 px-1">
            <EventTitle event={event} className="text-base font-bold text-gray-900 leading-snug" />

            <p className="text-xs text-gray-400 mt-1" style={{ fontFamily: 'Georgia, serif', fontStyle: 'italic' }}>
              {dateParts.weekday} {dateParts.month} {dateParts.day}
              {timeStr ? ` \u2014 ${timeStr}` : ''}
            </p>

            {event.location && (
              <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: 'Georgia, serif' }}>{event.location}</p>
            )}
            {event.source && (
              <p className="text-xs text-gray-400 italic mt-0.5">{event.source}</p>
            )}

            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 mt-2 leading-snug cursor-pointer" onClick={() => setShowDetail(true)}>
                {snippet}
              </p>
            )}

            <div className="mt-3 pt-2 border-t border-gray-100">
              <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
            </div>
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
