import React, { useState, useMemo } from 'react';
import { useCollection } from '../hooks/useCollection.js';
import { useColumnCount } from '../hooks/useColumnCount.js';
import { getMasonryColumns } from '../lib/helpers.js';
import MasonryGrid from './MasonryGrid.jsx';
import StyleSwitcher from './StyleSwitcher.jsx';

export default function FeedView({ feedId }) {
  const { collection, events, loading } = useCollection(feedId);
  const rawColumnCount = useColumnCount();

  const [styleOverride, setStyleOverride] = useState(null);
  const cardStyle = styleOverride || collection?.card_style || 'accent';

  const oneColStyles = ['list'];
  const twoColStyles = ['compact', 'split', 'splitimage'];
  const columnCount = oneColStyles.includes(cardStyle) ? 1
    : twoColStyles.includes(cardStyle) ? Math.min(rawColumnCount, 2)
    : rawColumnCount;

  const masonryColumns = useMemo(
    () => getMasonryColumns(events, columnCount),
    [events, columnCount]
  );

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="flex justify-center w-full min-h-screen bg-gray-50">
        <div className="max-w-[1400px] w-full px-4 py-12 text-center">
          <p className="text-lg text-gray-500">Collection not found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-center w-full overflow-x-hidden bg-gray-50 min-h-screen">
      <div className="max-w-[1400px] w-full px-4 py-6">
        {/* Collection header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{collection.name}</h1>
          {collection.description && (
            <p className="text-gray-500 mt-1">{collection.description}</p>
          )}
          <p className="text-xs text-gray-400 mt-1">
            {events.length} event{events.length !== 1 ? 's' : ''}
          </p>
        </div>

        <StyleSwitcher value={cardStyle} onChange={setStyleOverride} />

        {events.length === 0 ? (
          <p className="text-center text-gray-400 py-12">This collection has no events yet.</p>
        ) : (
          <MasonryGrid
            masonryColumns={masonryColumns}
            filterTerm=""
            onCategoryFilter={() => {}}
            variant={cardStyle}
          />
        )}
      </div>
    </div>
  );
}
