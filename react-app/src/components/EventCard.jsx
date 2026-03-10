import React from 'react';
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
};

export default function EventCard({ event, filterTerm, onCategoryFilter, variant }) {
  const CardComponent = VARIANTS[variant] || AccentCard;
  return <CardComponent event={event} filterTerm={filterTerm} onCategoryFilter={onCategoryFilter} />;
}
