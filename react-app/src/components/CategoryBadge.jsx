import React from 'react';
import { Badge } from 'flowbite-react';
import { categoryColorMap } from '../lib/categories.js';

export default function CategoryBadge({ category, onClick }) {
  if (!category) return null;

  const colors = categoryColorMap[category] || { label: '#666', background: '#eee' };

  return (
    <span onClick={onClick} className="cursor-pointer">
      <Badge
        size="xs"
        style={{ color: colors.label, backgroundColor: colors.background, borderColor: colors.background }}
      >
        {category}
      </Badge>
    </span>
  );
}
