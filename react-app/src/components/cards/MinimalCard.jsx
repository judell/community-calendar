import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle } from './shared.jsx';

export default function MinimalCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-6 px-1">
        {/* Image — full bleed, no card chrome */}
        {event.image_url && (
          <img src={event.image_url} alt="" className="w-full h-[180px] object-cover rounded mb-3" loading="lazy" />
        )}

        {/* Category as colored uppercase label */}
        {event.category && (
          <span
            className="text-[10px] font-semibold uppercase tracking-widest cursor-pointer"
            style={{ color: colors.label }}
            onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
          >
            {event.category}
          </span>
        )}

        {/* Title — large, bold */}
        <EventTitle event={event} className="text-lg font-bold tracking-tight text-gray-900 leading-snug mt-1" />

        {/* Date + time */}
        <p className="text-xs text-gray-400 mt-1">
          {dateParts.weekday} {dateParts.month} {dateParts.day}
          {timeStr ? ` \u00B7 ${timeStr}` : ''}
        </p>

        {/* Location + source */}
        {event.location && <p className="text-sm text-gray-500 mt-1">{event.location}</p>}
        {event.source && <p className="text-xs text-gray-400 italic mt-0.5">{event.source}</p>}

        <SearchSnippet html={searchSnippetHtml} />
        {snippet && (
          <p className="text-sm text-gray-500 mt-2 leading-relaxed cursor-pointer" onClick={() => setShowDetail(true)}>
            {snippet}
          </p>
        )}

        {/* Actions — very subtle */}
        <div className="mt-3">
          <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
        </div>

        {/* Separator line */}
        <div className="mt-5 border-b border-gray-200" />
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
