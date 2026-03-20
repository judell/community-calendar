import React from 'react';
import { createPortal } from 'react-dom';
import {
  Info, CalendarPlus, Download, Bookmark, Pencil, X, Settings2, Star,
  Palette, BookOpen, Laugh, Users, Drama, GraduationCap, Baby,
  Film, UtensilsCrossed, Landmark, Heart, Clock, Music,
  TreePine, Church, Dumbbell, Calendar, Lock,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth.jsx';
import { useCurator } from '../../hooks/useCurator.jsx';
import { usePicks, useIsEventPicked } from '../../hooks/usePicks.jsx';
import { useFeatured, useIsEventFeatured } from '../../hooks/useFeatured.jsx';
import { useTargetCollection } from '../../hooks/useTargetCollection.jsx';
import { useFeedContext } from '../../hooks/useFeedContext.jsx';
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
import { getDisplayTimezone, getTimezoneAbbr } from '../../lib/timezone.js';
import { categoryColorMap } from '../../lib/categories.js';
import CATEGORIES from '../../lib/categories.js';
import { SUPABASE_URL, SUPABASE_KEY } from '../../lib/supabase.js';
import EnrichmentEditor from '../EnrichmentEditor.jsx';
import EmbedModal from '../EmbedModal.jsx';

export const hideOnImgError = (e) => { e.target.style.display = 'none'; };

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

export function useEventCardData(event, filterTerm, cityOverride) {
  const { city: picksCity } = usePicks();
  const feedCtx = useFeedContext();
  const city = cityOverride || picksCity || feedCtx?.collection?.city;
  const displayTz = getDisplayTimezone(event, city);
  const dateParts = formatDateParts(event.start_time, displayTz);
  const dateStr = formatDayOfWeek(event.start_time, displayTz) + ' ' + formatMonthDay(event.start_time, displayTz);
  const timeStr = formatTime(event.start_time, displayTz);
  const tzAbbr = (city === 'publisher-resources' && event.timezone)
    ? getTimezoneAbbr(event.start_time, displayTz)
    : null;
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

  return { dateParts, dateStr, timeStr, tzAbbr, snippet, searchSnippetHtml, colors };
}

export function ActionBar({ event, onCategoryFilter, onShowDetail, colors }) {
  const { user } = useAuth();
  const { isCuratorForCity } = useCurator();
  const feedCtx = useFeedContext();
  const [showCatModal, setShowCatModal] = React.useState(false);
  const [showEnrich, setShowEnrich] = React.useState(false);

  const canCurate = isCuratorForCity(event.city);
  const isAutoFeed = feedCtx?.collection?.type === 'auto';
  const removeTitle = isAutoFeed ? 'Exclude from collection' : 'Remove from collection';

  return (
    <div>
      {/* Public tools row */}
      <div className="flex items-center gap-2">
        <CategoryBadgeInline
          category={event.category}
          colors={colors}
          onClick={() => onCategoryFilter && onCategoryFilter(event.category)}
        />
        <div className="flex-1" />
        {(event.description || event.image_url) && (
          <button
            onClick={onShowDetail}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="View details"
          >
            <Info size={16} />
          </button>
        )}
        <a
          href={buildGoogleCalendarUrl(event)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Add to Google Calendar"
        >
          <CalendarPlus size={16} />
        </a>
        <button
          onClick={() => downloadEventICS(event)}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Download .ics"
        >
          <Download size={16} />
        </button>
        {user && <BookmarkButton event={event} />}
      </div>
      {/* Curator tools row */}
      {canCurate && (
        <div className="border-t border-gray-100 dark:border-gray-700 mt-2 pt-2 flex items-center gap-2">
          <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wide">Curator</span>
          <div className="flex-1" />
          {event.category ? (
            <button
              onClick={() => setShowCatModal(true)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Override category"
            >
              <Pencil size={12} />
            </button>
          ) : (
            <button
              onClick={() => setShowCatModal(true)}
              className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-300 transition-colors"
            >
              + category
            </button>
          )}
          <button
            onClick={() => setShowEnrich(true)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="Edit enrichment"
          >
            <Settings2 size={14} />
          </button>
          {feedCtx?.onRemoveEvent && (
            <button
              onClick={() => feedCtx.onRemoveEvent(event)}
              className="text-gray-400 hover:text-red-400 transition-colors"
              title={removeTitle}
            >
              <X size={16} />
            </button>
          )}
          <StarButton event={event} />
        </div>
      )}
      {showCatModal && (
        <CategoryOverrideModal
          event={event}
          onClose={() => setShowCatModal(false)}
        />
      )}
      {showEnrich && (
        <EnrichmentEditor
          event={event}
          mode="enrich"
          onClose={() => setShowEnrich(false)}
          onSaved={() => setShowEnrich(false)}
        />
      )}
    </div>
  );
}

/** Curator tools for compact/hover cards — shown inline. */
export function CuratorTools({ event }) {
  const { user } = useAuth();
  const { isCuratorForCity } = useCurator();
  const feedCtx = useFeedContext();
  const [showCatModal, setShowCatModal] = React.useState(false);
  const [showEnrich, setShowEnrich] = React.useState(false);

  if (!user) return null;

  const canCurate = isCuratorForCity(event.city);
  const isAutoFeed = feedCtx?.collection?.type === 'auto';
  const removeTitle = isAutoFeed ? 'Exclude from collection' : 'Remove from collection';

  return (
    <>
      <div className="flex items-center gap-1.5">
        {canCurate && (
          <>
            {event.category ? (
              <button
                onClick={e => { e.stopPropagation(); setShowCatModal(true); }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                title="Override category"
              >
                <Pencil size={12} />
              </button>
            ) : (
              <button
                onClick={e => { e.stopPropagation(); setShowCatModal(true); }}
                className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-300 transition-colors"
              >
                +cat
              </button>
            )}
            <button
              onClick={e => { e.stopPropagation(); setShowEnrich(true); }}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Edit enrichment"
            >
              <Settings2 size={12} />
            </button>
            {feedCtx?.onRemoveEvent && (
              <button
                onClick={e => { e.stopPropagation(); feedCtx.onRemoveEvent(event); }}
                className="text-gray-400 hover:text-red-400 transition-colors"
                title={removeTitle}
              >
                <X size={14} />
              </button>
            )}
            <StarButton event={event} size={14} />
          </>
        )}
        <BookmarkButton event={event} size={14} />
      </div>
      {showCatModal && (
        <CategoryOverrideModal
          event={event}
          onClose={() => setShowCatModal(false)}
        />
      )}
      {showEnrich && (
        <EnrichmentEditor
          event={event}
          mode="enrich"
          onClose={() => setShowEnrich(false)}
          onSaved={() => setShowEnrich(false)}
        />
      )}
    </>
  );
}

function StarButton({ event, size = 16 }) {
  const { user } = useAuth();
  const { toggleFeatured } = useFeatured();
  const featured = useIsEventFeatured(event.id);

  if (!user) return null;

  return (
    <button
      onClick={(e) => { e.stopPropagation(); toggleFeatured(event); }}
      className={`transition-colors ${featured ? 'text-amber-400' : 'text-gray-400 hover:text-amber-400'}`}
      title={featured ? 'Remove from featured' : 'Feature this event'}
    >
      <Star size={size} fill={featured ? 'currentColor' : 'none'} />
    </button>
  );
}

const DEFAULT_BOOKMARK_COLOR = '#1e3a5f';

function BookmarkButton({ event, size = 16 }) {
  const { user } = useAuth();
  const { togglePick } = usePicks();
  const picked = useIsEventPicked(event.id);
  const { target, addToTarget, removeFromTarget, membershipMap } = useTargetCollection();
  const feedCtx = useFeedContext();
  const [toggling, setToggling] = React.useState(false);

  if (!user) return null;
  // On feed pages, the X button handles removal — hide bookmark to avoid confusion
  if (feedCtx?.onRemoveEvent) return null;

  const colors = categoryColorMap[event.category];
  const pickedColor = colors ? colors.label : DEFAULT_BOOKMARK_COLOR;
  const hasTarget = !!target;
  const inTarget = hasTarget && membershipMap[event.id]?.some(c => c.id === target.id);
  const filled = hasTarget ? inTarget : picked;

  async function handleClick() {
    if (toggling) return;
    setToggling(true);
    try {
      if (hasTarget) {
        if (inTarget) {
          await removeFromTarget(event.id);
        } else {
          // Add to target collection; also pick if not already picked
          if (!picked) await togglePick(event);
          await addToTarget(event.id);
        }
      } else {
        await togglePick(event);
      }
    } finally { setToggling(false); }
  }

  const title = hasTarget
    ? inTarget ? `Remove from ${target.name}` : `Add to ${target.name}`
    : picked ? 'Remove from picks' : 'Add to picks';

  return (
    <button
      onClick={handleClick}
      className={`transition-colors ${filled ? '' : 'text-gray-400 hover:text-gray-600'}`}
      style={filled ? { color: pickedColor } : undefined}
      title={title}
    >
      <Bookmark size={size} fill={filled ? 'currentColor' : 'none'} />
    </button>
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
      className="text-sm text-gray-700 dark:text-gray-300 mt-2"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// Detail modal — renders DB event descriptions (same trust model as existing XMLUI app)
export function DetailModal({ event, dateStr, timeStr, onClose }) {
  return (
    <EmbedModal onClose={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg max-w-lg w-full max-h-[80vh] overflow-y-auto p-6 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold tracking-tight text-gray-900 dark:text-gray-100 mb-2">{event.title}</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
          {dateStr}{timeStr ? `, ${timeStr}` : ''}
        </p>
        {event.location && <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">{event.location}</p>}
        {event.source && <p className="text-sm text-gray-400 italic mb-3">{event.source}</p>}
        {event.image_url && (
          <img src={event.image_url} alt="" className="w-full object-contain mb-4 rounded-lg" onError={hideOnImgError} />
        )}
        {event.description && (
          <div
            className="text-sm font-normal text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words"
            dangerouslySetInnerHTML={{ __html: event.description }}
          />
        )}
        {event.url && (
          <a href={event.url} target="_blank" rel="noopener noreferrer"
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-3 block">
            Event link
          </a>
        )}
        <button onClick={onClose}
          className="mt-4 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium transition-colors">
          Close
        </button>
      </div>
    </EmbedModal>
  );
}

export function EventTitle({ event, className }) {
  const base = className || 'text-base font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-snug';
  const lockIcon = event.is_private ? (
    <Lock size={14} className="inline-block ml-1.5 text-gray-400 align-baseline flex-shrink-0" title="Private source" />
  ) : null;
  if (event.url) {
    return (
      <a href={event.url} target="_blank" rel="noopener noreferrer"
        className={`${base} hover:underline block`}>
        {event.title}{lockIcon}
      </a>
    );
  }
  return <h5 className={base}>{event.title}{lockIcon}</h5>;
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
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-sm w-full max-h-[70vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="px-5 pt-4 pb-2">
          <h3 className="text-base font-bold text-gray-900 dark:text-gray-100">Set Category</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">{event.title}</p>
        </div>
        <div className="px-5 py-2 space-y-1">
          {CATEGORIES.map(cat => {
            const isSelected = selected === cat.name;
            return (
              <label
                key={cat.name}
                className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
                  isSelected ? 'bg-gray-100 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-700'
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
                <span className="text-sm text-gray-700 dark:text-gray-300">{cat.name}</span>
              </label>
            );
          })}
        </div>
        <div className="flex justify-end gap-2 px-5 py-3 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:text-gray-300 transition-colors"
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
