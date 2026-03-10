import React from 'react';
import EventCard from './EventCard.jsx';

export default function MasonryGrid({ masonryColumns, filterTerm, onCategoryFilter, variant }) {
  if (!masonryColumns || !masonryColumns.length) return null;

  return (
    <div className={`flex items-start w-full ${variant === 'minimal' ? 'gap-8' : 'gap-4'}`}>
      {masonryColumns.map((column, colIdx) => (
        <div key={colIdx} className="flex-1 min-w-0 flex flex-col">
          {column.map(event => (
            <EventCard
              key={event.id}
              event={event}
              filterTerm={filterTerm}
              onCategoryFilter={onCategoryFilter}
              variant={variant}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
