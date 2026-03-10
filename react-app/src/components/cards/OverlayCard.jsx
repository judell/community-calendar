import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle } from './shared.jsx';

export default function OverlayCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <div className="rounded-lg overflow-hidden shadow-sm border border-gray-200 bg-white
                        hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">

          {event.image_url ? (
            /* Image with date chip + category overlaid */
            <div className="relative">
              <img src={event.image_url} alt="" className="w-full h-[180px] object-cover" loading="lazy" />
              {/* Date chip — top left */}
              <div
                className="absolute top-3 left-3 w-12 h-14 rounded-lg flex flex-col items-center justify-center text-center shadow-md"
                style={{ backgroundColor: `${colors.background}ee`, color: colors.label }}
              >
                <span className="text-[10px] font-semibold leading-none tracking-wide">{dateParts.month}</span>
                <span className="text-xl font-bold leading-tight">{dateParts.day}</span>
                <span className="text-[10px] leading-none opacity-70">{dateParts.weekday}</span>
              </div>
              {/* Category pill — top right */}
              {event.category && (
                <span
                  className="absolute top-3 right-3 rounded-full px-2.5 py-0.5 text-[11px] font-medium shadow-sm cursor-pointer"
                  style={{ color: colors.label, backgroundColor: `${colors.background}ee` }}
                  onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
                >
                  {event.category}
                </span>
              )}

            </div>
          ) : (
            /* No image — colored band with date chip + category inline */
            <div
              className="relative px-4 py-3"
              style={{ background: `linear-gradient(135deg, ${colors.background}, ${colors.label}15)` }}
            >
              <div
                className="flex-shrink-0 w-12 h-14 rounded-lg flex flex-col items-center justify-center text-center shadow-sm"
                style={{ backgroundColor: 'rgba(255,255,255,0.85)', color: colors.label }}
              >
                <span className="text-[10px] font-semibold leading-none tracking-wide">{dateParts.month}</span>
                <span className="text-xl font-bold leading-tight">{dateParts.day}</span>
                <span className="text-[10px] leading-none opacity-70">{dateParts.weekday}</span>
              </div>
              {event.category && (
                <span
                  className="absolute top-3 right-3 rounded-full px-2.5 py-0.5 text-[11px] font-medium cursor-pointer shadow-sm"
                  style={{ color: colors.label, backgroundColor: 'rgba(255,255,255,0.7)' }}
                  onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
                >
                  {event.category}
                </span>
              )}
            </div>
          )}

          {/* Body — title + meta always below the image/band */}
          <div className="p-4 pt-3">
            <EventTitle event={event} />
            {timeStr && <p className="text-xs text-gray-500 mt-0.5">{timeStr}</p>}
            {event.location && <p className="text-xs text-gray-500 mt-0.5 truncate">{event.location}</p>}
            {event.source && <p className="text-xs text-gray-400 italic mt-0.5 truncate">{event.source}</p>}

            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 mt-2 cursor-pointer leading-snug" onClick={() => setShowDetail(true)}>{snippet}</p>
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
