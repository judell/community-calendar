import React from 'react';

const STYLES = [
  { id: 'classic', label: 'Classic', desc: 'Clean Flowbite cards' },
  { id: 'accent', label: 'Accent', desc: 'Date chip + color bar' },
  { id: 'magazine', label: 'Magazine', desc: 'Image overlay, editorial' },
  { id: 'compact', label: 'Compact', desc: 'Dense rows, no images' },
  { id: 'modern', label: 'Modern', desc: 'Soft tints, rounded' },
  { id: 'overlay', label: 'Overlay', desc: 'Date + category on image' },
  { id: 'alwaysimage', label: 'Always Image', desc: 'Placeholder when no image' },
  { id: 'minimal', label: 'Minimal', desc: 'Borderless, typography only' },
  { id: 'split', label: 'Split', desc: 'Image left, text right' },
  { id: 'splitimage', label: 'Split+Icon', desc: 'Split with icon placeholder' },
  { id: 'polaroid', label: 'Polaroid', desc: 'Photo frame style' },
  { id: 'ticket', label: 'Ticket', desc: 'Event ticket stub' },
];

export default function StyleSwitcher({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1.5 mb-4">
      {STYLES.map(style => (
        <button
          key={style.id}
          onClick={() => onChange(style.id)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
            value === style.id
              ? 'bg-gray-900 text-white shadow-sm'
              : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
          }`}
          title={style.desc}
        >
          {style.label}
        </button>
      ))}
    </div>
  );
}
