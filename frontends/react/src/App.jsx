import React, { useState, useCallback, useMemo, useSyncExternalStore } from 'react';
import { Plus } from 'lucide-react';
import CityPicker from './components/CityPicker.jsx';
import EmbedView from './components/EmbedView.jsx';
import FeedView from './components/FeedView.jsx';
import Header from './components/Header.jsx';
import SearchBar from './components/SearchBar.jsx';
import StyleSwitcher from './components/StyleSwitcher.jsx';
import MasonryGrid from './components/MasonryGrid.jsx';
import UniformGrid from './components/UniformGrid.jsx';
import DateListView from './components/DateListView.jsx';
import PicksList from './components/PicksList.jsx';
import CollectionTargetBar from './components/CollectionTargetBar.jsx';
import EnrichmentEditor from './components/EnrichmentEditor.jsx';
import SubmitEvent from './components/SubmitEvent.jsx';
import PendingEvents from './components/PendingEvents.jsx';
import { useEvents } from './hooks/useEvents.js';
import { useEnrichments } from './hooks/useEnrichments.js';
import { useProcessedEvents } from './hooks/useProcessedEvents.js';
import { useInfiniteScroll } from './hooks/useInfiniteScroll.js';
import { useColumnCount } from './hooks/useColumnCount.js';
import { useAuth } from './hooks/useAuth.jsx';
import { useCurator } from './hooks/useCurator.jsx';
import { useFeatured } from './hooks/useFeatured.jsx';
import { getActiveCategories } from './lib/helpers.js';
import { isGridLayout as checkGridLayout, getColumnCount as calcColumnCount } from './lib/cardStyles.js';

function App() {
  const { embed, embedStyle, embedFeaturedStyle, embedTitle, embedFeaturedTitle, embedNormalTitle, embedBg, embedMode, feed, city } = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return {
      embed: params.get('embed') || null,
      embedStyle: params.get('style') || null,
      embedFeaturedStyle: params.get('featured_style') || null,
      embedTitle: params.get('title') || null,
      embedFeaturedTitle: params.get('featured_title') || null,
      embedNormalTitle: params.get('normal_title') || null,
      embedBg: params.get('bg') || null,
      embedMode: params.get('mode') || null,
      feed: params.get('feed') || null,
      city: params.get('city') || null,
    };
  }, []);

  const { user, session } = useAuth();
  const { isCurator, isCuratorForCity } = useCurator();
  const canCurateCity = isCuratorForCity(city);
  const { featuredStore } = useFeatured();
  const featuredIds = useSyncExternalStore(featuredStore.subscribe, featuredStore.getSnapshot);
  const [filterTerm, setFilterTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [displayCount, setDisplayCount] = useState(50);
  const [cardStyle, setCardStyle] = useState('accent');
  const [viewMode, setViewMode] = useState('cards');
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [showSubmitEvent, setShowSubmitEvent] = useState(false);

  const { events, loading } = useEvents(city, session);
  const enrichments = useEnrichments(city);
  const rawColumnCount = useColumnCount();
  const columnCount = calcColumnCount(cardStyle, rawColumnCount);
  const isGridLayout = checkGridLayout(cardStyle);

  const { processedEvents, cardEvents, hasMore, featuredColumns, masonryColumns, featuredEvents, regularEvents } = useProcessedEvents(
    events,
    enrichments,
    filterTerm,
    displayCount,
    categoryFilter,
    columnCount,
    featuredIds
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
        montclair: 'Montclair', roanoke: 'Roanoke', matsu: 'MatSu', jweekly: 'JWeekly',
        evanston: 'Evanston', portland: 'Portland', boston: 'Boston',
      };
      document.title = (CITY_NAMES[city] || city) + ' Community Calendar';
    }
  }, [city]);

  if (embed) {
    return <EmbedView feedId={embed} style={embedStyle} featuredStyle={embedFeaturedStyle} title={embedTitle} featuredTitle={embedFeaturedTitle} normalTitle={embedNormalTitle} bg={embedBg} mode={embedMode} />;
  }

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

        {/* View mode tabs + Submit Event button */}
        <div className="flex gap-1 mb-4 items-center">
          {canCurateCity && (
            <>
              <button
                onClick={() => setViewMode('cards')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'cards' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Cards
              </button>
              <button
                onClick={() => setViewMode('picks')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'picks' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                My Collections
              </button>
              <button
                onClick={() => setViewMode('pending')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  viewMode === 'pending' ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Pending
              </button>
            </>
          )}
          <div className="ml-auto">
            <button
              onClick={() => setShowSubmitEvent(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <Plus size={16} />
              Submit Event
            </button>
          </div>
        </div>

        {showCreateEvent && (
          <EnrichmentEditor
            mode="create"
            onClose={() => setShowCreateEvent(false)}
            onSaved={() => setShowCreateEvent(false)}
          />
        )}

        {showSubmitEvent && (
          <SubmitEvent
            city={city}
            onClose={() => setShowSubmitEvent(false)}
            onSubmitted={() => setShowSubmitEvent(false)}
          />
        )}

        {viewMode === 'cards' && (
          <>
            {canCurateCity && <CollectionTargetBar />}
            <SearchBar
              filterTerm={filterTerm}
              onFilterTermChange={(val) => { setFilterTerm(val); setDisplayCount(50); }}
              categoryFilter={categoryFilter}
              onCategoryFilterChange={handleCategoryFilter}
              activeCategories={activeCategories}
              onClearAll={handleClearAll}
            />
            <details className="mb-4">
              <summary className="text-xs font-medium text-gray-400 cursor-pointer hover:text-gray-600 select-none">Layout options</summary>
              <div className="mt-2">
                <StyleSwitcher value={cardStyle} onChange={setCardStyle} />
              </div>
            </details>

            {loading && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
              </div>
            )}

            {!loading && events && (
              <>
                {cardStyle === 'datelist' ? (
                  <DateListView events={[...featuredEvents, ...regularEvents]} city={city} />
                ) : isGridLayout ? (
                  <>
                    {featuredEvents.length > 0 && (
                      <div className="mb-6">
                        <UniformGrid
                          events={featuredEvents}
                          filterTerm={filterTerm}
                          onCategoryFilter={handleCategoryFilter}
                          variant={cardStyle}
                          columnCount={columnCount}
                        />
                      </div>
                    )}
                    <UniformGrid
                      events={regularEvents}
                      filterTerm={filterTerm}
                      onCategoryFilter={handleCategoryFilter}
                      variant={cardStyle}
                      columnCount={columnCount}
                    />
                  </>
                ) : (
                  <>
                    {featuredColumns.some(col => col.length > 0) && (
                      <div className="mb-6">
                        <MasonryGrid
                          masonryColumns={featuredColumns}
                          filterTerm={filterTerm}
                          onCategoryFilter={handleCategoryFilter}
                          variant={cardStyle}
                        />
                      </div>
                    )}
                    <MasonryGrid
                      masonryColumns={masonryColumns}
                      filterTerm={filterTerm}
                      onCategoryFilter={handleCategoryFilter}
                      variant={cardStyle}
                    />
                  </>
                )}

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
        {viewMode === 'pending' && <PendingEvents city={city} />}
      </div>
    </div>
  );
}

export default App;
