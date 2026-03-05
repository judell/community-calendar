#!/usr/bin/env python3
"""
Two-tier event classifier for community calendar events.

Tier 1: Map ICS CATEGORIES tags to buckets (high confidence).
Tier 2: Keyword regex on title (medium confidence) or description (low confidence).

Events with only low confidence (description-only match) get category=None by default.
"""

import re

CATEGORIES = [
    "Music & Concerts",
    "Sports & Fitness",
    "Arts & Culture",
    "Education & Workshops",
    "Community & Social",
    "Family & Kids",
    "Food & Drink",
    "Health & Wellness",
    "Nature & Outdoors",
    "Religion & Spirituality",
]

# --- Tier 1: ICS CATEGORIES tag → bucket ---
# Lowercase tag → bucket name. Built from analysis of all ICS feeds.
ICS_CATEGORY_MAP = {
    # Music & Concerts
    'concert': 'Music & Concerts',
    'concerts (music)': 'Music & Concerts',
    'concerts (music': 'Music & Concerts',
    'live music': 'Music & Concerts',
    'live-music': 'Music & Concerts',
    'livemusic': 'Music & Concerts',
    'music': 'Music & Concerts',
    'music/dance': 'Music & Concerts',
    'concert/music': 'Music & Concerts',
    'jazz': 'Music & Concerts',
    'blues': 'Music & Concerts',
    'rock': 'Music & Concerts',
    'folk': 'Music & Concerts',
    'hip hop': 'Music & Concerts',
    'dj': 'Music & Concerts',
    'dj/club/rave': 'Music & Concerts',
    'dj/club/ra': 'Music & Concerts',
    'dj/club': 'Music & Concerts',
    'karaoke': 'Music & Concerts',
    'open mic': 'Music & Concerts',
    'open-mic': 'Music & Concerts',
    'singer-songwriter': 'Music & Concerts',
    'acoustic': 'Music & Concerts',
    'soul': 'Music & Concerts',
    'funk': 'Music & Concerts',
    'funk-music': 'Music & Concerts',
    'punk': 'Music & Concerts',
    'punk-rock-music': 'Music & Concerts',
    'metal-music': 'Music & Concerts',
    'hardcore-music': 'Music & Concerts',
    'pop music': 'Music & Concerts',
    'pop rock': 'Music & Concerts',
    'pop-music': 'Music & Concerts',
    'pop-folk': 'Music & Concerts',
    'progressive rock': 'Music & Concerts',
    'psychedelic rock': 'Music & Concerts',
    'clasic rock': 'Music & Concerts',
    'country blues': 'Music & Concerts',
    'soul-folk rock': 'Music & Concerts',
    'americana': 'Music & Concerts',
    'bluegrass': 'Music & Concerts',
    'celtic': 'Music & Concerts',
    'fingerstyle': 'Music & Concerts',
    'reggaeton': 'Music & Concerts',
    'soca': 'Music & Concerts',
    'experimental': 'Music & Concerts',
    'listening-party': 'Music & Concerts',
    'live-podcast': 'Music & Concerts',
    'choir practice': 'Music & Concerts',
    'bell choir practice': 'Music & Concerts',
    '80s music': 'Music & Concerts',

    # Sports & Fitness
    'athletics': 'Sports & Fitness',
    'athletic': 'Sports & Fitness',
    'sports': 'Sports & Fitness',
    'fitness': 'Sports & Fitness',
    'yoga': 'Sports & Fitness',
    'pilates': 'Sports & Fitness',
    'zumba': 'Sports & Fitness',
    'baseball': 'Sports & Fitness',
    'skating': 'Sports & Fitness',
    'hike': 'Sports & Fitness',
    'hiking': 'Sports & Fitness',
    'bicycling': 'Sports & Fitness',
    'walking': 'Sports & Fitness',
    'excercise': 'Sports & Fitness',
    'health & fitness': 'Sports & Fitness',

    # Arts & Culture
    'art': 'Arts & Culture',
    'arts': 'Arts & Culture',
    'art & culture': 'Arts & Culture',
    'arts & culture': 'Arts & Culture',
    'arts-&-culture': 'Arts & Culture',
    'arts & crafts': 'Arts & Culture',
    'arts & humanities': 'Arts & Culture',
    'arts activity': 'Arts & Culture',
    'visual-arts': 'Arts & Culture',
    'visual and creative arts': 'Arts & Culture',
    'gallery': 'Arts & Culture',
    'exhibit': 'Arts & Culture',
    'exhibits': 'Arts & Culture',
    'exhibition': 'Arts & Culture',
    'exhibitions': 'Arts & Culture',
    'exhibits & tours': 'Arts & Culture',
    'art exhibition': 'Arts & Culture',
    'art and museum exhibitions': 'Arts & Culture',
    'museum': 'Arts & Culture',
    'painting': 'Arts & Culture',
    'watercolor': 'Arts & Culture',
    'acrylic': 'Arts & Culture',
    'acrylic-painting': 'Arts & Culture',
    'oil-paint': 'Arts & Culture',
    'pastels': 'Arts & Culture',
    'colored-pencil': 'Arts & Culture',
    'drawing': 'Arts & Culture',
    'portrait': 'Arts & Culture',
    'calligraphy': 'Arts & Culture',
    'sculpture': 'Arts & Culture',
    'ceramic': 'Arts & Culture',
    'pottery': 'Arts & Culture',
    'printmak': 'Arts & Culture',
    'craft': 'Arts & Culture',
    'film': 'Arts & Culture',
    'films': 'Arts & Culture',
    'film/movie': 'Arts & Culture',
    'cinema/film/movies': 'Arts & Culture',
    'movie': 'Arts & Culture',
    'movie/film': 'Arts & Culture',
    'movies': 'Arts & Culture',
    'screening': 'Arts & Culture',
    'theater': 'Arts & Culture',
    'theatre': 'Arts & Culture',
    'theater & musicals': 'Arts & Culture',
    'theatre & opera': 'Arts & Culture',
    'theatre arts': 'Arts & Culture',
    'musical': 'Arts & Culture',
    'musical theatre': 'Arts & Culture',
    'ballet': 'Arts & Culture',
    'dance': 'Arts & Culture',
    'dancing': 'Arts & Culture',
    'dance performance': 'Arts & Culture',
    'dance ensemble': 'Arts & Culture',
    'dance-music': 'Arts & Culture',
    'dance---performance---theatre': 'Arts & Culture',
    'modern dance': 'Arts & Culture',
    'contemporary': 'Arts & Culture',
    'performance': 'Arts & Culture',
    'performances': 'Arts & Culture',
    'performances & arts': 'Arts & Culture',
    'performing arts': 'Arts & Culture',
    'performance art': 'Arts & Culture',
    'live performance': 'Arts & Culture',
    'liveperformance': 'Arts & Culture',
    'live shows': 'Arts & Culture',
    'comedy': 'Arts & Culture',
    'comedy & improv': 'Arts & Culture',
    'comedy-show': 'Arts & Culture',
    'improv': 'Arts & Culture',
    'burlesque': 'Arts & Culture',
    'circus': 'Arts & Culture',
    'poetry': 'Arts & Culture',
    'literary': 'Arts & Culture',
    'literary-arts': 'Arts & Culture',
    'spoken word/readings': 'Arts & Culture',
    'spoken-word/poetry': 'Arts & Culture',
    'book-launch': 'Arts & Culture',
    'writing': 'Arts & Culture',
    'author': 'Arts & Culture',
    'author talk': 'Arts & Culture',
    'author visit': 'Arts & Culture',
    'cultural': 'Arts & Culture',
    'culture and diversity': 'Arts & Culture',
    'culture and languages': 'Arts & Culture',
    'reenactments & living history': 'Arts & Culture',
    'radio play': 'Arts & Culture',
    'shows': 'Arts & Culture',
    # Dance styles → Arts & Culture
    'salsa': 'Arts & Culture',
    'bachata': 'Arts & Culture',
    'ballroom': 'Arts & Culture',
    'swing': 'Arts & Culture',
    'swing-dancing': 'Arts & Culture',
    'lindy hop': 'Arts & Culture',
    'lindy': 'Arts & Culture',
    'kizomba': 'Arts & Culture',
    'zouk': 'Arts & Culture',
    'tango - ballroom': 'Arts & Culture',
    'argentine tango': 'Arts & Culture',
    'cha cha': 'Arts & Culture',
    'merengue': 'Arts & Culture',
    'semba': 'Arts & Culture',
    'hustle': 'Arts & Culture',
    'flamenco': 'Arts & Culture',
    'bellydance': 'Arts & Culture',
    'hula': 'Arts & Culture',
    'bollywood': 'Arts & Culture',
    'contact improvisation': 'Arts & Culture',
    'contra dance': 'Arts & Culture',
    'english country dance': 'Arts & Culture',
    'scottish country dance': 'Arts & Culture',
    'square dance': 'Arts & Culture',
    'line dance': 'Arts & Culture',
    'line dancing': 'Arts & Culture',
    'line-dancing': 'Arts & Culture',
    'country two step': 'Arts & Culture',
    'east coast swing': 'Arts & Culture',
    'west coast swing': 'Arts & Culture',
    'ecstatic': 'Arts & Culture',
    'vogue': 'Arts & Culture',
    'waacking': 'Arts & Culture',
    'krump': 'Arts & Culture',
    'breakdance': 'Arts & Culture',
    'afrocuban': 'Arts & Culture',
    'cumbia': 'Arts & Culture',

    # Education & Workshops
    'class': 'Education & Workshops',
    'classes': 'Education & Workshops',
    'classes & workshops': 'Education & Workshops',
    'classes & lectures': 'Education & Workshops',
    'classes & camps': 'Education & Workshops',
    'workshop': 'Education & Workshops',
    'workshops': 'Education & Workshops',
    'workshops and training': 'Education & Workshops',
    'workshops and classes': 'Education & Workshops',
    'workshops & trainings': 'Education & Workshops',
    'workshop/short course': 'Education & Workshops',
    'seminar': 'Education & Workshops',
    'seminars': 'Education & Workshops',
    'lecture': 'Education & Workshops',
    'lectures': 'Education & Workshops',
    'lectures & talks': 'Education & Workshops',
    'lectures and talks': 'Education & Workshops',
    'lectures/conferences': 'Education & Workshops',
    'lecture/book-talk': 'Education & Workshops',
    'lecture/talk': 'Education & Workshops',
    'panel/seminar/colloquium': 'Education & Workshops',
    'panels & book discussions': 'Education & Workshops',
    'talk': 'Education & Workshops',
    'talks': 'Education & Workshops',
    'speaker': 'Education & Workshops',
    'speakers': 'Education & Workshops',
    'training': 'Education & Workshops',
    'education': 'Education & Workshops',
    'education programs': 'Education & Workshops',
    'thoughtfullearning': 'Education & Workshops',
    'adult classes': 'Education & Workshops',
    'adult education': 'Education & Workshops',
    'adult school': 'Education & Workshops',
    'academic calendar': 'Education & Workshops',
    'academic/career': 'Education & Workshops',
    'academic/educational': 'Education & Workshops',
    'career development': 'Education & Workshops',
    'career fair': 'Education & Workshops',
    'conference/symposium': 'Education & Workshops',
    'meetings and conferences': 'Education & Workshops',
    'information session': 'Education & Workshops',
    'teacher workshop': 'Education & Workshops',
    'teacher open house': 'Education & Workshops',
    'stem / steam': 'Education & Workshops',
    'steam': 'Education & Workshops',
    'tutoring': 'Education & Workshops',
    'study abroad fair': 'Education & Workshops',

    # Community & Social
    'community': 'Community & Social',
    'community events': 'Community & Social',
    'community event': 'Community & Social',
    'community engagement': 'Community & Social',
    'community outreach': 'Community & Social',
    'community programs': 'Community & Social',
    'building community': 'Community & Social',
    'social': 'Community & Social',
    'social event': 'Community & Social',
    'social clubs': 'Community & Social',
    'socials': 'Community & Social',
    'meeting': 'Community & Social',
    'public meetings': 'Community & Social',
    'board & committee meetings': 'Community & Social',
    'festival': 'Community & Social',
    'festivals & fairs': 'Community & Social',
    'fairs & festivals': 'Community & Social',
    'parade': 'Community & Social',
    'parades & community celebrations': 'Community & Social',
    'celebration': 'Community & Social',
    'celebrations & commemorations': 'Community & Social',
    'ceremonies & anniversaries': 'Community & Social',
    'market': 'Community & Social',
    "farmers' market": 'Community & Social',
    'volunteer': 'Community & Social',
    'volunteer opportunities': 'Community & Social',
    'volunteer and fundraising opportunities': 'Community & Social',
    'fundraiser': 'Community & Social',
    'fundraisers': 'Community & Social',
    'fundraising': 'Community & Social',
    'fundraiser/philanthropy': 'Community & Social',
    'open house': 'Community & Social',
    'open houses': 'Community & Social',
    'tours and open houses': 'Community & Social',
    'guided tour': 'Community & Social',
    'guided tours': 'Community & Social',
    'trivia': 'Community & Social',
    'trivia-night': 'Community & Social',
    'game night': 'Community & Social',
    'games & trivia': 'Community & Social',
    'party': 'Community & Social',
    'mixer': 'Community & Social',
    'mixers and parties': 'Community & Social',
    'pop-up': 'Community & Social',
    'repair café': 'Community & Social',
    'tradition & community': 'Community & Social',
    'service project': 'Community & Social',

    # Family & Kids
    'family': 'Family & Kids',
    'family friendly': 'Family & Kids',
    'family days': 'Family & Kids',
    'family program': 'Family & Kids',
    'for families': 'Family & Kids',
    'kids & families': 'Family & Kids',
    'kids events': 'Family & Kids',
    'kids classes': 'Family & Kids',
    'kids camps': 'Family & Kids',
    'kids / youth': 'Family & Kids',
    'children': 'Family & Kids',
    "children's programs": 'Family & Kids',
    'children/youth': 'Family & Kids',
    'youth': 'Family & Kids',
    'youth programs': 'Family & Kids',
    'youth & family activities': 'Family & Kids',
    'youth ensemble': 'Family & Kids',
    'teens': 'Family & Kids',
    'teen services': 'Family & Kids',
    'toddler-programming': 'Family & Kids',
    'early-learners': 'Family & Kids',
    'early-years': 'Family & Kids',
    'early years programs': 'Family & Kids',
    'mom and baby': 'Family & Kids',
    'storytime': 'Family & Kids',
    'story time': 'Family & Kids',
    'f.a.m. (families at the museum)': 'Family & Kids',
    'homeschool & education days': 'Family & Kids',

    # Food & Drink
    'food': 'Food & Drink',
    'food & drink': 'Food & Drink',
    'food & cooking': 'Food & Drink',
    'food & wine': 'Food & Drink',
    'culinary': 'Food & Drink',
    'wine': 'Food & Drink',
    'wines': 'Food & Drink',
    'wine tasting': 'Food & Drink',
    'beer': 'Food & Drink',
    'beer and cheer': 'Food & Drink',
    'brewery': 'Food & Drink',
    'spirits': 'Food & Drink',
    'tastings': 'Food & Drink',
    'dining': 'Food & Drink',
    'dinner': 'Food & Drink',
    'breakfast': 'Food & Drink',
    'brunch': 'Food & Drink',
    'happy-hour': 'Food & Drink',
    'cheese': 'Food & Drink',

    # Health & Wellness
    'health': 'Health & Wellness',
    'health & wellness': 'Health & Wellness',
    'health/wellness': 'Health & Wellness',
    'health and wellness': 'Health & Wellness',
    'health and nutrition': 'Health & Wellness',
    'wellness': 'Health & Wellness',
    'wellness day': 'Health & Wellness',
    'wellness and community': 'Health & Wellness',
    'well-being': 'Health & Wellness',
    'emotional wellness': 'Health & Wellness',
    'physical wellness': 'Health & Wellness',
    'intellectual wellness': 'Health & Wellness',
    'occupational wellness': 'Health & Wellness',
    'social wellness': 'Health & Wellness',
    'environmental wellness': 'Health & Wellness',
    'cultural wellness': 'Health & Wellness',
    'grief support': 'Health & Wellness',
    'grief support for adults': 'Health & Wellness',
    'therapeutic': 'Health & Wellness',
    'healing': 'Health & Wellness',

    # Nature & Outdoors
    'nature': 'Nature & Outdoors',
    'nature walk': 'Nature & Outdoors',
    'nature hike': 'Nature & Outdoors',
    'nature stories': 'Nature & Outdoors',
    'nature & wildlife programs': 'Nature & Outdoors',
    'outdoor': 'Nature & Outdoors',
    'outdoor & recreation': 'Nature & Outdoors',
    'outdoor experiences': 'Nature & Outdoors',
    'outdoor recreation (kayak': 'Nature & Outdoors',
    'outdoors': 'Nature & Outdoors',
    'garden': 'Nature & Outdoors',
    'gardening': 'Nature & Outdoors',
    'vegetable gardening': 'Nature & Outdoors',
    'botanical': 'Nature & Outdoors',
    'birding': 'Nature & Outdoors',
    'bird walk': 'Nature & Outdoors',
    'all things birds': 'Nature & Outdoors',
    'wildlife habitats': 'Nature & Outdoors',
    'stewardship': 'Nature & Outdoors',
    'conservation': 'Nature & Outdoors',
    'native plants': 'Nature & Outdoors',
    'pollinators': 'Nature & Outdoors',
    'plant sale': 'Nature & Outdoors',
    'sustainability': 'Nature & Outdoors',

    # Religion & Spirituality
    'worship': 'Religion & Spirituality',
    'spirituality': 'Religion & Spirituality',
    'spiritual wellness': 'Religion & Spirituality',
    'religious/spiritual': 'Religion & Spirituality',
    'religious school': 'Religion & Spirituality',
    'all church events': 'Religion & Spirituality',
    'christian education': 'Religion & Spirituality',
    'fellowship': 'Religion & Spirituality',
    'small groups': 'Religion & Spirituality',
}

