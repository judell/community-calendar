import React from 'react';
import { TextInput, Select } from 'flowbite-react';
import { Search, X } from 'lucide-react';

export default function SearchBar({
  filterTerm,
  onFilterTermChange,
  categoryFilter,
  onCategoryFilterChange,
  activeCategories,
  onClearAll,
}) {
  return (
    <div className="flex items-center gap-3 mb-4 flex-wrap sm:flex-nowrap">
      <div className="relative flex-1 min-w-[200px]">
        <TextInput
          type="text"
          placeholder="Search events..."
          value={filterTerm}
          onChange={e => onFilterTermChange(e.target.value)}
          icon={Search}
          sizing="md"
        />
        {filterTerm && (
          <button
            onClick={onClearAll}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X size={18} />
          </button>
        )}
      </div>
      <div className="flex-1 min-w-[200px]">
        <Select
          value={categoryFilter}
          onChange={e => onCategoryFilterChange(e.target.value)}
          sizing="md"
        >
          <option value="">All categories</option>
          {(activeCategories || []).map(cat => (
            <option key={cat.name} value={cat.name}>
              {cat.label}
            </option>
          ))}
        </Select>
      </div>
    </div>
  );
}
