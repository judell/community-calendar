#!/usr/bin/env python3
"""
Combine multiple ICS files into a single subscribable calendar feed.
Filters to only include events from today forward.
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

# Map filenames to friendly source names
SOURCE_NAMES = {
    'arlene_francis_theater': 'Arlene Francis Center',
    'luther_burbank_center': 'Luther Burbank Center',
    'schulz_museum': 'Charles M. Schulz Museum',
    'sonoma_com': 'Sonoma.com',
    'golocal_coop': 'GoLocal Cooperative',
    'sonoma_county_aa': 'Sonoma County AA',
    'sonoma_county_dsa': 'Sonoma County DSA',
    'museumsc': 'Museum of Sonoma County',
    'library_intercept': 'Sonoma County Library',
    'sonoma_county_gov': 'Sonoma County Government',
    'sonoma_parks': 'Sonoma County Parks',
    'cal_theatre': 'Cal Theatre',
    'copperfields': "Copperfield's Books",
    'bohemian': 'North Bay Bohemian',
    'eventbrite': 'Eventbrite',
    'pressdemocrat': 'Press Democrat',
    # Meetup groups - Santa Rosa
    'meetup_go_wild_hikers': 'Meetup: Go Wild Hikers',
    'meetup_shutupandwrite': 'Meetup: Shut Up & Write Wine Country',
    'meetup_scottish_dancing': 'Meetup: Scottish Country Dancing',
    'meetup_womens_wine_club': 'Meetup: Women\'s Wine Club',
    'meetup_toastmasters': 'Meetup: Santa Rosa Toastmasters',
    'meetup_yoga': 'Meetup: Nataraja Yoga',
    'meetup_creativity': 'Meetup: Women\'s Creativity Collective',
    'meetup_boomers': 'Meetup: Sonoma County Boomers',
    # Meetup groups - Davis
    'meetup_mosaics': 'Meetup: Mosaics',
    'meetup_intercultural': 'Meetup: Intercultural Mosaics',
    'meetup_board_games': 'Meetup: Yolo Board Game Gathering',
    'meetup_pence_art': 'Meetup: Pence Art Programs',
    'meetup_art_in_action': 'Meetup: Art in Action',
    'meetup_mindful': 'Meetup: Mindful Embodied Spirituality',
    'meetup_winters_write': 'Meetup: Winters Shut Up & Write',
    'SRCity': 'City of Santa Rosa',
    'srcc': 'Santa Rosa Cycling Club',
    'cafefrida': 'Cafe Frida',
    'barrel_proof': 'Barrel Proof Lounge',
    'sportsbasement': 'Sports Basement',
    'sebastopol_community': 'Sebastopol Community Center',
    'redwood_cafe': 'Redwood Cafe',
    'sebarts': 'Sebastopol Center for the Arts',
    'occidental_arts': 'Occidental Arts & Ecology Center',
    'svma': 'Sonoma Valley Museum of Art',
    'sonoma_city': 'City of Sonoma',
    'bgc_bloomington': 'Boys & Girls Club Bloomington',
    'bloomington_gov': 'City of Bloomington',
    'bloomington_arts': 'Bloomington Arts',
    'bluebird': 'The Bluebird',
    'iu_jacobs_music': 'IU Jacobs School of Music',
    'iu_auditorium': 'IU Auditorium',
    'iu_eskenazi_museum': 'Eskenazi Museum of Art',
    'bsquare_government': 'Bloomington Government',
    'bsquare_misc_civic': 'Bloomington Civic Events',
    'bsquare_critical_mass': 'Critical Mass Bloomington',
    'bsquare_bptc': 'Bloomington Public Transit',
    # Petaluma
    'petaluma_downtown': 'Petaluma Downtown Association',
    'meetup_mindful_petaluma': 'Meetup: Mindful Petaluma',
    'meetup_rebel_craft': 'Meetup: Rebel Craft Collective',
    'meetup_candlelight_yoga': 'Meetup: Candlelight Yoga Petaluma',
    'meetup_figure_drawing': 'Meetup: Petaluma Figure Drawing',
    'meetup_brat_pack': 'Meetup: Sonoma-Marin Brat Pack',
    'aqus_community': 'Aqus Community',
    'mystic_theatre': 'Mystic Theatre',
    'maxpreps_petaluma_high': 'Petaluma High School Athletics',
    'maxpreps_casa_grande': 'Casa Grande High School Athletics',
    'petaluma_chamber': 'Petaluma Chamber of Commerce',
    'meetup_petaluma_salon': 'Meetup: Petaluma Salon',
    'meetup_book_brew': 'Meetup: Petaluma Book & Brew Club',
    'meetup_active_20_30': 'Meetup: Petaluma Active 20-30',
    'srjc_petaluma': 'SRJC Petaluma Campus',
    'bigeasy': 'The Big Easy',
    'polly_klaas': 'Polly Klaas Community Theater',
    'brooksnote': 'Brooks Note Winery',
    # Santa Rosa - local arts/community
    'santa_rosa_arts_center': 'Santa Rosa Arts Center',
    'movingwriting': 'MovingWriting',
}

# Fallback URLs for sources that don't provide event URLs
SOURCE_URLS = {
    'arlene_francis_theater': 'https://arlenefranciscenter.org/calendar/',
    'luther_burbank_center': 'https://lutherburbankcenter.org/events/',
    'schulz_museum': 'https://schulzmuseum.org/events/',
    'sonoma_com': 'https://www.sonoma.com/events/',
    'golocal_coop': 'https://golocal.coop/events/',
    'sonoma_county_aa': 'https://sonomacountyaa.org/events/',
    'sonoma_county_dsa': 'https://dsasonomacounty.org/events/',
    'library_intercept': 'https://sonomalibrary.org/events',
    'sonoma_county_gov': 'https://sonomacounty.ca.gov/calendar/',
    'sonoma_parks': 'https://parks.sonomacounty.ca.gov/events/',
    'cal_theatre': 'https://www.facebook.com/CalTheatrePT/',
    'copperfields': 'https://www.copperfieldsbooks.com/events',
    'SRCity': 'https://srcity.org/calendar.aspx',
    'iu_jacobs_music': 'https://events.iu.edu/musiciub/',
    'iu_auditorium': 'https://events.iu.edu/iu-auditorium/',
    'iu_eskenazi_museum': 'https://events.iu.edu/artmuseum/',
    'bsquare_government': 'https://bloomington.in.gov/',
    'bsquare_misc_civic': 'https://bsquarebulletin.com/b-there-or-b-square/',
    'bsquare_critical_mass': 'https://bsquarebulletin.com/b-there-or-b-square/',
    'bsquare_bptc': 'https://bloomingtontransit.com/',
    'santa_rosa_arts_center': 'https://santarosaartscenter.org/events/',
    'movingwriting': 'https://www.movingwriting.com/workshops',
    'bigeasy': 'https://bigeasypetaluma.com/events/',
    'polly_klaas': 'https://pollyklaastheater.org/events/',
    'brooksnote': 'https://brooksnotewinery.com/event-calendar/',
}


def load_allowed_cities(input_dir):
    """Load allowed cities from city directory if file exists."""
    cities_file = Path(input_dir) / 'allowed_cities.txt'
    if not cities_file.exists():
        return None
    
    cities = set()
    for line in cities_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            # Strip trailing comment (e.g., "Petaluma  # 38.23, -122.63 (0.0 mi)")
            city = line.split('#')[0].strip().lower()
            if city:
                cities.add(city)
    return cities


# Locations that should always be allowed (virtual events, etc.)
VIRTUAL_LOCATION_PATTERNS = [
    'zoom',
    'online',
    'virtual',
    'webinar',
    'http://',
    'https://',
    'america/los_angeles',  # Malformed Meetup timezone-as-location
    'america/new_york',
]

# Patterns that indicate location is a real address (worth geo-filtering)
# If none of these match, we skip geo-filtering for that event
ADDRESS_INDICATORS = re.compile(
    r'(?:'
    r', [A-Z]{2}\b|'              # State abbreviation: ", CA"
    r'\b\d{5}\b|'                 # ZIP code
    r', [A-Z][a-z]+ [A-Z]{2}|'     # City, State: ", Santa Rosa CA"
    r'\d+\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|lane|ln|way|court|ct)\b'  # Street address: "123 Main St"
    r')',
    re.IGNORECASE
)


def location_matches_allowed_cities(location, allowed_cities):
    """Check if a location string contains any allowed city name.
    
    Only applies geo-filter to locations that look like real addresses.
    Venue-only names ("Theater", "BiblioBus") are allowed through.
    """
    if not allowed_cities:
        return True  # No filter configured
    if not location:
        return True  # No location to check, allow it
    
    location_lower = location.lower()
    
    # Always allow virtual/online events
    for pattern in VIRTUAL_LOCATION_PATTERNS:
        if pattern in location_lower:
            return True
    
    # Check if location looks like an address
    # If not, allow it through (venue name only, no geo info to filter on)
    if not ADDRESS_INDICATORS.search(location):
        return True
    
    # Location has address info - check against allowed cities
    for city in allowed_cities:
        if city in location_lower:
            return True
    return False


def get_source_name(filename):
    """Get friendly source name from filename."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return 'City of Santa Rosa'
    return SOURCE_NAMES.get(stem, stem.replace('_', ' ').title())