# --- Tier 2: Keyword regex patterns per bucket ---
# Order matters: first match wins. More specific patterns before general ones.

_PATTERNS = [
    ("Music & Concerts", re.compile(
        r'\b(concert|live music|music bingo|jazz|symphony|orchestra|choir|choral|'
        r'karaoke|open mic|acoustic|recital|opera\b|'
        r'blues|folk music|DJ\b|reggae|punk\b|metal\b|indie rock|bluegrass|'
        r'songwriter|musician|ensemble|quartet|trio|philharmonic|'
        r'hip[- ]?hop|beatbox|band\b)\b', re.I)),

    ("Sports & Fitness", re.compile(
        r'\b(soccer|football game|basketball|baseball|softball|tennis|golf\b|'
        r'swim|marathon|triathlon|5k\b|10k\b|hike\b|hiking|'
        r'bike ride|cycling|yoga|pilates|fitness|workout|zumba|qigong|tai chi|'
        r'martial art|karate|judo|boxing|wrestling|lacrosse|volleyball|'
        r'hockey|rugby|track and field|cross country|rowing|'
        r'athletic|tournament|championship|varsity|chess club)\b', re.I)),

    ("Arts & Culture", re.compile(
        r'\b(art\b|gallery|exhibit|museum|paint|sculpture|ceramic|pottery|'
        r'drawing|sketch|photography|photo show|film|cinema|movie|'
        r'theater|theatre|ballet|dance\b|dancing|'
        r'improv|comedy|stand[- ]?up|comedian|'
        r'poetry|poet\b|book club|book reading|author|literary|'
        r'craft|knit|crochet|sew|quilt|weav|fiber art|'
        r'mural|installation|performance|'
        r'salsa|bachata|swing dance|tango|ballroom|pastel)\b', re.I)),

    ("Education & Workshops", re.compile(
        r'\b(workshop|seminar|lecture|training|class\b|classes\b|'
        r'webinar|certification|clinic\b|'
        r'conference|summit|symposium|panel|'
        r'career fair|resume|professional development|STEM|'
        r'info session|orientation|ESL|english conversation|'
        r'tech help|computer skills|genealogy)\b', re.I)),

    ("Community & Social", re.compile(
        r'\b(town hall|community|meetup|meet[- ]up|potluck|picnic|'
        r'block party|festival|parade|celebration|carnival|'
        r'farmers.?market|flea market|swap meet|'
        r'volunteer|cleanup|clean[- ]up|'
        r'fundrais|benefit gala|auction|raffle|'
        r'trivia|board game|game night|intercambio)\b', re.I)),

    ("Family & Kids", re.compile(
        r'\b(storytime|story time|story hour|puppet|'
        r'trick.or.treat|easter egg hunt|petting zoo|'
        r'day camp|summer camp|scout|4-H|'
        r'bounce house|face painting|kids|baby village|'
        r'teen advisory|teen volunteer|toddler|preschool)\b', re.I)),

    ("Food & Drink", re.compile(
        r'\b(wine tasting|beer tasting|brew fest|tasting room|'
        r'dinner|brunch|food truck|cooking class|'
        r'culinary|chef\b|cocktail|distillery|'
        r'winery|taproom|pub crawl|happy hour|bake sale|'
        r'flight club|food fest)\b', re.I)),

    ("Health & Wellness", re.compile(
        r'\b(meditation|mindfulness|mental health|therapy|'
        r'support group|grief|recovery|sober|'
        r'nutrition|blood drive|blood pressure|'
        r'cancer|diabetes|alzheimer|dementia|'
        r'first aid|CPR|holistic|acupuncture|reiki|healing)\b', re.I)),

    ("Nature & Outdoors", re.compile(
        r'\b(garden|plant sale|tree planting|bird walk|birdwatch|birding|'
        r'wildlife|nature walk|nature hike|nature center|trail\b|'
        r'conservation|ecology|environmental|'
        r'farm tour|harvest|botanical|wildflower|stargazing)\b', re.I)),

    ("Religion & Spirituality", re.compile(
        r'\b(worship|prayer|bible study|scripture|sermon|'
        r'temple|mosque|synagogue|'
        r'interfaith|easter service|christmas service|'
        r'passover|ramadan|shabbat|lenten|advent|ministry)\b', re.I)),
]

