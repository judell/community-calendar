import React from 'react';
import { createPortal } from 'react-dom';
import {
  Info, CalendarPlus, Download, Bookmark, Pencil,
  Palette, BookOpen, Laugh, Users, Drama, GraduationCap, Baby,
  Film, UtensilsCrossed, Landmark, Heart, Clock, Music,
  TreePine, Church, Dumbbell, Calendar,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth.jsx';
import { usePicks, useIsEventPicked } from '../../hooks/usePicks.jsx';
import {
  formatDayOfWeek,
  formatMonthDay,
  formatDateParts,
  formatTime,
  getSnippet,
  getDescriptionSnippet,
  buildGoogleCalendarUrl,
  downloadEventICS,
} from '../../lib/helpers.js';
import { categoryColorMap } from '../../lib/categories.js';
import CATEGORIES from '../../lib/categories.js';
import { SUPABASE_URL, SUPABASE_KEY } from '../../lib/supabase.js';

export const CATEGORY_ICONS = {
  'Arts / Culture': Palette,
  'Books / Literature / Poetry': BookOpen,
  'Comedy / Improv': Laugh,
  'Community / Social': Users,
  'Dance / Performance': Drama,
  'Education / Workshops': GraduationCap,
  'Family / Kids': Baby,
  'Film / Cinema': Film,
  'Food / Drink': UtensilsCrossed,
  'Government / Civic': Landmark,
  'Health / Wellness': Heart,
  'History / Heritage': Clock,
  'Music / Concerts': Music,
  'Nature / Outdoors / Recreation': TreePine,
  'Religion / Spirituality': Church,
  'Sports / Fitness': Dumbbell,
};

export function CategoryIcon({ category, color, size = 40, className = 'opacity-40' }) {
  const Icon = CATEGORY_ICONS[category] || Calendar;
  return <Icon size={size} style={{ color }} strokeWidth={1.5} className={className} />;
}

export const DEFAULT_ACCENT = { label: '#6b7280', background: '#f3f4f6' };

export function useEventCardData(event, filterTerm) {
  const dateParts = formatDateParts(event.start_time);
  const dateStr = formatDayOfWeek(event.start_time) + ' ' + formatMonthDay(event.start_time);
  const timeStr = formatTime(event.start_time);
  const snippet = getSnippet(event.description, event.title);
  const searchSnippet = filterTerm ? getDescriptionSnippet(event.description, filterTerm) : null;
  const colors = categoryColorMap[event.category] || DEFAULT_ACCENT;

  // Search snippet HTML — markup we generate ourselves, not user content
  const searchSnippetHtml = searchSnippet
    ? searchSnippet.replace(
        /\*\*(.+?)\*\*/g,
        '<mark class="bg-yellow-200 text-yellow-800 px-0.5 rounded">$1</mark>'
      )
    : null;

  return { dateParts, dateStr, timeStr, snippet, searchSnippetHtml, colors };
}

export function ActionBar({ event, onCategoryFilter, onShowDetail, colors }) {
  const { user } = useAuth();
  const [showCatModal, setShowCatModal] = React.useState(false);

  return (
    <div className="flex items-center gap-2">
      <CategoryBadgeInline
        category={event.category}
        colors={colors}
        onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
      />
      {user && event.category && (
        <button
          onClick={() => setShowCatModal(true)}
          className="text-gray-300 hover:text-gray-500 transition-colors"
          title="Override category"
        >
          <Pencil size={12} />
        </button>
      )}
      {user && !event.category && (
        <button
          onClick={() => setShowCatModal(true)}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          + category
        </button>
      )}
      {showCatModal && (
        <CategoryOverrideModal
          event={event}
          onClose={() => setShowCatModal(false)}
        />
      )}
      <div className="flex-1" />
      <BookmarkButton event={event} />
      {(event.description || event.image_url) && (
        <button
          onClick={onShowDetail}
          className="text-gray-300 hover:text-gray-500 transition-colors"
          title="View details"
        >
          <Info size={16} />
        </button>
      )}
      <a
        href={buildGoogleCalendarUrl(event)}
        target="_blank"
        rel="noopener noreferrer"
        className="text-gray-300 hover:text-gray-500 transition-colors"
        title="Add to Google Calendar"
      >
        <CalendarPlus size={16} />
      </a>
      <button
        onClick={() => downloadEventICS(event)}
        className="text-gray-300 hover:text-gray-500 transition-colors"
        title="Download .ics"
      >
        <Download size={16} />
      </button>
    </div>
  );
}

const DEFAULT_BOOKMARK_COLOR = '#1e3a5f';

function BookmarkButton({ event }) {
  const { user } = useAuth();
  const { togglePick } = usePicks();
  const picked = useIsEventPicked(event.id);
  const [toggling, setToggling] = React.useState(false);

  if (!user) return null;

  const colors = categoryColorMap[event.category];
  const pickedColor = colors ? colors.label : DEFAULT_BOOKMARK_COLOR;

  async function handleClick() {
    if (toggling) return;
    setToggling(true);
    try { await togglePick(event); } finally { setToggling(false); }
  }

  return (
    <>
      <button
        onClick={handleClick}
        className={`transition-colors ${picked ? '' : 'text-gray-300 hover:text-gray-500'}`}
        style={picked ? { color: pickedColor } : undefined}
        title={picked ? 'Remove from picks' : 'Add to picks'}
      >
        <Bookmark size={16} fill={picked ? 'currentColor' : 'none'} />
      </button>
    </>
  );
}

export function CategoryBadgeInline({ category, colors, onClick }) {
  if (!category) return null;
  return (
    <span
      onClick={onClick}
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium cursor-pointer whitespace-nowrap"
      style={{ color: colors.label, backgroundColor: colors.background }}
    >
      {category}
    </span>
  );
}

export function SearchSnippet({ html }) {
  if (!html) return null;
  return (
    <p
      className="text-sm text-gray-700 mt-2"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// Detail modal — renders DB event descriptions (same trust model as existing XMLUI app)
export function DetailModal({ event, dateStr, timeStr, onClose }) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg max-w-lg w-full max-h-[80vh] overflow-y-auto p-6 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold tracking-tight text-gray-900 mb-2">{event.title}</h2>
        <p className="text-sm text-gray-500 mb-1">
          {dateStr}{timeStr ? `, ${timeStr}` : ''}
        </p>
        {event.location && <p className="text-sm text-gray-700 mb-1">{event.location}</p>}
        {event.source && <p className="text-sm text-gray-400 italic mb-3">{event.source}</p>}
        {event.image_url && (
          <img src={event.image_url} alt="" className="w-full object-contain mb-4 rounded-lg" />
        )}
        {event.description && (
          <div
            className="text-sm font-normal text-gray-700 whitespace-pre-wrap break-words"
            dangerouslySetInnerHTML={{ __html: event.description }}
          />
        )}
        {event.url && (
          <a href={event.url} target="_blank" rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:underline mt-3 block">
            Event link
          </a>
        )}
        <button onClick={onClose}
          className="mt-4 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm font-medium transition-colors">
          Close
        </button>
      </div>
    </div>
  );
}

export function EventTitle({ event, className }) {
  const base = className || 'text-base font-bold tracking-tight text-gray-900 leading-snug';
  if (event.url) {
    return (
      <a href={event.url} target="_blank" rel="noopener noreferrer"
        className={`${base} hover:underline block`}>
        {event.title}
      </a>
    );
  }
  return <h5 className={base}>{event.title}</h5>;
}

function CategoryOverrideModal({ event, onClose }) {
  const { user, session } = useAuth();
  const [selected, setSelected] = React.useState(event.category || '');
  const [saving, setSaving] = React.useState(false);

  async function handleSave() {
    if (!user || !session) return;
    setSaving(true);
    try {
      await fetch(`${SUPABASE_URL}/rest/v1/category_overrides?on_conflict=event_id`, {
        method: 'POST',
        headers: {
          apikey: SUPABASE_KEY,
          Authorization: 'Bearer ' + session.access_token,
          'Content-Type': 'application/json',
          Prefer: 'return=minimal,resolution=merge-duplicates',
        },
        body: JSON.stringify({
          event_id: event.id,
          category: selected,
          curator_id: user.id,
        }),
      });
      // Optimistically update the event object so the UI reflects the change
      event.category = selected;
      onClose();
    } catch {
      // silent fail
    } finally {
      setSaving(false);
    }
  }

  return createPortal(
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-sm w-full max-h-[70vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="px-5 pt-4 pb-2">
          <h3 className="text-base font-bold text-gray-900">Set Category</h3>
          <p className="text-sm text-gray-500 truncate mt-0.5">{event.title}</p>
        </div>
        <div className="px-5 py-2 space-y-1">
          {CATEGORIES.map(cat => {
            const isSelected = selected === cat.name;
            return (
              <label
                key={cat.name}
                className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
                  isSelected ? 'bg-gray-100' : 'hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="category"
                  checked={isSelected}
                  onChange={() => setSelected(cat.name)}
                  className="accent-gray-900"
                />
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: cat.label }}
                />
                <span className="text-sm text-gray-700">{cat.name}</span>
              </label>
            );
          })}
        </div>
        <div className="flex justify-end gap-2 px-5 py-3 border-t border-gray-100">
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
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
