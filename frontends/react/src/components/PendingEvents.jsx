import React, { useState, useEffect, useMemo } from 'react';
import { Check, XIcon, Loader2, Image, Type, FileText } from 'lucide-react';
import { useAuth } from '../hooks/useAuth.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

const TYPE_ICONS = { image: Image, text: Type, manual: FileText };
const TYPE_LABELS = { image: 'Image', text: 'Text', manual: 'Manual' };

export default function PendingEvents({ city }) {
  const { user, session } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [editId, setEditId] = useState(null);
  const [editFields, setEditFields] = useState({});
  const [errorId, setErrorId] = useState(null);

  const headers = useMemo(() => ({
    apikey: SUPABASE_KEY,
    Authorization: 'Bearer ' + session?.access_token,
  }), [session]);

  useEffect(() => {
    if (!session) return;
    setLoading(true);
    const params = new URLSearchParams({
      status: 'eq.pending',
      order: 'submitted_at.desc',
    });
    if (city) params.set('city', `eq.${city}`);

    fetch(`${SUPABASE_URL}/rest/v1/pending_events?${params}`, { headers })
      .then(r => r.json())
      .then(data => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [session, city]);

  async function handleApprove(pe) {
    setActionId(pe.id);
    setErrorId(null);
    const merged = editId === pe.id ? { ...pe, ...editFields } : pe;
    const jsonHeaders = { ...headers, 'Content-Type': 'application/json', Prefer: 'return=minimal' };
    try {
      // Insert into events table
      const sourceUid = `community_submission:${pe.id}:${Date.now()}`;
      const insertRes = await fetch(`${SUPABASE_URL}/rest/v1/events`, {
        method: 'POST',
        headers: jsonHeaders,
        body: JSON.stringify({
          title: merged.title,
          start_time: merged.start_time,
          end_time: merged.end_time || null,
          location: merged.location || null,
          description: merged.description || null,
          url: merged.url || null,
          city: merged.city || null,
          timezone: merged.timezone || null,
          source: 'community_submission',
          source_uid: sourceUid,
        }),
      });
      if (!insertRes.ok) throw new Error('Failed to insert event');

      // Mark pending event as approved
      await fetch(`${SUPABASE_URL}/rest/v1/pending_events?id=eq.${pe.id}`, {
        method: 'PATCH',
        headers: jsonHeaders,
        body: JSON.stringify({
          status: 'approved',
          reviewed_by: user?.id || null,
          reviewed_at: new Date().toISOString(),
        }),
      });

      setEvents(prev => prev.filter(e => e.id !== pe.id));
      setEditId(null);
    } catch (err) {
      console.error(err);
      setErrorId(pe.id);
    } finally {
      setActionId(null);
    }
  }

  async function handleReject(pe) {
    if (!window.confirm(`Reject "${pe.title}"?`)) return;
    setActionId(pe.id);
    setErrorId(null);
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/pending_events?id=eq.${pe.id}`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
        body: JSON.stringify({
          status: 'rejected',
          reviewed_by: user?.id || null,
          reviewed_at: new Date().toISOString(),
        }),
      });
      if (!res.ok) throw new Error('Reject failed');
      setEvents(prev => prev.filter(e => e.id !== pe.id));
    } catch (err) {
      console.error(err);
      setErrorId(pe.id);
    } finally {
      setActionId(null);
    }
  }

  function startEdit(pe) {
    setEditId(pe.id);
    setEditFields({
      title: pe.title,
      start_time: pe.start_time,
      end_time: pe.end_time || '',
      location: pe.location || '',
      description: pe.description || '',
      url: pe.url || '',
    });
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        No pending submissions
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500 mb-2">{events.length} pending submission{events.length !== 1 ? 's' : ''}</p>
      {events.map(pe => {
        const TypeIcon = TYPE_ICONS[pe.submission_type] || FileText;
        const isEditing = editId === pe.id;
        const isBusy = actionId === pe.id;
        const dateStr = pe.start_time ? new Date(pe.start_time).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '';

        return (
          <div key={pe.id} className={`bg-white rounded-lg border p-4 ${errorId === pe.id ? 'border-red-300' : 'border-gray-200'}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-500">
                    <TypeIcon size={12} />
                    {TYPE_LABELS[pe.submission_type] || 'Unknown'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(pe.submitted_at).toLocaleDateString()}
                  </span>
                </div>

                {isEditing ? (
                  <div className="space-y-2 mt-2">
                    <EditField label="Title" value={editFields.title} onChange={v => setEditFields(f => ({ ...f, title: v }))} />
                    <EditField label="Start" value={editFields.start_time?.substring(0, 16)} onChange={v => setEditFields(f => ({ ...f, start_time: v + ':00' }))} placeholder="YYYY-MM-DDTHH:MM" />
                    <EditField label="Location" value={editFields.location} onChange={v => setEditFields(f => ({ ...f, location: v }))} />
                    <div>
                      <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                      <textarea
                        value={editFields.description}
                        onChange={e => setEditFields(f => ({ ...f, description: e.target.value }))}
                        rows={2}
                        className="w-full rounded border border-gray-200 px-2 py-1 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none resize-none"
                      />
                    </div>
                    <EditField label="URL" value={editFields.url} onChange={v => setEditFields(f => ({ ...f, url: v }))} />
                  </div>
                ) : (
                  <>
                    <p className="font-semibold text-gray-900 text-sm truncate">{pe.title}</p>
                    {dateStr && <p className="text-xs text-gray-500">{dateStr}</p>}
                    {pe.location && <p className="text-xs text-gray-500">{pe.location}</p>}
                    {pe.description && <p className="text-xs text-gray-400 mt-1 line-clamp-2">{pe.description}</p>}
                  </>
                )}
              </div>

              <div className="flex gap-1 flex-shrink-0">
                {!isEditing && (
                  <button
                    onClick={() => startEdit(pe)}
                    className="px-2 py-1 rounded text-xs text-gray-500 hover:bg-gray-100 transition-colors"
                  >
                    Edit
                  </button>
                )}
                {isEditing && (
                  <button
                    onClick={() => setEditId(null)}
                    className="px-2 py-1 rounded text-xs text-gray-500 hover:bg-gray-100 transition-colors"
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={() => handleApprove(pe)}
                  disabled={isBusy}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 transition-colors disabled:opacity-40"
                >
                  {isBusy ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                  Approve
                </button>
                <button
                  onClick={() => handleReject(pe)}
                  disabled={isBusy}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 transition-colors disabled:opacity-40"
                >
                  <XIcon size={12} />
                  Reject
                </button>
              </div>
            </div>
            {errorId === pe.id && (
              <p className="text-xs text-red-600 mt-2">Action failed. Please try again.</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

function EditField({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type="text"
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded border border-gray-200 px-2 py-1 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
      />
    </div>
  );
}
