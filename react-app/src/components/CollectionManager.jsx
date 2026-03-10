import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ChevronDown, ChevronRight, Link2, X } from 'lucide-react';
import { useCollections } from '../hooks/useCollections.js';
import { formatDayOfWeek, formatMonthDay } from '../lib/helpers.js';

export default function CollectionManager() {
  const {
    collections, createCollection, deleteCollection,
    getCollectionEvents, removeEventFromCollection,
  } = useCollections();

  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const [expanded, setExpanded] = useState(null); // collection id
  const [expandedEvents, setExpandedEvents] = useState([]);
  const [copied, setCopied] = useState(null);

  // Load events when a collection is expanded
  useEffect(() => {
    if (!expanded) { setExpandedEvents([]); return; }
    getCollectionEvents(expanded).then(setExpandedEvents);
  }, [expanded, getCollectionEvents, collections]);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    await createCollection(name);
    setNewName('');
    setCreating(false);
  };

  const handleDelete = async (id) => {
    await deleteCollection(id);
    if (expanded === id) setExpanded(null);
  };

  const handleRemoveEvent = async (collectionId, eventId) => {
    await removeEventFromCollection(collectionId, eventId);
    setExpandedEvents(prev => prev.filter(ce => ce.event_id !== eventId));
  };

  const copyShareUrl = (id) => {
    const url = `${window.location.origin}${window.location.pathname}?feed=${id}`;
    navigator.clipboard.writeText(url);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Collections</h3>

      {/* Create new */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleCreate()}
          placeholder="New collection name…"
          className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400"
        />
        <button
          onClick={handleCreate}
          disabled={creating || !newName.trim()}
          className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-40"
        >
          <Plus size={14} /> New
        </button>
      </div>

      {/* Collection list */}
      {collections.length === 0 && (
        <p className="text-xs text-gray-400">No collections yet. Create one to organize your picks.</p>
      )}

      <div className="space-y-1">
        {collections.map(col => (
          <div key={col.id} className="border border-gray-100 rounded-lg bg-white">
            <div className="flex items-center gap-2 px-3 py-2">
              <button
                onClick={() => setExpanded(expanded === col.id ? null : col.id)}
                className="text-gray-400 hover:text-gray-600"
              >
                {expanded === col.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              <span className="flex-1 text-sm font-medium text-gray-800 truncate">{col.name}</span>
              <button
                onClick={() => copyShareUrl(col.id)}
                className={`text-xs px-2 py-0.5 rounded transition-colors ${
                  copied === col.id
                    ? 'bg-green-100 text-green-700'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                }`}
                title="Copy share link"
              >
                {copied === col.id ? 'Copied!' : <Link2 size={13} />}
              </button>
              <button
                onClick={() => handleDelete(col.id)}
                className="text-gray-300 hover:text-red-400 transition-colors"
                title="Delete collection"
              >
                <Trash2 size={13} />
              </button>
            </div>

            {/* Expanded: show events in this collection */}
            {expanded === col.id && (
              <div className="border-t border-gray-50 px-3 py-2">
                {expandedEvents.length === 0 ? (
                  <p className="text-xs text-gray-400">No events in this collection. Add them from your picks below.</p>
                ) : (
                  <div className="space-y-1">
                    {expandedEvents.map(ce => {
                      const ev = ce.events;
                      if (!ev) return null;
                      return (
                        <div key={ce.id} className="flex items-center gap-2 text-xs text-gray-600">
                          <span className="flex-1 truncate">
                            {ev.title}
                            {ev.start_time && (
                              <span className="text-gray-400 ml-1">
                                · {formatDayOfWeek(ev.start_time)} {formatMonthDay(ev.start_time)}
                              </span>
                            )}
                          </span>
                          <button
                            onClick={() => handleRemoveEvent(col.id, ce.event_id)}
                            className="text-gray-300 hover:text-red-400 flex-shrink-0"
                            title="Remove from collection"
                          >
                            <X size={12} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
