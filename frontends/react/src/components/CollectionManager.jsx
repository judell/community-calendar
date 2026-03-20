import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, ChevronDown, ChevronRight, Link2, Code, X, Zap, RotateCcw, Pencil, Check } from 'lucide-react';
import { useCollections } from '../hooks/useCollections.js';
import { usePicks } from '../hooks/usePicks.jsx';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import { categoryList } from '../lib/categories.js';
import { formatDayOfWeek, formatMonthDay } from '../lib/helpers.js';

/** Summary text for auto-collection rules */
function ruleSummary(rules) {
  if (!rules) return '';
  const parts = [];
  if (rules.sources?.length) parts.push(rules.sources.join(', '));
  if (rules.categories?.length) parts.push(rules.categories.join(', '));
  return parts.join(' · ');
}

export default function CollectionManager({ expanded, onExpandedChange }) {
  const {
    collections, createCollection, renameCollection, deleteCollection,
    getCollectionEvents, removeEventFromCollection, restoreExcludedEvent,
    updateCollectionRules, updateAllowedDomains,
  } = useCollections();
  const { city } = usePicks();

  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('manual');
  const [selectedSources, setSelectedSources] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [availableSources, setAvailableSources] = useState([]);
  const [creating, setCreating] = useState(false);
  const setExpanded = onExpandedChange;
  const [expandedEvents, setExpandedEvents] = useState([]);
  const [excludedEvents, setExcludedEvents] = useState([]);
  const [copied, setCopied] = useState(null);
  const [embedId, setEmbedId] = useState(null);
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [domainInput, setDomainInput] = useState('');
  const [embedConfig, setEmbedConfig] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cc-embed-config')) || {}; } catch { return {}; }
  });
  const [editSources, setEditSources] = useState([]);
  const [editCategories, setEditCategories] = useState([]);
  const [editingRules, setEditingRules] = useState(false);
  const renameRef = useRef(null);

  // Determine if we need sources: creating an auto collection, or editing one
  const expandedCol = collections.find(c => c.id === expanded);
  const needSources = (newType === 'auto' || expandedCol?.type === 'auto') && city;

  // Fetch distinct sources when needed for auto collection create or edit
  useEffect(() => {
    if (!needSources) { setAvailableSources([]); return; }
    fetch(
      `${SUPABASE_URL}/rest/v1/events?city=eq.${encodeURIComponent(city)}&select=source&order=source`,
      { headers: { apikey: SUPABASE_KEY, Accept: 'application/json' } }
    )
      .then(r => r.json())
      .then(data => {
        if (!Array.isArray(data)) return;
        const all = data.map(d => d.source).filter(Boolean).flatMap(s => s.split(',').map(x => x.trim()));
        const unique = [...new Set(all)];
        setAvailableSources(unique.sort());
      })
      .catch(() => setAvailableSources([]));
  }, [needSources, city]);

  // Load events when a collection is expanded
  useEffect(() => {
    setEditingRules(false);
    if (!expanded) { setExpandedEvents([]); setExcludedEvents([]); return; }
    getCollectionEvents(expanded).then(({ active, excluded }) => {
      setExpandedEvents(active);
      setExcludedEvents(excluded);
    });
  }, [expanded, getCollectionEvents, collections]);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    if (newType === 'auto') {
      const rules = {};
      if (selectedSources.length) rules.sources = selectedSources;
      if (selectedCategories.length) rules.categories = selectedCategories;
      await createCollection(name, { type: 'auto', rules });
    } else {
      await createCollection(name);
    }
    setNewName('');
    setNewType('manual');
    setSelectedSources([]);
    setSelectedCategories([]);
    setCreating(false);
  };

  const handleDelete = async (id) => {
    await deleteCollection(id);
    if (expanded === id) setExpanded(null);
  };

  const handleRemoveEvent = async (collectionId, eventId, sourceUid) => {
    const col = collections.find(c => c.id === collectionId);
    await removeEventFromCollection(collectionId, eventId, sourceUid);
    if (col?.type === 'auto' && sourceUid) {
      // Move to excluded list locally
      const removed = expandedEvents.find(ce => ce.event_id === eventId);
      setExpandedEvents(prev => prev.filter(ce => ce.event_id !== eventId));
      if (removed) setExcludedEvents(prev => [...prev, removed]);
    } else {
      setExpandedEvents(prev => prev.filter(ce => ce.event_id !== eventId));
    }
  };

  const handleRestoreEvent = async (collectionId, sourceUid) => {
    await restoreExcludedEvent(collectionId, sourceUid);
    // Move from excluded back to active locally
    const restored = excludedEvents.find(ce => ce.events?.source_uid === sourceUid);
    setExcludedEvents(prev => prev.filter(ce => ce.events?.source_uid !== sourceUid));
    if (restored) setExpandedEvents(prev => [...prev, restored]);
  };

  const copyShareUrl = (id) => {
    const url = `${window.location.origin}${window.location.pathname}?feed=${id}`;
    navigator.clipboard.writeText(url);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const STYLE_OPTIONS = [
    { value: '', label: 'Default' },
    { value: 'classic', label: 'Classic' },
    { value: 'accent', label: 'Accent' },
    { value: 'magazine', label: 'Magazine' },
    { value: 'modern', label: 'Modern' },
    { value: 'overlay', label: 'Overlay' },
    { value: 'alwaysimage', label: 'Always Image' },
    { value: 'minimal', label: 'Minimal' },
    { value: 'split', label: 'Split' },
    { value: 'splitimage', label: 'Split Image' },
    { value: 'polaroid', label: 'Polaroid' },
    { value: 'ticket', label: 'Ticket' },
    { value: 'noimage', label: 'No Image' },
    { value: 'nodesc', label: 'No Description' },
    { value: 'tile', label: 'Tile' },
    { value: 'compact', label: 'Compact' },
    { value: 'list', label: 'List' },
    { value: 'grid-classic', label: 'Grid: Classic' },
    { value: 'grid-accent', label: 'Grid: Accent' },
    { value: 'grid-magazine', label: 'Grid: Magazine' },
    { value: 'grid-modern', label: 'Grid: Modern' },
    { value: 'grid-overlay', label: 'Grid: Overlay' },
    { value: 'grid-alwaysimage', label: 'Grid: Always Image' },
    { value: 'grid-minimal', label: 'Grid: Minimal' },
    { value: 'grid-split', label: 'Grid: Split' },
    { value: 'grid-splitimage', label: 'Grid: Split Image' },
    { value: 'grid-polaroid', label: 'Grid: Polaroid' },
    { value: 'grid-ticket', label: 'Grid: Ticket' },
    { value: 'grid-noimage', label: 'Grid: No Image' },
    { value: 'grid-nodesc', label: 'Grid: No Desc' },
    { value: 'grid-tile', label: 'Grid: Tile' },
  ];

  const getEmbedCfg = (colId) => embedConfig[colId] || {};
  const setEmbedCfg = (colId, key, value) =>
    setEmbedConfig(prev => {
      const next = { ...prev, [colId]: { ...prev[colId], [key]: value } };
      try { localStorage.setItem('cc-embed-config', JSON.stringify(next)); } catch {}
      return next;
    });

  const buildEmbedCode = (col) => {
    const cfg = getEmbedCfg(col.id);
    const base = `${window.location.origin}${window.location.pathname}`;
    const params = new URLSearchParams({ embed: col.id });
    const style = cfg.style || (col.card_style && col.card_style !== 'accent' ? col.card_style : '');
    const featuredStyle = cfg.featured_style || '';
    const featuredTitle = cfg.featured_title || 'Featured Events';
    const normalTitle = cfg.normal_title || 'Upcoming Events';
    const mode = cfg.mode || '';
    if (style) params.set('style', style);
    if (featuredStyle) params.set('featured_style', featuredStyle);
    params.set('featured_title', featuredTitle);
    params.set('normal_title', normalTitle);
    if (mode) params.set('mode', mode);
    const ghostWide = cfg.ghostWide || false;
    const src = `${base}?${params}`;
    const iframeId = `cc-embed-${col.id}`;
    const classAttr = ghostWide ? ` class="kg-width-wide"` : '';
    return `<iframe id="${iframeId}"${classAttr} src="${src}" width="100%" frameborder="0" style="border:none;overflow:hidden;" scrolling="no"></iframe>
<script>(function(){var f=document.getElementById("${iframeId}");function send(){var r=f.getBoundingClientRect();f.contentWindow.postMessage({type:"community-calendar-embed-viewport",iframeTop:r.top+window.scrollY,iframeHeight:r.height,viewportHeight:window.innerHeight,parentScrollY:window.scrollY},"*")}window.addEventListener("message",function(e){if(e.data&&e.data.type==="community-calendar-embed-resize"){f.style.height=e.data.height+"px";send()}if(e.data&&e.data.type==="community-calendar-embed-ready"){send()}});window.addEventListener("scroll",send,{passive:true});window.addEventListener("resize",send,{passive:true})})();</script>`;
  };

  const copyEmbedCode = (col) => {
    navigator.clipboard.writeText(buildEmbedCode(col));
    setCopied('embed-' + col.id);
    setTimeout(() => setCopied(null), 2000);
  };

  const startRename = (col) => {
    setRenamingId(col.id);
    setRenameValue(col.name);
    setTimeout(() => renameRef.current?.focus(), 0);
  };

  const commitRename = async () => {
    const trimmed = renameValue.trim();
    if (trimmed && renamingId) {
      await renameCollection(renamingId, trimmed);
    }
    setRenamingId(null);
  };

  const toggleSource = (s) => setSelectedSources(prev =>
    prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
  );
  const toggleCategory = (c) => setSelectedCategories(prev =>
    prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
  );

  const toggleEditSource = (s) => setEditSources(prev =>
    prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
  );
  const toggleEditCategory = (c) => setEditCategories(prev =>
    prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
  );

  const startEditRules = (col) => {
    setEditSources(col.rules?.sources || []);
    setEditCategories(col.rules?.categories || []);
    setEditingRules(true);
  };

  const saveEditRules = async (colId) => {
    const rules = {};
    if (editSources.length) rules.sources = editSources;
    if (editCategories.length) rules.categories = editCategories;
    await updateCollectionRules(colId, rules);
    setEditingRules(false);
  };

  const cancelEditRules = () => {
    setEditingRules(false);
  };

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Collections</h3>

      {/* Create new */}
      <div className="mb-3">
        <div className="flex gap-2 mb-2">
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

        {/* Type toggle */}
        <div className="flex gap-1 mb-2">
          <button
            onClick={() => setNewType('manual')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
              newType === 'manual'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Manual
          </button>
          <button
            onClick={() => setNewType('auto')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
              newType === 'auto'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Zap size={11} /> Auto
          </button>
        </div>

        {/* Auto-collection rules panel */}
        {newType === 'auto' && (
          <div className="border border-gray-200 rounded-lg p-3 space-y-3 bg-gray-50">
            {/* Sources */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <p className="text-xs font-medium text-gray-600">Sources</p>
                <button onClick={() => setSelectedSources([...availableSources])} className="text-[10px] text-gray-400 hover:text-gray-600">All</button>
                <button onClick={() => setSelectedSources([])} className="text-[10px] text-gray-400 hover:text-gray-600">None</button>
              </div>
              {availableSources.length === 0 ? (
                <p className="text-xs text-gray-400">Loading sources…</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {availableSources.map(s => (
                    <label key={s} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedSources.includes(s)}
                        onChange={() => toggleSource(s)}
                        className="rounded border-gray-300 text-gray-900 focus:ring-gray-500 h-3.5 w-3.5"
                      />
                      {s}
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Categories */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <p className="text-xs font-medium text-gray-600">Categories</p>
                <button onClick={() => setSelectedCategories([...categoryList])} className="text-[10px] text-gray-400 hover:text-gray-600">All</button>
                <button onClick={() => setSelectedCategories([])} className="text-[10px] text-gray-400 hover:text-gray-600">None</button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {categoryList.map(c => (
                  <label key={c} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedCategories.includes(c)}
                      onChange={() => toggleCategory(c)}
                      className="rounded border-gray-300 text-gray-900 focus:ring-gray-500 h-3.5 w-3.5"
                    />
                    {c}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Collection list */}
      {collections.length === 0 && (
        <p className="text-xs text-gray-400">No collections yet. Create one to organize your picks.</p>
      )}

      <div className="space-y-1">
        {collections.map(col => {
          const isAuto = col.type === 'auto';
          const summary = isAuto ? ruleSummary(col.rules) : '';
          return (
            <div key={col.id} className="border border-gray-100 rounded-lg bg-white">
              <div className="flex items-center gap-2 px-3 py-2">
                <button
                  onClick={() => setExpanded(expanded === col.id ? null : col.id)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {expanded === col.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                {isAuto && <Zap size={12} className="text-amber-500 flex-shrink-0" />}
                <div className="flex-1 min-w-0">
                  {renamingId === col.id ? (
                    <input
                      ref={renameRef}
                      type="text"
                      value={renameValue}
                      onChange={e => setRenameValue(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenamingId(null); }}
                      onBlur={commitRename}
                      className="text-sm font-medium text-gray-800 w-full px-1 py-0 border border-gray-300 rounded focus:outline-none focus:border-gray-500"
                    />
                  ) : (
                    <span
                      className="text-sm font-medium text-gray-800 truncate block cursor-pointer"
                      onDoubleClick={() => startRename(col)}
                      title="Double-click to rename"
                    >
                      {col.name}
                    </span>
                  )}
                  {isAuto && summary && expanded !== col.id && (
                    <span className="text-[10px] text-gray-400 truncate block">{summary}</span>
                  )}
                </div>
                {renamingId !== col.id && (
                  <button
                    onClick={() => startRename(col)}
                    className="text-gray-300 hover:text-gray-500 transition-colors"
                    title="Rename collection"
                  >
                    <Pencil size={12} />
                  </button>
                )}
                {renamingId === col.id && (
                  <button
                    onClick={commitRename}
                    className="text-green-500 hover:text-green-600 transition-colors"
                    title="Save name"
                  >
                    <Check size={14} />
                  </button>
                )}
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
                  onClick={() => embedId === col.id ? setEmbedId(null) : setEmbedId(col.id)}
                  className={`text-xs px-2 py-0.5 rounded transition-colors ${
                    copied === 'embed-' + col.id
                      ? 'bg-green-100 text-green-700'
                      : embedId === col.id
                        ? 'text-gray-700 bg-gray-100'
                        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                  }`}
                  title="Embed code"
                >
                  {copied === 'embed-' + col.id ? 'Copied!' : <Code size={13} />}
                </button>
                <button
                  onClick={() => handleDelete(col.id)}
                  className="text-gray-300 hover:text-red-400 transition-colors"
                  title="Delete collection"
                >
                  <Trash2 size={13} />
                </button>
              </div>

              {/* Embed code panel */}
              {embedId === col.id && (
                <div className="border-t border-gray-50 px-3 py-2 space-y-3">
                  {/* Embed configuration */}
                  <div>
                    <p className="text-[10px] font-medium text-gray-500 mb-2">Embed settings</p>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-[10px] text-gray-500 block mb-0.5">Card style</label>
                        <select
                          value={getEmbedCfg(col.id).style || ''}
                          onChange={e => setEmbedCfg(col.id, 'style', e.target.value)}
                          className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400 bg-white"
                        >
                          {STYLE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 block mb-0.5">Featured style</label>
                        <select
                          value={getEmbedCfg(col.id).featured_style || ''}
                          onChange={e => setEmbedCfg(col.id, 'featured_style', e.target.value)}
                          className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400 bg-white"
                        >
                          {STYLE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 block mb-0.5">Featured title</label>
                        <input
                          type="text"
                          key={`ft-${col.id}`}
                          defaultValue={getEmbedCfg(col.id).featured_title || ''}
                          onBlur={e => setEmbedCfg(col.id, 'featured_title', e.target.value)}
                          placeholder="Featured Events"
                          className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 block mb-0.5">Normal title</label>
                        <input
                          type="text"
                          key={`nt-${col.id}`}
                          defaultValue={getEmbedCfg(col.id).normal_title || ''}
                          onBlur={e => setEmbedCfg(col.id, 'normal_title', e.target.value)}
                          placeholder="Upcoming Events"
                          className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-gray-500 block mb-0.5">Mode</label>
                        <select
                          value={getEmbedCfg(col.id).mode || ''}
                          onChange={e => setEmbedCfg(col.id, 'mode', e.target.value)}
                          className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400 bg-white"
                        >
                          <option value="">Light</option>
                          <option value="dark">Dark</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Domain allowlist */}
                  <div>
                    <p className="text-[10px] font-medium text-gray-500 mb-1">Allowed domains</p>
                    <div className="flex gap-1.5 mb-1.5">
                      <input
                        type="text"
                        value={domainInput}
                        onChange={e => setDomainInput(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            const d = domainInput.trim().toLowerCase();
                            if (d && !(col.allowed_domains || []).includes(d)) {
                              updateAllowedDomains(col.id, [...(col.allowed_domains || []), d]);
                            }
                            setDomainInput('');
                          }
                        }}
                        placeholder="e.g. mysite.com"
                        className="flex-1 px-2 py-1 text-xs border border-gray-200 rounded focus:outline-none focus:border-gray-400"
                      />
                      <button
                        onClick={() => {
                          const d = domainInput.trim().toLowerCase();
                          if (d && !(col.allowed_domains || []).includes(d)) {
                            updateAllowedDomains(col.id, [...(col.allowed_domains || []), d]);
                          }
                          setDomainInput('');
                        }}
                        className="px-2 py-1 text-xs font-medium bg-gray-900 text-white rounded hover:bg-gray-800"
                      >
                        Add
                      </button>
                    </div>
                    {(col.allowed_domains || []).length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {col.allowed_domains.map(d => (
                          <span key={d} className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded-full">
                            {d}
                            <button
                              onClick={() => updateAllowedDomains(col.id, col.allowed_domains.filter(x => x !== d))}
                              className="text-gray-400 hover:text-red-400"
                            >
                              <X size={10} />
                            </button>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[10px] text-gray-400">No restrictions — embed works on any site.</p>
                    )}
                  </div>

                  {/* Generated embed code */}
                  <div className="pt-2 border-t border-gray-100">
                    <label className="flex items-center gap-1.5 mb-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={getEmbedCfg(col.id).ghostWide || false}
                        onChange={e => setEmbedCfg(col.id, 'ghostWide', e.target.checked)}
                        className="rounded border-gray-300 text-gray-900 focus:ring-gray-500 h-3.5 w-3.5"
                      />
                      <span className="text-[11px] text-gray-500">Wide layout on Ghost</span>
                    </label>
                    <p className="text-[10px] font-medium text-gray-500 mb-1">Embed code</p>
                    <div className="flex gap-1.5">
                      <code className="flex-1 text-[11px] text-gray-600 bg-gray-50 border border-gray-200 rounded px-2 py-1.5 block overflow-x-auto whitespace-nowrap">
                        {buildEmbedCode(col)}
                      </code>
                      <button
                        onClick={() => copyEmbedCode(col)}
                        className="flex-shrink-0 px-2.5 py-1.5 text-xs font-medium bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors"
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Expanded: show events in this collection */}
              {expanded === col.id && (
                <div className="border-t border-gray-50 px-3 py-2">
                  {/* Auto-collection rules editor */}
                  {isAuto && (
                    <div className="mb-2">
                      {editingRules ? (
                        <div className="border border-gray-200 rounded-lg p-3 space-y-3 bg-gray-50">
                          {/* Sources */}
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-xs font-medium text-gray-600">Sources</p>
                              <button onClick={() => setEditSources([...availableSources])} className="text-[10px] text-gray-400 hover:text-gray-600">All</button>
                              <button onClick={() => setEditSources([])} className="text-[10px] text-gray-400 hover:text-gray-600">None</button>
                            </div>
                            {availableSources.length === 0 ? (
                              <p className="text-xs text-gray-400">Loading sources…</p>
                            ) : (
                              <div className="flex flex-wrap gap-1.5">
                                {availableSources.map(s => (
                                  <label key={s} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
                                    <input
                                      type="checkbox"
                                      checked={editSources.includes(s)}
                                      onChange={() => toggleEditSource(s)}
                                      className="rounded border-gray-300 text-gray-900 focus:ring-gray-500 h-3.5 w-3.5"
                                    />
                                    {s}
                                  </label>
                                ))}
                              </div>
                            )}
                          </div>
                          {/* Categories */}
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-xs font-medium text-gray-600">Categories</p>
                              <button onClick={() => setEditCategories([...categoryList])} className="text-[10px] text-gray-400 hover:text-gray-600">All</button>
                              <button onClick={() => setEditCategories([])} className="text-[10px] text-gray-400 hover:text-gray-600">None</button>
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {categoryList.map(c => (
                                <label key={c} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={editCategories.includes(c)}
                                    onChange={() => toggleEditCategory(c)}
                                    className="rounded border-gray-300 text-gray-900 focus:ring-gray-500 h-3.5 w-3.5"
                                  />
                                  {c}
                                </label>
                              ))}
                            </div>
                          </div>
                          {/* Save / Cancel */}
                          <div className="flex gap-2">
                            <button
                              onClick={() => saveEditRules(col.id)}
                              className="px-3 py-1 text-xs font-medium bg-gray-900 text-white rounded-md hover:bg-gray-800"
                            >
                              Save rules
                            </button>
                            <button
                              onClick={cancelEditRules}
                              className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => startEditRules(col)}
                          className="flex items-center gap-1.5 text-[11px] text-gray-500 hover:text-gray-700 transition-colors border border-gray-200 hover:border-gray-300 rounded-md px-2.5 py-1.5 bg-white hover:bg-gray-50 w-full text-left"
                        >
                          <Pencil size={10} className="flex-shrink-0" />
                          <span className="truncate">{summary || 'No filters — matching all events'}</span>
                        </button>
                      )}
                    </div>
                  )}

                  {expandedEvents.length === 0 && excludedEvents.length === 0 ? (
                    <p className="text-xs text-gray-400">
                      {isAuto ? 'No matching events.' : 'No events in this collection. Add them from your picks below.'}
                    </p>
                  ) : (
                    <div className="space-y-1">
                      <details className="group">
                        <summary className="text-[11px] text-gray-400 cursor-pointer hover:text-gray-600 select-none">
                          Included posts ({expandedEvents.length})
                        </summary>
                        <div className="mt-1 space-y-1">
                          {expandedEvents.map(ce => {
                            const ev = ce.events;
                            if (!ev) return null;
                            return (
                              <div key={ce.id || ce.event_id} className="flex items-center gap-2 text-xs text-gray-600">
                                <span className="flex-1 truncate">
                                  {ev.title}
                                  {ev.start_time && (
                                    <span className="text-gray-400 ml-1">
                                      · {formatDayOfWeek(ev.start_time, ev.timezone)} {formatMonthDay(ev.start_time, ev.timezone)}
                                    </span>
                                  )}
                                </span>
                                <button
                                  onClick={() => handleRemoveEvent(col.id, ce.event_id, ev.source_uid)}
                                  className="text-gray-300 hover:text-red-400 flex-shrink-0"
                                  title={isAuto ? 'Exclude from auto-collection' : 'Remove from collection'}
                                >
                                  <X size={12} />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </details>
                      {/* Excluded events (auto-collections only) */}
                      {isAuto && excludedEvents.length > 0 && (
                        <>
                          <div className="border-t border-gray-100 mt-2 pt-2">
                            <p className="text-[10px] text-gray-400 mb-1">Excluded</p>
                          </div>
                          {excludedEvents.map(ce => {
                            const ev = ce.events;
                            if (!ev) return null;
                            return (
                              <div key={ce.id || ce.event_id} className="flex items-center gap-2 text-xs text-gray-400">
                                <span className="flex-1 truncate line-through">
                                  {ev.title}
                                  {ev.start_time && (
                                    <span className="ml-1">
                                      · {formatDayOfWeek(ev.start_time, ev.timezone)} {formatMonthDay(ev.start_time, ev.timezone)}
                                    </span>
                                  )}
                                </span>
                                <button
                                  onClick={() => handleRestoreEvent(col.id, ev.source_uid)}
                                  className="text-gray-300 hover:text-green-500 flex-shrink-0"
                                  title="Restore to collection"
                                >
                                  <RotateCcw size={12} />
                                </button>
                              </div>
                            );
                          })}
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
