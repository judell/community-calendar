import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { X, CheckCircle, ChevronDown, ChevronRight, CalendarPlus, Download } from 'lucide-react';
import { useAuth } from '../hooks/useAuth.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import {
  formatDayOfWeek, formatMonthDay,
  buildRRule, parseRRule, toggleDay, detectRecurrence, getOrdinalWeekday,
  buildGoogleCalendarUrl, downloadEventICS,
} from '../lib/helpers.js';
import CATEGORIES from '../lib/categories.js';

const DAYS = [
  { code: 'SU', label: 'Su' }, { code: 'MO', label: 'Mo' }, { code: 'TU', label: 'Tu' },
  { code: 'WE', label: 'We' }, { code: 'TH', label: 'Th' }, { code: 'FR', label: 'Fr' },
  { code: 'SA', label: 'Sa' },
];

const ORDINALS = [
  { value: 1, label: '1st' }, { value: 2, label: '2nd' },
  { value: 3, label: '3rd' }, { value: 4, label: '4th' },
];

const DAY_OPTIONS = [
  { value: 'SU', label: 'Sunday' }, { value: 'MO', label: 'Monday' }, { value: 'TU', label: 'Tuesday' },
  { value: 'WE', label: 'Wednesday' }, { value: 'TH', label: 'Thursday' }, { value: 'FR', label: 'Friday' },
  { value: 'SA', label: 'Saturday' },
];

