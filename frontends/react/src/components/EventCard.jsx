import React from 'react';
import { Star } from 'lucide-react';
import { useIsEventFeatured } from '../hooks/useFeatured.jsx';
import { parseCardStyle } from '../lib/cardStyles.js';
import ClassicCard from './cards/ClassicCard.jsx';
import AccentCard from './cards/AccentCard.jsx';
import MagazineCard from './cards/MagazineCard.jsx';
import CompactCard from './cards/CompactCard.jsx';
import ModernCard from './cards/ModernCard.jsx';
import OverlayCard from './cards/OverlayCard.jsx';
import AlwaysImageCard from './cards/AlwaysImageCard.jsx';
import MinimalCard from './cards/MinimalCard.jsx';
import SplitCard from './cards/SplitCard.jsx';
import SplitImageCard from './cards/SplitImageCard.jsx';
import PolaroidCard from './cards/PolaroidCard.jsx';
import TicketCard from './cards/TicketCard.jsx';
import NoImageCard from './cards/NoImageCard.jsx';
import NoDescCard from './cards/NoDescCard.jsx';
import TileCard from './cards/TileCard.jsx';

const VARIANTS = {
  classic: ClassicCard,
  accent: AccentCard,
  magazine: MagazineCard,
  compact: CompactCard,
  modern: ModernCard,
  overlay: OverlayCard,
  alwaysimage: AlwaysImageCard,
  minimal: MinimalCard,
  split: SplitCard,
  splitimage: SplitImageCard,
  polaroid: PolaroidCard,
  ticket: TicketCard,
  list: SplitCard,
  compactlist: CompactCard,
  noimage: NoImageCard,
  nodesc: NoDescCard,
  tile: TileCard,
};

export default function EventCard({ event, filterTerm, onCategoryFilter, variant }) {
  const { baseStyle } = parseCardStyle(variant);
  const CardComponent = VARIANTS[baseStyle] || VARIANTS[variant] || AccentCard;
  const featured = useIsEventFeatured(event.id) || event._featured;

  if (featured) {
    return (
      <div className="relative">
        <div className="absolute top-2 right-2 z-10 text-amber-400">
          <Star size={14} fill="currentColor" />
        </div>
        <CardComponent event={event} filterTerm={filterTerm} onCategoryFilter={onCategoryFilter} />
      </div>
    );
  }

  return <CardComponent event={event} filterTerm={filterTerm} onCategoryFilter={onCategoryFilter} />;
}