def get_fallback_url(filename):
    """Get fallback URL for a source."""
    stem = Path(filename).stem
    if stem.startswith('SRCity_'):
        return SOURCE_URLS.get('SRCity')
    return SOURCE_URLS.get(stem)


def parse_ics_datetime(dt_str):
    """Parse an ICS datetime string to a datetime object."""
    if ';' in dt_str:
        dt_str = dt_str.split(':')[-1]
    
    dt_str = dt_str.strip()
    
    try:
        if dt_str.endswith('Z'):
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        elif 'T' in dt_str:
            return datetime.strptime(dt_str, '%Y%m%dT%H%M%S')
        else:
            return datetime.strptime(dt_str, '%Y%m%d')
    except ValueError:
        return None


def extract_events(ics_content, source_name=None, fallback_url=None):
    """Extract VEVENT blocks from ICS content."""
    events = []

    pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
    matches = re.findall(pattern, ics_content, re.DOTALL)

    for event_content in matches:
        dtstart_match = re.search(r'DTSTART[^:]*:([^\r\n]+)', event_content)
        if dtstart_match:
            dt = parse_ics_datetime(dtstart_match.group(1))
            if dt:
                # Add fallback URL if no URL exists
                if fallback_url and 'URL:' not in event_content:
                    event_content = f'URL:{fallback_url}\r\n{event_content}'

                # Add or update source in description
                if source_name:
                    # Check if DESCRIPTION exists
                    desc_match = re.search(r'DESCRIPTION:([^\r\n]*(?:\r?\n [^\r\n]*)*)', event_content)
                    source_line = f'Source: {source_name}'
                    
                    if desc_match:
                        old_desc = desc_match.group(1)
                        # Don't add if source already mentioned
                        if 'Source:' not in old_desc:
                            new_desc = old_desc.rstrip() + '\\n\\n' + source_line
                            event_content = event_content.replace(
                                f'DESCRIPTION:{old_desc}',
                                f'DESCRIPTION:{new_desc}'
                            )
                    else:
                        # Add DESCRIPTION with source
                        event_content = f'DESCRIPTION:{source_line}\r\n{event_content}'
                    
                    # Also add X-SOURCE header
                    if 'X-SOURCE' not in event_content:
                        event_content = f'X-SOURCE:{source_name}\r\n{event_content}'
                
                events.append({
                    'dtstart': dt,
                    'content': event_content
                })
    
    return events


