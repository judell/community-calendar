import React, { useState } from 'react';
import { Card } from 'flowbite-react';
import { useEventCardData, ActionBar, SearchSnippet, DetailModal, EventTitle, hideOnImgError } from './shared.jsx';

export default function ClassicCard({ event, filterTerm, onCategoryFilter }) {
  const [showDetail, setShowDetail] = useState(false);
  const { dateStr, timeStr, snippet, searchSnippetHtml, colors } = useEventCardData(event, filterTerm);

  return (
    <>
      <div className="mb-3">
        <Card
          className="max-w-sm"
          renderImage={event.image_url ? () => (
            <img src={event.image_url} alt="" className="w-full h-[180px] object-cover rounded-t-lg" loading="lazy" onError={hideOnImgError} />
          ) : undefined}
        >
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {dateStr}{timeStr ? `, ${timeStr}` : ''}
          </p>
          <EventTitle event={event} />
          {event.location && <p className="font-normal text-sm text-gray-500 dark:text-gray-400">{event.location}</p>}
          {event.source && <p className="text-sm text-gray-400 italic">{event.source}</p>}
          <SearchSnippet html={searchSnippetHtml} />
          {snippet && (
            <p className="font-normal text-sm text-gray-700 dark:text-gray-300 cursor-pointer" onClick={() => setShowDetail(true)}>
              {snippet}
            </p>
          )}
          <div className="pt-1">
            <ActionBar event={event} onCategoryFilter={onCategoryFilter} onShowDetail={() => setShowDetail(true)} colors={colors} />
          </div>
        </Card>
      </div>
      {showDetail && <DetailModal event={event} dateStr={dateStr} timeStr={timeStr} onClose={() => setShowDetail(false)} />}
    </>
  );
}