# Tags to ignore — venue names, cities, metadata, not semantic categories
_IGNORE_TAGS = {
    'santa-rosa', 'san-rafael', 'bloomington', 'petaluma', 'toronto',
    'in-person', 'online', 'virtual', 'hybrid', 'free', 'free event',
    'featured', 'featured event', 'featured events', 'special event',
    'special events', 'all events', 'events', 'event', 'other',
    'general', 'general events', 'tickets', 'program', 'programs',
    'programs & events', 'main', 'front page', 'calendar of events',
    'weekend', 'friday', 'monthly', 'adults', 'seniors',
}

# Also ignore venue-specific tags (Toronto venues, etc.)
_VENUE_SUFFIXES = {
    '-bar', '-hall', '-theatre', '-theater', '-lounge', '-club',
    '-tavern', '-cinema', '-gallery', '-studio', '-church',
    '-centre', '-center', '-house', '-room', '-space',
}


def _is_ignorable_tag(tag):
    """Return True if a tag is metadata/venue, not a semantic category."""
    if tag in _IGNORE_TAGS:
        return True
    # Venue-like tags often end with venue suffixes
    for suffix in _VENUE_SUFFIXES:
        if tag.endswith(suffix):
            return True
    return False


def classify_from_ics_categories(ics_categories):
    """Tier 1: Map ICS CATEGORIES tags to a bucket.

    Args:
        ics_categories: list of category strings from the ICS CATEGORIES field

    Returns:
        bucket name or None
    """
    if not ics_categories:
        return None

    for tag in ics_categories:
        tag_lower = tag.strip().lower()

        if _is_ignorable_tag(tag_lower):
            continue
        if 'schemas.google.com' in tag_lower:
            continue

        # Exact match
        if tag_lower in ICS_CATEGORY_MAP:
            return ICS_CATEGORY_MAP[tag_lower]

        # Substring match for truncated tags (e.g., "exhi" → exhibition)
        for key, bucket in ICS_CATEGORY_MAP.items():
            if len(tag_lower) >= 4 and key.startswith(tag_lower):
                return bucket

    return None


