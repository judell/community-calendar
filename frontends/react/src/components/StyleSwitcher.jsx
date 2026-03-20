import React from 'react';

const MASONRY_STYLES = [
  { id: 'classic', label: 'Classic' },
  { id: 'accent', label: 'Accent' },
  { id: 'magazine', label: 'Magazine' },
  { id: 'overlay', label: 'Overlay' },
  { id: 'alwaysimage', label: 'Always Image' },
  { id: 'modern', label: 'Modern' },
  { id: 'minimal', label: 'Minimal' },
  { id: 'split', label: 'Split' },
  { id: 'splitimage', label: 'Split+Icon' },
  { id: 'polaroid', label: 'Polaroid' },
  { id: 'ticket', label: 'Ticket' },
  { id: 'noimage', label: 'No Image' },
  { id: 'nodesc', label: 'No Description' },
  { id: 'tile', label: 'Tiles' },
];

const GRIDDED_STYLES = [
  { id: 'grid-classic', label: 'Classic' },
  { id: 'grid-accent', label: 'Accent' },
  { id: 'grid-magazine', label: 'Magazine' },
  { id: 'grid-overlay', label: 'Overlay' },
  { id: 'grid-alwaysimage', label: 'Always Image' },
  { id: 'grid-modern', label: 'Modern' },
  { id: 'grid-minimal', label: 'Minimal' },
  { id: 'grid-split', label: 'Split' },
  { id: 'grid-splitimage', label: 'Split+Icon' },
  { id: 'grid-polaroid', label: 'Polaroid' },
  { id: 'grid-ticket', label: 'Ticket' },
  { id: 'grid-noimage', label: 'No Image' },
  { id: 'grid-nodesc', label: 'No Description' },
  { id: 'grid-tile', label: 'Tiles' },
];

const OTHER_STYLES = [
  { id: 'list', label: 'List' },
  { id: 'compact', label: 'Compact' },
  { id: 'compactlist', label: 'Compact List' },
  { id: 'datelist', label: 'By Date' },
];

function StyleSection({ heading, styles, value, onChange }) {
  return (
    <div>
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">{heading}</div>
      <div className="flex flex-wrap gap-1.5">
        {styles.map(style => (
          <button
            key={style.id}
            onClick={() => onChange(style.id)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
              value === style.id
                ? 'bg-gray-900 text-white shadow-sm'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
            }`}
          >
            {style.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function StyleSwitcher({ value, onChange }) {
  return (
    <div className="flex flex-col gap-3 mb-4">
      <StyleSection heading="Masonry" styles={MASONRY_STYLES} value={value} onChange={onChange} />
      <StyleSection heading="Gridded" styles={GRIDDED_STYLES} value={value} onChange={onChange} />
      <StyleSection heading="Other" styles={OTHER_STYLES} value={value} onChange={onChange} />
    </div>
  );
}
