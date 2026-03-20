import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Image, Type, FileText, Loader2, CheckCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth.jsx';
import { useCurator } from '../hooks/useCurator.jsx';
import { SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY } from '../lib/supabase.js';

const CAPTURE_URL = `${SUPABASE_URL}/functions/v1/capture-event`;

function resizeImage(file, maxWidth = 1500, quality = 0.8) {
  return new Promise((resolve) => {
    const img = new window.Image();
    img.onload = () => {
      let { width, height } = img;
      if (width > maxWidth) {
        height = Math.round((height * maxWidth) / width);
        width = maxWidth;
      }
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      canvas.getContext('2d').drawImage(img, 0, 0, width, height);
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', quality);
    };
    img.src = URL.createObjectURL(file);
  });
}

const cityTimezones = {
  petaluma: 'America/Los_Angeles',
  portland: 'America/Los_Angeles',
  bloomington: 'America/Indiana/Indianapolis',
  boston: 'America/New_York',
  evanston: 'America/Chicago',
  roanoke: 'America/New_York',
  matsu: 'America/Anchorage',
  jweekly: 'America/Los_Angeles',
  'publisher-resources': 'America/New_York',
};

export default function SubmitEvent({ city, onClose, onSubmitted, inline }) {
  const { user, session } = useAuth();
  const { isCuratorForCity } = useCurator();
  const canCurate = isCuratorForCity(city);
  const eventTimezone = cityTimezones[city] || 'America/Los_Angeles';

  const [tab, setTab] = useState('image');
  const [extracting, setExtracting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Extracted/form fields
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [extracted, setExtracted] = useState(false);

  // Tab-specific state
  const [pasteText, setPasteText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  function populateFromEvent(ev) {
    setTitle(ev.title || '');
    setDate((ev.start_time || '').substring(0, 10));
    setTime((ev.start_time || '').substring(11, 16));
    if (ev.end_time) setEndTime(ev.end_time.substring(11, 16));
    setLocation(ev.location || '');
    setDescription(ev.description || '');
    setUrl(ev.url || '');
    setExtracted(true);
  }

  function resetForm() {
    setTitle(''); setDate(''); setTime(''); setEndTime('');
    setLocation(''); setDescription(''); setUrl('');
    setExtracted(false); setError('');
  }

  // Extract calls use raw fetch with anon JWT — no user auth needed
  async function extractFromImage(formData) {
    const res = await fetch(CAPTURE_URL, {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + SUPABASE_ANON_KEY },
      body: formData,
    });
    if (!res.ok) throw new Error('Extraction failed');
    return res.json();
  }

  async function extractFromText(text) {
    const res = await fetch(CAPTURE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + SUPABASE_ANON_KEY,
      },
      body: JSON.stringify({ mode: 'extract-text', text, timezone: eventTimezone }),
    });
    if (!res.ok) throw new Error('Extraction failed');
    return res.json();
  }

  async function handleImageSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setError('');
    setExtracting(true);
    resetForm();

    try {
      const resized = await resizeImage(file);
      const formData = new FormData();
      formData.append('mode', 'extract');
      formData.append('timezone', eventTimezone);
      formData.append('file', resized, 'image.jpg');

      const data = await extractFromImage(formData);
      if (data.event) populateFromEvent(data.event);
      else throw new Error('No event data returned');
    } catch (err) {
      setError(err.message || 'Failed to extract event from image');
    } finally {
      setExtracting(false);
    }
  }

  async function handleTextExtract() {
    if (!pasteText.trim()) { setError('Please paste some text first'); return; }
    setError('');
    setExtracting(true);
    resetForm();

    try {
      const data = await extractFromText(pasteText);
      if (data.event) populateFromEvent(data.event);
      else throw new Error('No event data returned');
    } catch (err) {
      setError(err.message || 'Failed to extract event from text');
    } finally {
      setExtracting(false);
    }
  }

  async function handleSubmit() {
    if (!title.trim()) { setError('Title is required'); return; }
    if (!date) { setError('Date is required'); return; }
    setError('');
    setSubmitting(true);

    const startTime = date + 'T' + (time || '00:00') + ':00';
    const endTimeStr = endTime ? date + 'T' + endTime + ':00' : null;

    const submissionType = tab === 'image' ? 'image' : tab === 'text' ? 'text' : 'manual';

    try {
      if (canCurate) {
        // Curator: insert directly into events table via REST API
        if (!session?.access_token) { setError('Please sign in'); setSubmitting(false); return; }
        const sourceUid = `community_submission:${user.id}:${Date.now()}`;
        const res = await fetch(`${SUPABASE_URL}/rest/v1/events`, {
          method: 'POST',
          headers: {
            apikey: SUPABASE_KEY,
            Authorization: 'Bearer ' + session.access_token,
            'Content-Type': 'application/json',
            Prefer: 'return=minimal',
          },
          body: JSON.stringify({
            title: title.trim(),
            start_time: startTime,
            end_time: endTimeStr,
            location: location || null,
            description: description || null,
            url: url || null,
            city: city || null,
            timezone: eventTimezone,
            source: 'community_submission',
            source_uid: sourceUid,
          }),
        });
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || 'Failed to save event');
        }
      } else {
        // Public/anonymous: insert into pending_events via REST API (no auth needed)
        const headers = {
          apikey: SUPABASE_KEY,
          'Content-Type': 'application/json',
          Prefer: 'return=minimal',
        };
        if (session?.access_token) {
          headers.Authorization = 'Bearer ' + session.access_token;
        }
        const res = await fetch(`${SUPABASE_URL}/rest/v1/pending_events`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            title: title.trim(),
            start_time: startTime,
            end_time: endTimeStr,
            location: location || null,
            description: description || null,
            url: url || null,
            city: city || null,
            timezone: eventTimezone,
            submitted_by: user?.id || null,
            submission_type: submissionType,
            original_text: tab === 'text' ? pasteText : null,
          }),
        });
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || 'Failed to submit event');
        }
      }
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  }

  const tabs = [
    { id: 'image', label: 'Image', icon: Image },
    { id: 'text', label: 'Text', icon: Type },
    { id: 'manual', label: 'Manual', icon: FileText },
  ];

  const showForm = tab === 'manual' || extracted;

  const modal = (
    <div className="bg-white rounded-xl max-w-md w-full max-h-[85vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-5 pb-3">
        <h2 className="text-lg font-bold text-gray-900">Submit Event</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
          <X size={20} />
        </button>
      </div>

      <div className="px-6 pb-5">
          {success ? (
            <div className="text-center py-6">
              <CheckCircle size={36} className="text-green-500 mx-auto mb-3" />
              <p className="font-semibold text-gray-900 text-lg mb-1">
                {canCurate ? 'Event added!' : 'Event submitted!'}
              </p>
              <p className="text-sm text-gray-500 mb-5">
                {canCurate
                  ? `"${title}" is now live on the calendar.`
                  : `"${title}" has been submitted for review. A curator will review it shortly.`}
              </p>
              <button
                onClick={() => { onSubmitted?.(); onClose(); }}
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Done
              </button>
            </div>
          ) : (
            <>
              {/* Tab bar */}
              <div className="flex gap-1 mb-4">
                {tabs.map(t => (
                  <button
                    key={t.id}
                    onClick={() => { setTab(t.id); resetForm(); setImageFile(null); setImagePreview(null); setPasteText(''); }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      tab === t.id ? 'bg-gray-900 text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <t.icon size={14} />
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Image tab */}
              {tab === 'image' && !extracted && (
                <div className="mb-4">
                  <label className="block border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-gray-300 transition-colors">
                    {imagePreview ? (
                      <img src={imagePreview} alt="Preview" className="max-h-48 mx-auto rounded mb-2" />
                    ) : (
                      <>
                        <Image size={32} className="mx-auto text-gray-300 mb-2" />
                        <p className="text-sm text-gray-500">Click to upload an event poster or flyer</p>
                      </>
                    )}
                    <input type="file" accept="image/*" className="hidden" onChange={handleImageSelect} />
                  </label>
                  {extracting && (
                    <div className="flex items-center justify-center gap-2 mt-3 text-sm text-gray-500">
                      <Loader2 size={16} className="animate-spin" />
                      Extracting event details...
                    </div>
                  )}
                </div>
              )}

              {/* Text tab */}
              {tab === 'text' && !extracted && (
                <div className="mb-4">
                  <textarea
                    value={pasteText}
                    onChange={e => setPasteText(e.target.value)}
                    placeholder="Paste event text here (from a website, email, social media, etc.)"
                    rows={6}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none resize-none mb-2"
                  />
                  <button
                    onClick={handleTextExtract}
                    disabled={extracting || !pasteText.trim()}
                    className="w-full py-2 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
                  >
                    {extracting ? (
                      <><Loader2 size={14} className="animate-spin" /> Extracting...</>
                    ) : (
                      'Extract Event Details'
                    )}
                  </button>
                </div>
              )}

              {/* Review form (shown for manual tab always, or after extraction) */}
              {showForm && (
                <div className="space-y-3 mb-4">
                  <Field label="Title" value={title} onChange={setTitle} />
                  <Field label="Date" value={date} onChange={setDate} placeholder="YYYY-MM-DD" />
                  <div className="flex gap-3">
                    <Field label="Start" value={time} onChange={setTime} placeholder="HH:MM" className="flex-1" />
                    <Field label="End" value={endTime} onChange={setEndTime} placeholder="HH:MM" className="flex-1" />
                  </div>
                  <Field label="Location" value={location} onChange={setLocation} />
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
                    <textarea
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                      rows={3}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-gray-400 focus:ring-0 focus:outline-none resize-none"
                    />
                  </div>
                  <Field label="URL" value={url} onChange={setUrl} placeholder="Event website" />
                </div>
              )}

              {/* Back button for extracted state */}
              {extracted && tab !== 'manual' && (
                <button
                  onClick={() => { resetForm(); }}
                  className="text-xs text-gray-400 hover:text-gray-600 mb-3 transition-colors"
                >
                  &larr; Start over
                </button>
              )}

              {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

              {/* Submit button */}
              {showForm && (
                <div className="flex justify-end gap-2">
                  <button
                    onClick={onClose}
                    className="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-40"
                  >
                    {submitting ? 'Submitting...' : canCurate ? 'Add Event' : 'Submit for Review'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
  );

  if (inline) return modal;

  return createPortal(
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      {modal}
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
