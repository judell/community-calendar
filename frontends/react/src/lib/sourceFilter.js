/**
 * Escape a value for use inside a PostgREST `like` pattern.
 * Percent-encodes characters that are structural in PostgREST
 * query syntax: commas, parentheses, and ampersands.
 */
function pgrstEncode(s) {
  return s
    .replace(/%/g, '%25')
    .replace(/,/g, '%2C')
    .replace(/\(/g, '%28')
    .replace(/\)/g, '%29')
    .replace(/&/g, '%26');
}

/**
 * Build Supabase/PostgREST query params for source inclusion.
 *
 * Uses `like` so that multi-source values ("A, B") match when any
 * individual source is included.
 *
 * If the resulting filter would exceed a safe URL-length budget
 * (e.g. dozens of sources selected), the filter is omitted so the
 * query still succeeds — a few extra events is better than none.
 *
 * @param {string[]} sources - sources to include (empty = all)
 * @returns {string} query string fragment to append (starts with '&')
 */
const MAX_FILTER_LENGTH = 1500; // keep well under typical URL limits

export function buildSourceFilter(sources) {
  if (!sources?.length) return '';
  const parts = sources.map(s => `source.like.*${pgrstEncode(s)}*`).join(',');
  const fragment = `&or=(${parts})`;
  if (fragment.length > MAX_FILTER_LENGTH) return '';
  return fragment;
}
