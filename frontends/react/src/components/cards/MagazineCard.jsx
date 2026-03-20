import React, { useState } from 'react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, hideOnImgError } from './shared.jsx';

export default function MagazineCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <div className="flex-1 rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600">

          {/* Hero area — image with overlay, or colored block */}
          {event.image_url ? (
            <div className="relative h-[200px]">
              <img src={event.image_url} alt="" className="w-full h-full object-cover" loading="lazy" onError={hideOnImgError} />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
              {/* Date badge overlaid on image */}
              <div className="absolute top-3 left-3 bg-white dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-2 py-1 text-center shadow-sm">
                <span className="block text-[10px] font-bold text-gray-600 dark:text-gray-400 leading-none">{dateParts.month}</span>
                <span className="block text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">{dateParts.day}</span>
              </div>
              {/* Category pill on image */}
              {event.category && (
                <span
                  className="absolute top-3 right-3 rounded-full px-2.5 py-0.5 text-[11px] font-medium shadow-sm cursor-pointer"
                  style={{ color: colors.label, backgroundColor: `${colors.background}e6` }}
                  onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
                >
                  {event.category}
                </span>
              )}
              {/* Title on image */}
              <div className="absolute bottom-0 left-0 right-0 p-4">
                {event.url ? (
                  <a href={event.url} target="_blank" rel="noopener noreferrer"
                    className="text-lg font-bold text-white leading-snug hover:underline block drop-shadow-md">
                    {event.title}
                  </a>
                ) : (
                  <h5 className="text-lg font-bold text-white leading-snug drop-shadow-md">{event.title}</h5>
                )}
                {timeStr && <p className="text-sm text-white/80 mt-0.5">{timeStr}</p>}
              </div>
            </div>
          ) : (
            /* No image — colored header block */
            <div className="relative px-4 pt-4 pb-3"
              style={{ background: `linear-gradient(135deg, ${colors.background}, ${colors.label}12)` }}>
              <div className="flex items-start gap-3">
                <div className="bg-white dark:bg-gray-800/80 rounded-lg px-2 py-1 text-center shadow-sm flex-shrink-0">
                  <span className="block text-[10px] font-bold text-gray-600 dark:text-gray-400 leading-none">{dateParts.month}</span>
                  <span className="block text-lg font-bold text-gray-900 dark:text-gray-100 leading-tight">{dateParts.day}</span>
                </div>
                <div className="flex-1 min-w-0">
                  {event.url ? (
                    <a href={event.url} target="_blank" rel="noopener noreferrer"
                      className="text-base font-bold tracking-tight text-gray-900 dark:text-gray-100 hover:underline block leading-snug">
                      {event.title}
                    </a>
                  ) : (
                    <h5 className="text-base font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-snug">{event.title}</h5>
                  )}
                  {timeStr && <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{timeStr}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Body */}
          <div className="px-4 py-3">
            {event.location && <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{event.location}</p>}
            {event.source && <p className="text-xs text-gray-400 italic truncate">{event.source}</p>}
            <SearchSnippet html={searchSnippetHtml} />
            {snippet && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1.5 cursor-pointer leading-snug" onClick={() => setShowDetail(true)}>{snippet}</p>
            )}
            <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
              <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
            </div>
          </div>
        </div>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
