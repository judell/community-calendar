import React, { useState, useCallback, useMemo } from 'react';
import CityPicker from './components/CityPicker.jsx';
import FeedView from './components/FeedView.jsx';
import Header from './components/Header.jsx';
import SearchBar from './components/SearchBar.jsx';
import StyleSwitcher from './components/StyleSwitcher.jsx';
import MasonryGrid from './components/MasonryGrid.jsx';
import PicksList from './components/PicksList.jsx';
import { useEvents } from './hooks/useEvents.js';
import { useEnrichments } from './hooks/useEnrichments.js';
import { useProcessedEvents } from './hooks/useProcessedEvents.js';
import { useInfiniteScroll } from './hooks/useInfiniteScroll.js';
import { useColumnCount } from './hooks/useColumnCount.js';
import { useAuth } from './hooks/useAuth.jsx';
import { getActiveCategories } from './lib/helpers.js';

function App() {
  const { feed, city } = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return { feed: params.get('feed') || null, city: params.get('city') || null };
  }, []);

  const { user } = useAuth();
  const [filterTerm, setFilterTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [displayCount, setDisplayCount] = useState(50);
  const [cardStyle, setCardStyle] = useState('accent');
  const [viewMode, setViewMode] = useState('cards');

  const { events, loading } = useEvents(city);
  const enrichments = useEnrichments(city);
  const rawColumnCount = useColumnCount();
  const oneColStyles = ['list'];
  const twoColStyles = ['compact', 'split', 'splitimage'];
  const columnCount = oneColStyles.includes(cardStyle) ? 1
    : twoColStyles.includes(cardStyle) ? Math.min(rawColumnCount, 2)
    : rawColumnCount;

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

  if (feed) {
    return <FeedView feedId={feed} />;
  }

  if (!city) {
    return <CityPicker />;
  }

  return (
    <div className="flex justify-center w-full overflow-x-hidden bg-gray-50 min-h-screen">
      <div className="max-w-[1400px] w-full px-4 py-6">
        <Header city={city} events={processedEvents} />

        {/* View mode tabs — only show picks tab when signed in */}
        <div className="flex gap-1 mb-4">
          <button
            onClick={() => setViewMode('cards')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'cards' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
          >
            Cards
          </button>
          {user && (
            <button
              onClick={() => setViewMode('picks')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'picks' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              My Picks
            </button>
          )}
        </div>

        {viewMode === 'cards' && (
          <>
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
          </>
        )}

        {viewMode === 'picks' && <PicksList />}
      </div>
    </div>
  );
}

export default App;
