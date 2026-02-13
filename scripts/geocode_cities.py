#!/usr/bin/env python3
"""
Geocode cities for geo-filtering.

Uses Nominatim (OpenStreetMap) for free geocoding.
Run once when setting up a new city to generate/update allowed_cities.txt.

Usage:
    # Geocode cities for a city's allowed list:
    python scripts/geocode_cities.py --city petaluma
    
    # Geocode with a specific center and radius:
    python scripts/geocode_cities.py --city petaluma --center "38.2324,-122.6367" --radius 25
    
    # Just validate existing config (no API calls):
    python scripts/geocode_cities.py --city petaluma --validate-only
"""

import argparse
import json
import time
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

import requests

CACHE_FILE = Path(__file__).parent.parent / '.geocode_cache.json'
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'


def load_cache():
    """Load geocoding cache."""
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save_cache(cache):
    """Save geocoding cache."""
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def geocode(city_name, state='CA', cache=None):
    """Geocode a city name to lat/lng using Nominatim."""
    if cache is None:
        cache = {}
    
    cache_key = f"{city_name}, {state}"
    if cache_key in cache:
        return cache[cache_key]
    
    # Rate limit: 1 request per second for Nominatim
    time.sleep(1.1)
    
    params = {
        'q': f"{city_name}, {state}, USA",
        'format': 'json',
        'limit': 1,
    }
    headers = {
        'User-Agent': 'CommunityCalendar/1.0 (event aggregator)'
    }
    
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data:
            lat = float(data[0]['lat'])
            lng = float(data[0]['lon'])
            cache[cache_key] = {'lat': lat, 'lng': lng}
            save_cache(cache)
            return cache[cache_key]
    except Exception as e:
        print(f"  Warning: Failed to geocode '{city_name}': {e}")
    
    return None


def haversine(lat1, lng1, lat2, lng2):
    """Calculate distance in miles between two lat/lng points."""
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    miles = 3956 * c  # Earth radius in miles
    return miles


def parse_allowed_cities_file(filepath):
    """Parse allowed_cities.txt and extract config."""
    config = {
        'center': None,
        'radius': None,
        'state': 'CA',
        'cities': []
    }
    
    for line in filepath.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('# center:'):
            parts = line.split(':', 1)[1].strip().split(',')
            config['center'] = (float(parts[0].strip()), float(parts[1].strip()))
        elif line.startswith('# radius:'):
            config['radius'] = float(line.split(':', 1)[1].strip())
        elif line.startswith('# state:'):
            config['state'] = line.split(':', 1)[1].strip()
        elif not line.startswith('#'):
            # Strip trailing comment from city name
            city = line.split('#')[0].strip()
            if city:
                config['cities'].append(city)
    
    return config


def write_allowed_cities_file(filepath, config, city_coords):
    """Write allowed_cities.txt with config header."""
    lines = [
        f"# center: {config['center'][0]}, {config['center'][1]}",
        f"# radius: {config['radius']}",
        f"# state: {config['state']}",
        "#",
        "# Cities within radius (auto-generated coordinates):",
    ]
    
    center_lat, center_lng = config['center']
    
    for city in sorted(config['cities']):
        coords = city_coords.get(city)
        if coords:
            dist = haversine(center_lat, center_lng, coords['lat'], coords['lng'])
            if dist <= config['radius']:
                lines.append(f"{city}  # {coords['lat']:.4f}, {coords['lng']:.4f} ({dist:.1f} mi)")
            else:
                lines.append(f"{city}  # {coords['lat']:.4f}, {coords['lng']:.4f} ({dist:.1f} mi) ⚠️ OUTSIDE RADIUS")
        else:
            lines.append(f"{city}  # (coordinates unknown)")
    
    filepath.write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Geocode cities for geo-filtering')
    parser.add_argument('--city', required=True, help='City directory name (e.g., petaluma)')
    parser.add_argument('--center', help='Center coordinates as "lat,lng"')
    parser.add_argument('--radius', type=float, help='Radius in miles')
    parser.add_argument('--state', default='CA', help='State abbreviation (default: CA)')
    parser.add_argument('--validate-only', action='store_true', help='Just validate, no geocoding')
    
    args = parser.parse_args()
    
    city_dir = Path(__file__).parent.parent / 'cities' / args.city
    allowed_file = city_dir / 'allowed_cities.txt'
    
    if not allowed_file.exists():
        print(f"Error: {allowed_file} does not exist")
        print(f"Create it first with a list of cities to allow")
        return 1
    
    # Parse existing file
    config = parse_allowed_cities_file(allowed_file)
    
    # Override with command line args
    if args.center:
        parts = args.center.split(',')
        config['center'] = (float(parts[0].strip()), float(parts[1].strip()))
    if args.radius:
        config['radius'] = args.radius
    if args.state:
        config['state'] = args.state
    
    if not config['center']:
        print("Error: No center defined. Use --center or add '# center: lat, lng' to file")
        return 1
    if not config['radius']:
        print("Error: No radius defined. Use --radius or add '# radius: N' to file")
        return 1
    
    print(f"Center: {config['center']}")
    print(f"Radius: {config['radius']} miles")
    print(f"State: {config['state']}")
    print(f"Cities: {len(config['cities'])}")
    print()
    
    # Load geocoding cache
    cache = load_cache()
    city_coords = {}
    
    # Geocode cities
    for city in config['cities']:
        cache_key = f"{city}, {config['state']}"
        if cache_key in cache:
            city_coords[city] = cache[cache_key]
            status = "cached"
        elif args.validate_only:
            status = "skipped (validate-only)"
        else:
            print(f"  Geocoding {city}...", end=' ', flush=True)
            coords = geocode(city, config['state'], cache)
            if coords:
                city_coords[city] = coords
                status = f"OK ({coords['lat']:.4f}, {coords['lng']:.4f})"
            else:
                status = "FAILED"
            print(status)
    
    # Report distances
    print()
    print("Distance report:")
    center_lat, center_lng = config['center']
    outside_count = 0
    
    for city in sorted(config['cities']):
        coords = city_coords.get(city)
        if coords:
            dist = haversine(center_lat, center_lng, coords['lat'], coords['lng'])
            flag = ""
            if dist > config['radius']:
                flag = " ⚠️  OUTSIDE RADIUS"
                outside_count += 1
            print(f"  {city}: {dist:.1f} mi{flag}")
        else:
            print(f"  {city}: (no coordinates)")
    
    if outside_count > 0:
        print(f"\n⚠️  {outside_count} cities are outside the {config['radius']} mile radius")
        print("   They will still be allowed but this may indicate a config issue.")
    
    # Update file with coordinates
    if not args.validate_only:
        write_allowed_cities_file(allowed_file, config, city_coords)
        print(f"\nUpdated {allowed_file}")
    
    return 0


if __name__ == '__main__':
    exit(main())
