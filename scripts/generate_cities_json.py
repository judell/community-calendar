#!/usr/bin/env python3
"""Generate cities.json from city.conf files.

Reads timezone (and optionally other config) from each city's city.conf
and writes a single cities.json manifest for the frontend.
"""

import json
from pathlib import Path

CITIES_DIR = Path(__file__).parent.parent / 'cities'


def main():
    cities = {}
    for conf in sorted(CITIES_DIR.glob('*/city.conf')):
        city = conf.parent.name
        tz = None
        for line in conf.read_text().splitlines():
            if line.startswith('# timezone:'):
                tz = line.split(':', 1)[1].strip()
        if tz:
            cities[city] = {'timezone': tz}

    out = CITIES_DIR.parent / 'cities.json'
    out.write_text(json.dumps(cities, indent=2) + '\n')
    print(f"Generated cities.json with {len(cities)} cities")


if __name__ == '__main__':
    main()
