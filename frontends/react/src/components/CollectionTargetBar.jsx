import React, { useState } from 'react';
import { FolderPlus, X, Plus, Zap } from 'lucide-react';
import { useTargetCollection } from '../hooks/useTargetCollection.jsx';

export default function CollectionTargetBar() {
  const { target, setTarget, collections, createCollection } = useTargetCollection();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    const col = await createCollection(name);
    if (col?.id) setTarget(col.id);
    setNewName('');
    setCreating(false);
  };

  if (target) {
    return (
      <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-indigo-50 border border-indigo-200">
        <FolderPlus size={14} className="text-indigo-500 flex-shrink-0" />
        <span className="text-sm text-indigo-700">
          Bookmarks add to <span className="font-semibold">{target.name}</span>
        </span>
        <button
          onClick={() => setTarget(null)}
          className="ml-auto text-indigo-400 hover:text-indigo-600 transition-colors"
          title="Stop adding to collection"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 mb-3 flex-wrap">
      {collections.map(col => (
        <button
          key={col.id}
          onClick={() => setTarget(col.id)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-gray-400 hover:text-gray-800 transition-colors"
        >
          {col.type === 'auto' ? <Zap size={12} className="text-amber-500" /> : <FolderPlus size={12} />}
          {col.name}
        </button>
      ))}
      {!creating ? (
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-600 transition-colors"
        >
          <Plus size={12} /> New collection
        </button>
      ) : (
        <div className="flex items-center gap-1">
          <input
            type="text"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') handleCreate();
              if (e.key === 'Escape') { setCreating(false); setNewName(''); }
            }}
            placeholder="Collection name…"
            autoFocus
            className="px-2 py-1 text-xs border border-gray-200 rounded-md focus:outline-none focus:border-gray-400 w-36"
          />
          <button
            onClick={handleCreate}
            disabled={!newName.trim()}
            className="px-2 py-1 text-xs font-medium bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:opacity-40"
          >
            Create
          </button>
          <button
            onClick={() => { setCreating(false); setNewName(''); }}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
