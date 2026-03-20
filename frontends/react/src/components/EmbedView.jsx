import React, { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { useCollection } from '../hooks/useCollection.js';
import { useColumnCount } from '../hooks/useColumnCount.js';
import { getMasonryColumns, getActiveCategories } from '../lib/helpers.js';
import { isGridLayout as checkGridLayout, getColumnCount as calcColumnCount } from '../lib/cardStyles.js';
import { FeedProvider } from '../hooks/useFeedContext.jsx';
import MasonryGrid from './MasonryGrid.jsx';
import UniformGrid from './UniformGrid.jsx';
import SearchBar from './SearchBar.jsx';
import SubmitEvent from './SubmitEvent.jsx';
import { Plus } from 'lucide-react';

/**
 * Minimal embeddable feed view.
 * URL params:
 *   embed={feedId}          — collection to display
 *   style={cardStyle}       — card variant (accent, compact, grid, gridtile, etc.)
 *   featured_style={cardStyle} — card variant for featured events (defaults to style)
 *   title={custom title}    — single heading above all events (legacy, overrides both)
 *   featured_title={text}   — heading above featured events section
 *   normal_title={text}     — heading above regular events section
 *   bg={color}              — background color
 *   mode=dark               — dark mode
 *
 * Posts height to parent window via postMessage so the host page
 * can auto-resize the iframe (no scroll-within-scroll).
 */
export default function EmbedView({ feedId, style, featuredStyle, title, featuredTitle, normalTitle, bg, mode }) {
  const isDark = mode === 'dark';
  const { collection, events: allEvents, loading, featuredEvents: earlyFeatured, featuredLoading } = useCollection(feedId);
  const rawColumnCount = useColumnCount();
  const containerRef = useRef(null);
  const observerRef = useRef(null);
  const [filterTerm, setFilterTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showSubmitEvent, setShowSubmitEvent] = useState(false);

  const activeCategories = useMemo(() => getActiveCategories(allEvents), [allEvents]);

  const events = useMemo(() => {
    let filtered = allEvents;
    if (categoryFilter) {
      filtered = filtered.filter(e => e.category === categoryFilter);
    }
    if (filterTerm) {
      const term = filterTerm.toLowerCase();
      filtered = filtered.filter(e =>
        (e.title && e.title.toLowerCase().includes(term)) ||
        (e.description && e.description.toLowerCase().includes(term)) ||
        (e.location && e.location.toLowerCase().includes(term)) ||
        (e.source && e.source.toLowerCase().includes(term))
      );
    }
    return filtered;
  }, [allEvents, filterTerm, categoryFilter]);

  const handleClearAll = useCallback(() => {
    setFilterTerm('');
    setCategoryFilter('');
  }, []);

  const postHeight = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const height = document.documentElement.scrollHeight;
    window.parent.postMessage(
      { type: 'community-calendar-embed-resize', height },
      '*'
    );
  }, []);

  // Observe the container for size changes
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    observerRef.current?.disconnect();
    const observer = new ResizeObserver(postHeight);
    observer.observe(el);
    observerRef.current = observer;
    return () => observer.disconnect();
  }, [postHeight]);

  // Re-post height whenever content changes (events load, window resize)
  useEffect(() => {
    postHeight();
  }, [events, loading, earlyFeatured, postHeight]);

  useEffect(() => {
    window.addEventListener('resize', postHeight);
    return () => window.removeEventListener('resize', postHeight);
  }, [postHeight]);

  const cardStyle = style || collection?.card_style || 'compact';
  const featuredCardStyle = featuredStyle || cardStyle;

  const isGridLayout = checkGridLayout(cardStyle);
  const isFeaturedGridLayout = checkGridLayout(featuredCardStyle);
  const columnCount = calcColumnCount(cardStyle, rawColumnCount);
  const featuredColumnCount = calcColumnCount(featuredCardStyle, rawColumnCount);

  const { featuredEvents, regularEvents } = useMemo(() => {
    // While full events are still loading, use early featured if available
    if (loading && earlyFeatured.length > 0) {
      return { featuredEvents: earlyFeatured, regularEvents: [] };
    }
    const featured = events.filter(e => e._featured);
    if (featured.length === 0) return { featuredEvents: [], regularEvents: events };
    return { featuredEvents: featured, regularEvents: events.filter(e => !e._featured) };
  }, [events, loading, earlyFeatured]);

  const featuredColumns = useMemo(
    () => getMasonryColumns(featuredEvents, featuredColumnCount),
    [featuredEvents, featuredColumnCount]
  );

  const masonryColumns = useMemo(
    () => getMasonryColumns(regularEvents, columnCount),
    [regularEvents, columnCount]
  );

  // Title resolution: legacy `title` param overrides both; otherwise use individual params
  const displayFeaturedTitle = title || featuredTitle;
  const displayNormalTitle = title ? null : normalTitle;

  // Domain allowlist check
  const domainBlocked = useMemo(() => {
    if (!collection?.allowed_domains?.length) return false;
    try {
      const referrerHost = new URL(document.referrer).hostname;
      return !collection.allowed_domains.some(d => {
        // Support both bare hostnames (mysite.com) and full URLs (https://mysite.com)
        let allowed = d;
        try { allowed = new URL(d).hostname; } catch {}
        return referrerHost === allowed || referrerHost.endsWith('.' + allowed);
      });
    } catch {
      // No referrer or invalid — block when allowlist is set
      return true;
    }
  }, [collection]);

  const spinner = (
    <div className="flex justify-center py-8">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
    </div>
  );

  let content;
  if (loading && (featuredLoading || earlyFeatured.length === 0)) {
    content = spinner;
  } else if (loading && earlyFeatured.length > 0) {
    // Progressive: show featured section early while regular events still load
    const hasFeatured = featuredEvents.length > 0;
    content = (
      <>
        {hasFeatured && (
          <div className="mb-6">
            {displayFeaturedTitle && (
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3 px-1">{displayFeaturedTitle}</h2>
            )}
            {isFeaturedGridLayout ? (
              <UniformGrid
                events={featuredEvents}
                filterTerm={filterTerm}
                onCategoryFilter={setCategoryFilter}
                variant={featuredCardStyle}
                columnCount={featuredColumnCount}
              />
            ) : (
              <MasonryGrid
                masonryColumns={featuredColumns}
                filterTerm={filterTerm}
                onCategoryFilter={setCategoryFilter}
                variant={featuredCardStyle}
              />
            )}
          </div>
        )}
        {spinner}
      </>
    );
  } else if (!collection) {
    content = <p className="text-center text-gray-400 py-8 text-sm">Collection not found.</p>;
  } else if (domainBlocked) {
    content = <p className="text-center text-gray-400 py-8 text-sm">This embed is not authorized for this domain.</p>;
  } else if (events.length === 0) {
    content = <p className="text-center text-gray-400 py-8 text-sm">No events yet.</p>;
  } else {
    const hasFeatured = featuredEvents.length > 0;
    content = (
      <>
        {hasFeatured && (
          <div className="mb-6">
            {displayFeaturedTitle && (
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3 px-1">{displayFeaturedTitle}</h2>
            )}
            {isFeaturedGridLayout ? (
              <UniformGrid
                events={featuredEvents}
                filterTerm={filterTerm}
                onCategoryFilter={setCategoryFilter}
                variant={featuredCardStyle}
                columnCount={featuredColumnCount}
              />
            ) : (
              <MasonryGrid
                masonryColumns={featuredColumns}
                filterTerm={filterTerm}
                onCategoryFilter={setCategoryFilter}
                variant={featuredCardStyle}
              />
            )}
          </div>
        )}
        {displayNormalTitle && (
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3 px-1">{displayNormalTitle}</h2>
        )}
        {/* If no featured section exists and legacy title is set, show it above regular events */}
        {!hasFeatured && title && (
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3 px-1">{title}</h1>
        )}
        {isGridLayout ? (
          <UniformGrid
            events={regularEvents}
            filterTerm={filterTerm}
            onCategoryFilter={setCategoryFilter}
            variant={cardStyle}
            columnCount={columnCount}
          />
        ) : (
          <MasonryGrid
            masonryColumns={masonryColumns}
            filterTerm={filterTerm}
            onCategoryFilter={setCategoryFilter}
            variant={cardStyle}
          />
        )}
      </>
    );
  }

  return (
    <FeedProvider collection={collection}>
      <div ref={containerRef} className={`w-full py-4 ${isDark ? 'dark' : ''}`} style={{ backgroundColor: bg || 'transparent' }}>
        {!loading && allEvents.length > 0 && (
          <div className="flex items-start md:gap-2 flex-col md:flex-row">
            <div className="flex-1 min-w-0">
              <SearchBar
                filterTerm={filterTerm}
                onFilterTermChange={setFilterTerm}
                categoryFilter={categoryFilter}
                onCategoryFilterChange={setCategoryFilter}
                activeCategories={activeCategories}
                onClearAll={handleClearAll}
              />
            </div>
            <button
              onClick={() => setShowSubmitEvent(true)}
              className="flex items-center gap-1.5 px-3 py-2 mt-0.5 rounded-lg text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors whitespace-nowrap"
            >
              <Plus size={16} />
              Submit Event
            </button>
          </div>
        )}
        {showSubmitEvent && (
          <div className="mb-4">
            <SubmitEvent
              city={collection?.city}
              onClose={() => setShowSubmitEvent(false)}
              onSubmitted={() => setShowSubmitEvent(false)}
              inline
            />
          </div>
        )}
        {content}
      </div>
    </FeedProvider>
  );
}
