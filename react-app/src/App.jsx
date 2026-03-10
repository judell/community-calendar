import React, { useState, useCallback, useMemo } from 'react';
import CityPicker from './components/CityPicker.jsx';
import Header from './components/Header.jsx';
import SearchBar from './components/SearchBar.jsx';
import StyleSwitcher from './components/StyleSwitcher.jsx';
import MasonryGrid from './components/MasonryGrid.jsx';
import { useEvents } from './hooks/useEvents.js';
import { useEnrichments } from './hooks/useEnrichments.js';
import { useProcessedEvents } from './hooks/useProcessedEvents.js';
import { useInfiniteScroll } from './hooks/useInfiniteScroll.js';
import { useColumnCount } from './hooks/useColumnCount.js';
import { getActiveCategories } from './lib/helpers.js';

function App() {
  // Read city from URL params
  const city = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('city') || null;
  }, []);

  const [filterTerm, setFilterTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [displayCount, setDisplayCount] = useState(50);
  const [cardStyle, setCardStyle] = useState('accent');

  const { events, loading } = useEvents(city);
  const enrichments = useEnrichments(city);
  const rawColumnCount = useColumnCount();
  const twoColStyles = ['compact', 'split', 'splitimage'];
  const columnCount = twoColStyles.includes(cardStyle) ? Math.min(rawColumnCount, 2) : rawColumnCount;

  const { processedEvents, cardEvents, hasMore, masonryColumns } = useProcessedEvents(
    events,
    enrichments,
    filterTerm,
    displayCount,
    categoryFilter,
    columnCount
  );

  const activeCategories = useMemo(
    () => getActiveCategories(processedEvents),
    [processedEvents]
  );

  const handleLoadMore = useCallback(() => {
    setDisplayCount(prev => prev + 50);
  }, []);

  const sentinelRef = useInfiniteScroll(hasMore && !filterTerm, handleLoadMore);

  const handleCategoryFilter = useCallback((cat) => {
    setCategoryFilter(cat);
    setDisplayCount(50);
  }, []);

  const handleClearAll = useCallback(() => {
    setFilterTerm('');
    setCategoryFilter('');
  }, []);

  // Update page title
  useMemo(() => {
    if (city) {
      const CITY_NAMES = {
        santarosa: 'Santa Rosa', davis: 'Davis', bloomington: 'Bloomington',
        petaluma: 'Petaluma', toronto: 'Toronto', raleighdurham: 'Raleigh-Durham',
        montclair: 'Montclair', roanoke: 'Roanoke', matsu: 'MatSu',
      };
      document.title = (CITY_NAMES[city] || city) + ' Community Calendar';
    }
  }, [city]);

  if (!city) {
    return <CityPicker />;
  }

  return (
    <div className="flex justify-center w-full overflow-x-hidden bg-gray-50 min-h-screen">
      <div className="max-w-[1400px] w-full px-4 py-6">
        <Header city={city} />
        <SearchBar
          filterTerm={filterTerm}
          onFilterTermChange={(val) => { setFilterTerm(val); setDisplayCount(50); }}
          categoryFilter={categoryFilter}
          onCategoryFilterChange={handleCategoryFilter}
          activeCategories={activeCategories}
          onClearAll={handleClearAll}
        />
        <StyleSwitcher value={cardStyle} onChange={setCardStyle} />

        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
          </div>
        )}

        {!loading && events && (
          <>
            <MasonryGrid
              masonryColumns={masonryColumns}
              filterTerm={filterTerm}
              onCategoryFilter={handleCategoryFilter}
              variant={cardStyle}
            />

            {hasMore && !filterTerm && (
              <div ref={sentinelRef} className="w-full text-center py-4 text-gray-400 text-sm">
                Loading more...
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default App;