def combine_ics_files(input_dir, output_file, calendar_name="Combined Calendar"):
    """Combine all ICS files in a directory into one."""
    all_events = []
    geo_filtered_count = 0
    # Use 24 hours ago to avoid filtering out same-day events due to timezone differences
    from datetime import timedelta
    now = datetime.now(timezone.utc) - timedelta(hours=24)
    
    # Load allowed cities for geo filtering
    allowed_cities = load_allowed_cities(input_dir)
    if allowed_cities:
        print(f"  Geo filter active: {len(allowed_cities)} allowed cities")
    
    ics_dir = Path(input_dir)
    for ics_file in sorted(ics_dir.glob('*.ics')):
        # Skip the output file if it exists
        if ics_file.name == Path(output_file).name:
            continue
            
        try:
            content = ics_file.read_text(encoding='utf-8', errors='ignore')
            source_name = get_source_name(ics_file.name)
            fallback_url = get_fallback_url(ics_file.name)
            events = extract_events(content, source_name, fallback_url)
            
            # Filter to future events only
            future_events = [e for e in events if e['dtstart'].replace(tzinfo=timezone.utc) >= now]
            
            # Apply geo filter if configured
            if allowed_cities:
                filtered_events = []
                for e in future_events:
                    # Handle ICS line folding (continuation lines start with space/tab)
                    # Use ^LOCATION to avoid matching X-LIC-LOCATION
                    location_match = re.search(r'^LOCATION:([^\n]+(?:\n[ \t][^\n]+)*)', e['content'], re.MULTILINE)
                    if location_match:
                        # Unfold: remove newline+space/tab
                        location = re.sub(r'\n[ \t]', '', location_match.group(1))
                    else:
                        location = ''
                    if location_matches_allowed_cities(location, allowed_cities):
                        filtered_events.append(e)
                    else:
                        geo_filtered_count += 1
                future_events = filtered_events
            
            all_events.extend(future_events)
            
            if future_events:
                print(f"  {len(future_events):4d} future events from {ics_file.name} ({source_name})")
        except Exception as e:
            print(f"  Error processing {ics_file.name}: {e}")
    
    # Sort by start time
    def normalize_dt(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    all_events.sort(key=lambda x: normalize_dt(x['dtstart']))
    
    # Remove duplicates based on UID
    seen_uids = set()
    unique_events = []
    for event in all_events:
        uid_match = re.search(r'UID:([^\r\n]+)', event['content'])
        if uid_match:
            uid = uid_match.group(1)
            if uid not in seen_uids:
                seen_uids.add(uid)
                unique_events.append(event)
        else:
            unique_events.append(event)
    
    # Build combined ICS
    output = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Community Calendar//Combined Feed//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        f'X-WR-CALNAME:{calendar_name}',
        'REFRESH-INTERVAL;VALUE=DURATION:PT1H',
        'X-PUBLISHED-TTL:PT1H',
    ]
    
    for event in unique_events:
        output.append('BEGIN:VEVENT')
        output.append(event['content'])
        output.append('END:VEVENT')
    
    output.append('END:VCALENDAR')
    
    Path(output_file).write_text('\r\n'.join(output), encoding='utf-8')
    
    if geo_filtered_count > 0:
        print(f"  (Geo-filtered {geo_filtered_count} events outside allowed cities)")
    print(f"\nCombined {len(unique_events)} unique future events into {output_file}")
    return len(unique_events)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine ICS files into a single feed')
    parser.add_argument('--input-dir', '-i', required=True, help='Directory containing ICS files')
    parser.add_argument('--output', '-o', required=True, help='Output ICS file')
    parser.add_argument('--name', '-n', default='Community Calendar', help='Calendar name')
    
    args = parser.parse_args()
    
    print(f"Combining ICS files from {args.input_dir}...")
    combine_ics_files(args.input_dir, args.output, args.name)
