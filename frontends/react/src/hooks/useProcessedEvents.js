import { useMemo } from 'react';
import {
  applyEnrichments,
  dedupeEvents,
  expandEnrichments,
  getCumulativeEvents,
  getMasonryColumns,
} from '../lib/helpers.js';
import { getDateRange } from './useEvents.js';

export function useProcessedEvents(events, enrichments, filterTerm, displayCount, categoryFilter, columnCount, featuredIds) {
  const { from, to } = useMemo(() => getDateRange(), []);

  const processedEvents = useMemo(() => {
    if (!events) return [];
    const enriched = applyEnrichments(events, enrichments);
    const expanded = expandEnrichments(enrichments, from, to);
    const combined = [...enriched, ...expanded];
    const deduped = dedupeEvents(combined);
    return deduped;
  }, [events, enrichments, from, to]);

  // Extract featured from the full processed list (before slicing) so they always appear
  const { featuredEvents, nonFeaturedEvents } = useMemo(() => {
    const isFeatured = e => (featuredIds && featuredIds.has(e.id)) || e._featured;
    const featured = processedEvents.filter(isFeatured);
    if (featured.length === 0) return { featuredEvents: [], nonFeaturedEvents: processedEvents };
    return { featuredEvents: featured, nonFeaturedEvents: processedEvents.filter(e => !isFeatured(e)) };
  }, [processedEvents, featuredIds]);

  const { events: regularEvents, hasMore } = useMemo(() => {
    return getCumulativeEvents(nonFeaturedEvents, filterTerm, displayCount, categoryFilter);
  }, [nonFeaturedEvents, filterTerm, displayCount, categoryFilter]);

  const cardEvents = useMemo(() => {
    return [...featuredEvents, ...regularEvents];
  }, [featuredEvents, regularEvents]);

  const featuredColumns = useMemo(() => {
    return getMasonryColumns(featuredEvents, columnCount);
  }, [featuredEvents, columnCount]);

  const masonryColumns = useMemo(() => {
    return getMasonryColumns(regularEvents, columnCount);
  }, [regularEvents, columnCount]);

  return { processedEvents, cardEvents, hasMore, featuredColumns, masonryColumns, featuredEvents, regularEvents };
}
