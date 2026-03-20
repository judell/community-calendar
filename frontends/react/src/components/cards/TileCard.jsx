import React, { useState } from 'react';
import { useEventCardData, DetailModal, EventTitle, hideOnImgError, CategoryIcon } from './shared.jsx';
import { CalendarPlus, Info } from 'lucide-react';
import { buildGoogleCalendarUrl } from '../../lib/helpers.js';

export default function TileCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div
        data-grid-card
        className="h-full mb-3 relative rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-all duration-200 cursor-pointer group min-h-[200px]"
        onClick={() => setShowDetail(true)}
      >
        {/* Background */}
        {event.image_url ? (
          <img src={event.image_url} alt="" className="w-full object-cover min-h-[200px]" loading="lazy" onError={hideOnImgError} />
        ) : (
          <div className="min-h-[200px]" style={{ background: `linear-gradient(135deg, ${colors.label}20, ${colors.background})` }}>
            <div className="absolute inset-0 flex items-center justify-center">
              <CategoryIcon category={event.category} color={colors.label} size={64} className="opacity-20" />
            </div>
          </div>
        )}

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

        {/* Date badge top-left */}
        <div className="absolute top-2 left-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-2 py-1 text-center">
          <span className="text-[9px] font-semibold text-gray-500 block leading-none">{dateParts.month}</span>
          <span className="text-base font-bold text-gray-900 dark:text-gray-100 leading-tight">{dateParts.day}</span>
        </div>

        {/* Action buttons top-right (show on hover) */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
          <a
            href={buildGoogleCalendarUrl(event)}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="bg-white/90 backdrop-blur-sm rounded-full p-1.5 text-gray-600 hover:text-gray-900 transition-colors"
            title="Add to Google Calendar"
          >
            <CalendarPlus size={14} />
          </a>
          <button
            onClick={e => { e.stopPropagation(); setShowDetail(true); }}
            className="bg-white/90 backdrop-blur-sm rounded-full p-1.5 text-gray-600 hover:text-gray-900 transition-colors"
            title="View details"
          >
            <Info size={14} />
          </button>
        </div>

        {/* Bottom text */}
        <div className="absolute bottom-0 inset-x-0 p-3">
          {event.category && (
            <span
              className="inline-block rounded-full px-2 py-0.5 text-[10px] font-medium mb-1.5 cursor-pointer"
              style={{ color: '#fff', backgroundColor: colors.label + 'cc' }}
              onClick={e => { e.stopPropagation(); onCategoryFilter && onCategoryFilter(event.category); }}
            >
              {event.category}
            </span>
          )}
          <h5 className="text-sm font-bold text-white leading-snug line-clamp-2">{event.title}</h5>
          {timeStr && <p className="text-xs text-white/70 mt-0.5">{timeStr}</p>}
          {event.location && <p className="text-xs text-white/60 mt-0.5 truncate">{event.location}</p>}
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
