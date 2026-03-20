import React, { useState, useMemo } from 'react';
import { X, Plus, CheckCircle, Rss } from 'lucide-react';
import { getSourceCounts } from '../lib/helpers.js';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

export default function SourcesDialog({ events, onClose }) {
  const [showSuggestForm, setShowSuggestForm] = useState(false);
  const [suggestName, setSuggestName] = useState('');
  const [suggestUrl, setSuggestUrl] = useState('');
  const [suggestFeedType, setSuggestFeedType] = useState('');
  const [suggestNotes, setSuggestNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestSuccess, setSuggestSuccess] = useState(false);
  const [suggestError, setSuggestError] = useState('');

  const sourceCounts = useMemo(() => getSourceCounts(events), [events]);

  const city = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('city') || 'unknown';
  }, []);

  async function handleSubmit() {
    setIsSubmitting(true);
    setSuggestError('');
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/source_suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          apikey: SUPABASE_KEY,
          Prefer: 'return=minimal',
        },
        body: JSON.stringify({
          city,
          name: suggestName,
          url: suggestUrl,
          feed_type: suggestFeedType || null,
          notes: suggestNotes || null,
        }),
      });
      if (!res.ok) throw new Error('Failed');
      setSuggestSuccess(true);
    } catch {
      setSuggestError('Failed to submit suggestion. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetForm() {
    setSuggestSuccess(false);
    setSuggestName('');
    setSuggestUrl('');
    setSuggestFeedType('');
    setSuggestNotes('');
    setSuggestError('');
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl max-w-md w-full max-h-[80vh] overflow-y-auto shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <Rss size={18} className="text-gray-400" />
            <h2 className="text-lg font-bold text-gray-900">Sources</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="px-6 pb-5">
          {/* Summary */}
          <p className="text-sm text-gray-500 mb-4">
            {events ? `${events.length} events` : 'Loading...'}
            <span className="text-gray-400"> &middot; counts reflect overlap between sources</span>
          </p>

          {/* Source list */}
          <div className="space-y-1 mb-5">
            {sourceCounts.map(({ source, count }) => (
              <div key={source} className="flex items-center gap-3 py-1.5">
                <span className="text-sm font-semibold text-gray-700 w-8 text-right tabular-nums">{count}</span>
                <span className="text-sm text-gray-600">{source}</span>
              </div>
            ))}
          </div>

          {/* Suggest a source */}
          {!showSuggestForm && !suggestSuccess && (
            <button
              onClick={() => { setShowSuggestForm(true); resetForm(); }}
              className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              <Plus size={16} />
              Suggest a source
            </button>
          )}

          {showSuggestForm && !suggestSuccess && (
            <div className="mt-3 pt-4 border-t border-gray-100">
              <p className="text-sm text-gray-500 mb-4">
                Know of a local calendar source we're missing? An ICS feed URL is ideal. An RSS feed also works. A link to an events page is fine too.
              </p>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Source name *</label>
                  <input
                    type="text"
                    value={suggestName}
                    onChange={e => setSuggestName(e.target.value)}
                    placeholder="Venue or organization name"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">URL *</label>
                  <input
                    type="text"
                    value={suggestUrl}
                    onChange={e => setSuggestUrl(e.target.value)}
                    placeholder="Link to events page or feed"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Feed type</label>
                  <select
                    value={suggestFeedType}
                    onChange={e => setSuggestFeedType(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none text-gray-600"
                  >
                    <option value="">Select type (if known)</option>
                    <option value="ics">ICS feed</option>
                    <option value="rss">RSS feed</option>
                    <option value="webpage">Events page / other</option>
                    <option value="unknown">Not sure</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Notes</label>
                  <textarea
                    value={suggestNotes}
                    onChange={e => setSuggestNotes(e.target.value)}
                    placeholder="Anything else we should know?"
                    rows={2}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none resize-none"
                  />
                </div>

                {suggestError && (
                  <p className="text-sm text-red-600">{suggestError}</p>
                )}

                <div className="flex justify-end gap-2 pt-1">
                  <button
                    onClick={() => setShowSuggestForm(false)}
                    disabled={isSubmitting}
                    className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !suggestName || !suggestUrl}
                    className="px-4 py-1.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {suggestSuccess && (
            <div className="mt-3 pt-4 border-t border-gray-100 text-center py-4">
              <CheckCircle size={32} className="text-green-500 mx-auto mb-2" />
              <p className="font-semibold text-gray-900 mb-1">Thanks for the suggestion!</p>
              <p className="text-sm text-gray-500 mb-3">We'll look into adding this source.</p>
              <button
                onClick={resetForm}
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Suggest another
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