def classify_from_text(title, description):
    """Tier 2: Keyword regex on title and description.

    Returns:
        (category, confidence) where confidence is "medium" (title match)
        or "low" (description-only match), or (None, None).
    """
    title = title or ''
    description = description or ''

    # Try title first (medium confidence)
    for cat_name, pattern in _PATTERNS:
        if pattern.search(title):
            return cat_name, 'medium'

    # Try description (low confidence)
    for cat_name, pattern in _PATTERNS:
        if pattern.search(description):
            return cat_name, 'low'

    return None, None


def classify_event(title, description, ics_categories=None, min_confidence='medium'):
    """Classify an event into one of 10 category buckets.

    Args:
        title: event title
        description: event description
        ics_categories: list of ICS CATEGORIES tag values (optional)
        min_confidence: minimum confidence to return a category.
            "high" = ICS categories only
            "medium" = ICS categories + title keyword match (default)
            "low" = all matches including description-only

    Returns:
        (category, confidence) tuple. Returns (None, None) if below threshold.
    """
    confidence_rank = {'high': 3, 'medium': 2, 'low': 1}
    min_rank = confidence_rank.get(min_confidence, 2)

    # Tier 1: ICS CATEGORIES
    bucket = classify_from_ics_categories(ics_categories)
    if bucket:
        return bucket, 'high'

    # Tier 2: keyword regex
    bucket, confidence = classify_from_text(title, description)
    if bucket and confidence_rank.get(confidence, 0) >= min_rank:
        return bucket, confidence

    return None, None
