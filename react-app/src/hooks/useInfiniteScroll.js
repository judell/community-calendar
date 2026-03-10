import { useEffect, useRef, useCallback } from 'react';

export function useInfiniteScroll(hasMore, onLoadMore) {
  const sentinelRef = useRef(null);
  const throttledRef = useRef(false);

  const loadMore = useCallback(() => {
    if (throttledRef.current || !hasMore) return;
    throttledRef.current = true;
    onLoadMore();
    setTimeout(() => { throttledRef.current = false; }, 600);
  }, [hasMore, onLoadMore]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) loadMore();
      },
      { rootMargin: '0px 0px 800px 0px', threshold: 0 }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  return sentinelRef;
}
