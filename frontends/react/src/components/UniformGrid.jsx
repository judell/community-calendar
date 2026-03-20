import React from 'react';
import { parseCardStyle } from '../lib/cardStyles.js';
import EventCard from './EventCard.jsx';

export default function UniformGrid({ events, filterTerm, onCategoryFilter, variant, columnCount }) {
  if (!events || !events.length) return null;

  const { layout } = parseCardStyle(variant);
  const needsWrapper = layout === 'grid';

  return (
    <div
      className="grid w-full gap-4 items-stretch"
      style={{ gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))` }}
    >
      {events.map(event => (
        needsWrapper ? (
          <div key={event.id} className="h-full min-h-0 flex flex-col overflow-hidden rounded-lg [&>*]:!mb-0 [&>*:first-child]:flex-1 [&>*:first-child]:min-h-0 [&>*:first-child]:flex [&>*:first-child]:flex-col [&_[data-grid-card]]:flex-1 [&_[data-grid-card]]:min-h-0 [&_[data-grid-card]]:flex [&_[data-grid-card]]:flex-col [&_[data-grid-card]]:h-full [&_[data-testid='flowbite-card']]:grow [&_[data-testid='flowbite-card']>*]:flex [&_[data-testid='flowbite-card']>*]:flex-col [&_[data-testid='flowbite-card']>*]:justify-start">
            <EventCard
              event={event}
              filterTerm={filterTerm}
              onCategoryFilter={onCategoryFilter}
              variant={variant}
            />
          </div>
        ) : (
          <EventCard
            key={event.id}
            event={event}
            filterTerm={filterTerm}
            onCategoryFilter={onCategoryFilter}
            variant={variant}
          />
        )
      ))}
    </div>
  );
}