// Mode: 'pick' (picking an event, with form), 'enrich' (editing enrichment for existing pick),
//        or 'create' (manual event — standalone enrichment, no linked event)
export default function EnrichmentEditor({ event, pick, mode = 'pick', onClose, onSaved }) {
  const { user, session } = useAuth();

  // Form fields
  const [title, setTitle] = useState(event?.title || '');
  const [date, setDate] = useState((event?.start_time || '').substring(0, 10));
  const [time, setTime] = useState((event?.start_time || '').substring(11, 16));
  const [endTime, setEndTime] = useState(event?.end_time ? event.end_time.substring(11, 16) : '');
  const [location, setLocation] = useState(event?.location || '');
  const [description, setDescription] = useState(event?.description || '');
  const [category, setCategory] = useState(event?.category || '');

  // Recurrence
  const detected = useMemo(() => detectRecurrence(event?.description, event?.title), [event]);
  const [frequency, setFrequency] = useState(detected?.frequency || 'none');
  const [days, setDays] = useState(detected?.days || []);
  const defaultOrd = useMemo(() => getOrdinalWeekday(date, event?.timezone), [date, event?.timezone]);
  const [ordinal, setOrdinal] = useState(detected?.ordinal || defaultOrd?.ordinal || 1);
  const [monthDay, setMonthDay] = useState(detected?.monthDay || defaultOrd?.day || 'MO');

  // Enrich mode extra fields
  const [urlValue, setUrlValue] = useState('');
  const [notesValue, setNotesValue] = useState('');

  // Recurrence section expanded
  const [showRecurrence, setShowRecurrence] = useState(!!detected);

  // State
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const headers = useMemo(() => ({
    apikey: SUPABASE_KEY,
    Authorization: 'Bearer ' + session?.access_token,
    'Content-Type': 'application/json',
  }), [session]);

  // In enrich mode, load existing enrichment
  useEffect(() => {
    if (mode !== 'enrich' || !user) return;
    const eventId = pick?.event_id || pick?.events?.id || event?.id;
    if (!eventId) return;

    fetch(`${SUPABASE_URL}/rest/v1/event_enrichments?event_id=eq.${eventId}&curator_id=eq.${user.id}`, {
      headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + session?.access_token },
    })
      .then(r => r.json())
      .then(data => {
        if (data?.[0]) {
          const e = data[0];
          const p = parseRRule(e.rrule);
          setFrequency(p.frequency);
          setDays(p.days);
          setUrlValue(e.url || '');
          setNotesValue(e.notes || '');
          if (e.title) setTitle(e.title);
          if (e.location) setLocation(e.location);
          if (e.description) setDescription(e.description);
          if (e.start_time) {
            setDate(e.start_time.substring(0, 10));
            setTime(e.start_time.substring(11, 16));
          }
          if (e.end_time) setEndTime(e.end_time.substring(11, 16));
          if (p.frequency !== 'none') setShowRecurrence(true);
        }
      })
      .catch(() => {});
  }, [mode, pick, user, session]);

  async function handleSave() {
    if (!user) { setError('Please sign in'); return; }
    setSaving(true);
    setError('');

    const rruleStr = buildRRule(frequency, days, ordinal, monthDay);
    const curatorName = user.user_metadata?.preferred_username || user.user_metadata?.full_name || user.email || 'curator';

    try {
      if (mode === 'create') {
        // Manual event — create standalone enrichment with no event_id
        if (!title.trim()) { setError('Title is required'); setSaving(false); return; }
        if (!date) { setError('Date is required'); setSaving(false); return; }

        const startTime = (date || '') + 'T' + (time || '00:00') + ':00';
        const endTimeStr = endTime ? (date || '') + 'T' + endTime + ':00' : null;
        const res = await fetch(`${SUPABASE_URL}/rest/v1/event_enrichments`, {
          method: 'POST',
          headers: { ...headers, Prefer: 'return=representation' },
          body: JSON.stringify({
            event_id: null,
            curator_id: user.id,
            rrule: rruleStr,
            title: title.trim(),
            start_time: startTime,
            end_time: endTimeStr,
            location: location || null,
            description: description || null,
            url: urlValue || null,
            notes: notesValue || null,
            city: new URLSearchParams(window.location.search).get('city') || null,
            curator_name: curatorName,
          }),
        });

        if (!res.ok) {
          setError('Failed to create event');
          setSaving(false);
          return;
        }

        setSuccess(true);
      } else if (mode === 'pick') {
        // Create pick
        const pickRes = await fetch(`${SUPABASE_URL}/rest/v1/picks`, {
          method: 'POST',
          headers: { ...headers, Prefer: 'return=representation' },
          body: JSON.stringify({ user_id: user.id, event_id: event.id }),
        });

        if (!pickRes.ok) {
          const msg = await pickRes.text();
          if (msg.includes('duplicate') || msg.includes('unique') || pickRes.status === 409) {
            setError('This event is already in your picks');
          } else {
            setError('Failed to create pick');
          }
          setSaving(false);
          return;
        }

        // Create enrichment if recurrence set
        if (rruleStr) {
          const startTime = (date || '') + 'T' + (time || '00:00') + ':00';
          const endTimeStr = endTime ? (date || '') + 'T' + endTime + ':00' : null;
          await fetch(`${SUPABASE_URL}/rest/v1/event_enrichments?on_conflict=event_id,curator_id`, {
            method: 'POST',
            headers: { ...headers, Prefer: 'return=minimal,resolution=merge-duplicates' },
            body: JSON.stringify({
              event_id: event.id,
              curator_id: user.id,
              rrule: rruleStr,
              title, start_time: startTime, end_time: endTimeStr,
              location: location || null, description: description || null,
              city: new URLSearchParams(window.location.search).get('city') || null,
              curator_name: curatorName,
            }),
          });
        }

        setSuccess(true);
      } else {
        // Enrich mode — upsert enrichment with all fields
        const eventId = pick?.event_id || pick?.events?.id || event?.id;
        const startTime = (date || '') + 'T' + (time || '00:00') + ':00';
        const endTimeStr = endTime ? (date || '') + 'T' + endTime + ':00' : null;
        await fetch(`${SUPABASE_URL}/rest/v1/event_enrichments?on_conflict=event_id,curator_id`, {
          method: 'POST',
          headers: { ...headers, Prefer: 'return=minimal,resolution=merge-duplicates' },
          body: JSON.stringify({
            event_id: eventId,
            curator_id: user.id,
            rrule: rruleStr,
            title, start_time: startTime, end_time: endTimeStr,
            location: location || null, description: description || null,
            url: urlValue || null,
            notes: notesValue || null,
            city: new URLSearchParams(window.location.search).get('city') || null,
            curator_name: curatorName,
          }),
        });

        // Save category override if changed
        if (category !== (event?.category || '')) {
          await fetch(`${SUPABASE_URL}/rest/v1/category_overrides?on_conflict=event_id`, {
            method: 'POST',
            headers: { ...headers, Prefer: 'return=minimal,resolution=merge-duplicates' },
            body: JSON.stringify({
              event_id: eventId,
              category: category || null,
              curator_id: user.id,
            }),
          });
        }

        onSaved?.();
        onClose();
      }
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  // Build event object for calendar export (success state)
  const calEvent = useMemo(() => ({
    id: event?.id,
    title,
    start_time: (date || '') + 'T' + (time || '00:00') + ':00',
    end_time: endTime ? (date || '') + 'T' + endTime + ':00' : null,
    location, description,
    url: event?.url || null,
    rrule: buildRRule(frequency, days, ordinal, monthDay),
  }), [event, title, date, time, endTime, location, description, frequency, days, ordinal, monthDay]);

  const eventDate = event?.start_time
    ? formatDayOfWeek(event.start_time, event?.timezone) + ' ' + formatMonthDay(event.start_time, event?.timezone)
    : '';

  return createPortal(
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-md w-full max-h-[85vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <h2 className="text-lg font-bold text-gray-900">
            {mode === 'create' ? 'Add Event' : mode === 'pick' ? 'Add to My Picks' : 'Enrich Event'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="px-6 pb-5">
          {!success ? (
            <>
              {/* Event info (skip for create mode — no existing event) */}
              {mode !== 'create' && (
                <>
                  <p className="font-semibold text-gray-900 text-sm">{event?.title || pick?.events?.title}</p>
                  {eventDate && <p className="text-xs text-gray-500 mb-4">{eventDate}</p>}
                </>
              )}

              <div className="space-y-3 mb-4">
                <Field label="Title" value={title} onChange={setTitle} />
                <Field label="Date" value={date} onChange={setDate} placeholder="YYYY-MM-DD" />
                <div className="flex gap-3">
                  <Field label="Start" value={time} onChange={setTime} placeholder="HH:MM" className="flex-1" />
                  <Field label="End" value={endTime} onChange={setEndTime} placeholder="HH:MM" className="flex-1" />
                </div>
                <Field label="Location" value={location} onChange={setLocation} />
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={e => setCategory(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none text-gray-600"
                  >
                    <option value="">None</option>
                    {CATEGORIES.map(cat => (
                      <option key={cat.name} value={cat.name}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                  <textarea
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    rows={3}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none resize-none"
                  />
                </div>
              </div>

              {/* Recurrence section */}
              <div className="border-t border-gray-100 pt-3 mb-4">
                <button
                  onClick={() => setShowRecurrence(v => !v)}
                  className="flex items-center gap-1 text-sm font-medium text-gray-700 mb-2"
                >
                  {showRecurrence ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  Recurrence
                </button>

                {showRecurrence && (
                  <div className="space-y-3 pl-1">
                    <select
                      value={frequency}
                      onChange={e => setFrequency(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
                    >
                      <option value="none">No recurrence</option>
                      <option value="WEEKLY">Weekly</option>
                      <option value="MONTHLY">Monthly</option>
                    </select>

                    {frequency === 'WEEKLY' && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1.5">Repeat on:</p>
                        <div className="flex gap-1">
                          {DAYS.map(d => (
                            <button
                              key={d.code}
                              onClick={() => setDays(toggleDay(days, d.code))}
                              className={`w-9 h-8 rounded-md text-xs font-medium transition-colors ${
                                days.includes(d.code)
                                  ? 'bg-gray-900 text-white'
                                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                              }`}
                            >
                              {d.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {frequency === 'MONTHLY' && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1.5">Repeat on:</p>
                        <div className="flex gap-2">
                          <select
                            value={ordinal}
                            onChange={e => setOrdinal(parseInt(e.target.value))}
                            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
                          >
                            {ORDINALS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                          </select>
                          <select
                            value={monthDay}
                            onChange={e => setMonthDay(e.target.value)}
                            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
                          >
                            {DAY_OPTIONS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                          </select>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-3 mb-4">
                <Field label="URL" value={urlValue} onChange={setUrlValue} placeholder="Reference URL" />
                <Field label="Notes" value={notesValue} onChange={setNotesValue} placeholder="Internal notes" />
              </div>

              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <button
                  onClick={onClose}
                  className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-40"
                >
                  {saving ? 'Saving...' : mode === 'create' ? 'Add Event' : mode === 'pick' ? 'Add to My Picks' : 'Save'}
                </button>
              </div>
            </>
          ) : (
            /* Success state */
            <div className="text-center py-6">
              <CheckCircle size={36} className="text-green-500 mx-auto mb-3" />
              <p className="font-semibold text-gray-900 text-lg mb-1">
                {mode === 'create' ? 'Event added!' : 'Event picked!'}
              </p>
              <p className="text-sm text-gray-500 mb-5">
                "{title}" has been {mode === 'create' ? 'added to the calendar' : 'added to your picks'}.
              </p>

              <div className="space-y-2 mb-4">
                <p className="text-sm font-medium text-gray-700">Add to your calendar:</p>
                <div className="flex justify-center gap-2">
                  <a
                    href={buildGoogleCalendarUrl(calEvent)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    <CalendarPlus size={14} />
                    Google Calendar
                  </a>
                  <button
                    onClick={() => downloadEventICS(calEvent)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    <Download size={14} />
                    Download .ics
                  </button>
                </div>
                <p className="text-xs text-gray-400">For Apple Calendar: download .ics, then open the file.</p>
              </div>

              <button
                onClick={() => { onSaved?.(); onClose(); }}
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

function Field({ label, value, onChange, placeholder, className = '' }) {
  return (
    <div className={className}>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none"
      />
    </div>
  );
}
