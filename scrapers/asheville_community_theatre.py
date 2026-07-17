#!/usr/bin/env python3
"""
Scraper for Asheville Community Theatre (ashevilletheatre.org).

ACT (35 E Walnut St; stages: Mainstage, 35below) runs WordPress with the
My Calendar plugin, but all My Calendar API/ICS endpoints 404 and the
REST `mc_event` list carries no event dates (meta is null). Show pages
server-render the run info instead:

    <h4 class="event-short-desc">August 21-30, 2026</h4>
    <p>Location: 35below</p>
    <p>Fridays and Saturdays at 8:00 PM & 10:00 PM, Sundays at 2:00 PM & 4:00 PM</p>

Observed h4 variants:
    "August 21-30, 2026"                          (run range)
    "December 4 - 20, 2026"                       (run range, spaced dash)
    "September 25 – October 11, 2026"             (cross-month range)
    "Saturday, July 18, 2026 at 8:00 PM & 10:00 PM"  (explicit date + times)
    "Saturday April 25, 2026 at 10:30 AM"         (no comma after weekday)
    "Friday & Saturday, January 9 & 10, 2026 at 8:00 PM"  (multi-date list)
    "8PM Friday, November 21 & Saturday, November 22"  (time-first, no year)

Range shows carry showtimes either as weekly prose ("Fridays and Saturdays
at 8:00 PM & 10:00 PM, Sundays at 2:00 PM & 4:00 PM") or as an explicit
dated list ("Friday, August 7, 2026 at 7:30 PM Saturday, August 8, ...").

Strategy: REST mc_event list -> fetch each show page -> parse the h4 run
line. Ranges are EXPANDED to individual performances using the showtime
prose (day-of-week + times clauses); when the prose can't be parsed, fall
back to a single all-day event spanning the run. Explicit-date h4s emit
one event per date x time. Shows with no parseable dates are logged and
skipped rather than emitting wrong dates.

Usage:
    python scrapers/asheville_community_theatre.py \
        --output cities/asheville/asheville_community_theatre.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REST_URL = ("https://ashevilletheatre.org/wp-json/wp/v2/mc_event"
            "?per_page=100&_fields=link,title")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
}

TZ = ZoneInfo("America/New_York")
ADDRESS = "35 E Walnut St, Asheville, NC 28801"

MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
               'August', 'September', 'October', 'November', 'December']
MONTHS = {m.lower(): i for i, m in enumerate(MONTH_NAMES, start=1)}
MONTH_RE = '|'.join(MONTH_NAMES)

WEEKDAYS = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6}

DASH = r'[-–—]'  # hyphen, en dash, em dash

# "August 21-30, 2026" / "December 4 - 20, 2026" / "September 25 – October 11, 2026"
RANGE_RE = re.compile(
    rf'({MONTH_RE})\s+(\d{{1,2}})\s*{DASH}\s*(?:({MONTH_RE})\s+)?(\d{{1,2}}),?\s*(\d{{4}})',
    re.IGNORECASE
)

# "Saturday, July 18, 2026 at 8:00 PM & 10:00 PM" /
# "Friday & Saturday, January 9 & 10, 2026 at 8:00 PM"
EXPLICIT_RE = re.compile(
    rf'({MONTH_RE})\s+(\d{{1,2}}(?:\s*(?:&|,|and)\s*\d{{1,2}})*)\s*,?\s*(\d{{4}})\s+at\s+(.+)',
    re.IGNORECASE
)

DAY_TOKEN_RE = re.compile(
    r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)s?\b', re.IGNORECASE)
TIME_TOKEN_RE = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?\b', re.IGNORECASE)

# One fully-dated performance: "Friday, August 7, 2026 at 7:30 PM"
DATED_PERF_RE = re.compile(
    rf'({MONTH_RE})\s+(\d{{1,2}}),\s*(\d{{4}})\s+at\s+(\d{{1,2}})(?::(\d{{2}}))?\s*([AP])\.?M\.?',
    re.IGNORECASE
)

# Year-less date: "November 21"
MONTH_DAY_RE = re.compile(rf'({MONTH_RE})\s+(\d{{1,2}})\b', re.IGNORECASE)


def _time_to_hm(hh: str, mm: Optional[str], ap: str) -> tuple[int, int]:
    hour = int(hh) % 12
    if ap.lower() == 'p':
        hour += 12
    return hour, int(mm) if mm else 0


def _parse_showtime_clauses(text: str) -> list[tuple[list[int], list[tuple[int, int]]]]:
    """
    Parse showtime prose like "Fridays and Saturdays at 8:00 PM & 10:00 PM,
    Sundays at 2:00 PM & 4:00 PM" or "Friday & Saturday 10:00 AM, 12:30 PM,
    & 3:00 PM" into clauses of (weekday numbers, (hour, minute) times).

    Works by tokenizing day names and times in order, then grouping each
    maximal run of days with the following run of times. Returns [] when
    the text doesn't form complete clauses.
    """
    tokens = []
    for m in DAY_TOKEN_RE.finditer(text):
        tokens.append((m.start(), 'day', WEEKDAYS[m.group(1).lower()]))
    for m in TIME_TOKEN_RE.finditer(text):
        tokens.append((m.start(), 'time', _time_to_hm(m.group(1), m.group(2), m.group(3))))
    tokens.sort()

    clauses = []
    days: list[int] = []
    times: list[tuple[int, int]] = []
    for _, kind, val in tokens:
        if kind == 'day':
            if times:  # a new day run closes the previous clause
                clauses.append((days, times))
                days, times = [], []
            if val not in days:
                days.append(val)
        else:
            if not days:
                return []  # time with no preceding days: not showtime prose
            if val not in times:
                times.append(val)
    if days and times:
        clauses.append((days, times))
    elif days:
        return []  # trailing days without times: incomplete
    return clauses


class AshevilleCommunityTheatreScraper(BaseScraper):
    """Scraper for ACT show pages (My Calendar, dates in server-rendered prose)."""

    name = "Asheville Community Theatre"
    domain = "ashevilletheatre.org"
    timezone = "America/New_York"

    def _fetch_page(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _list_shows(self) -> list[dict[str, str]]:
        content = self._fetch_page(REST_URL)
        if not content:
            self.logger.error("Could not fetch mc_event REST list")
            return []
        try:
            posts = json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Bad JSON from REST list: {e}")
            return []
        shows = []
        for p in posts:
            link = p.get('link', '')
            title = html_mod.unescape(p.get('title', {}).get('rendered', '')).strip()
            if link and title:
                shows.append({'link': link, 'title': title})
        self.logger.info(f"REST list: {len(shows)} shows")
        return shows

    def _location(self, stage: str) -> str:
        if stage:
            return f"Asheville Community Theatre ({stage}), {ADDRESS}"
        return f"Asheville Community Theatre, {ADDRESS}"

    def _parse_show(self, show: dict[str, str]) -> list[dict[str, Any]]:
        url, title = show['link'], show['title']
        html = self._fetch_page(url)
        if not html:
            return []

        # Scope to the show's entry-content to avoid box-office hours,
        # sidebar season lists, etc.
        m = re.search(r'<div class="entry-content">(.*?)</article>', html, re.DOTALL)
        content = m.group(1) if m else html

        h4m = re.search(r'class="event-short-desc"[^>]*>(.*?)</h4>', content, re.DOTALL)
        h4 = ''
        if h4m:
            h4 = html_mod.unescape(re.sub(r'<[^>]+>', '', h4m.group(1))).strip()
        if not h4:
            self.logger.info(f"Skipping {title!r}: no run-date line found ({url})")
            return []

        # Stage / location
        stage = ''
        lm = re.search(r'Location:\s*([^<|]+)', html_mod.unescape(re.sub(r'<[^>]+>', '|', content)))
        if lm:
            raw = lm.group(1).strip()
            if '35below' in raw.lower().replace(' ', ''):
                stage = '35below'
            elif 'mainstage' in raw.lower():
                stage = 'Mainstage'
            else:
                stage = raw
        location = self._location(stage)

        now = datetime.now(TZ)
        today = now.date()

        # --- Variant 1: run range, expand via showtime prose ---
        rm = RANGE_RE.search(h4)
        if rm:
            mon1, d1, mon2, d2, year = rm.groups()
            year = int(year)
            m1 = MONTHS[mon1.lower()]
            m2 = MONTHS[mon2.lower()] if mon2 else m1
            try:
                start_d = date(year, m1, int(d1))
                end_d = date(year, m2, int(d2))
            except ValueError:
                self.logger.warning(f"Skipping {title!r}: bad range {h4!r} ({url})")
                return []
            if end_d < start_d or (end_d - start_d).days > 90:
                self.logger.warning(f"Skipping {title!r}: implausible range {h4!r} ({url})")
                return []

            # Find the first paragraph that parses as pure showtime prose
            # (day names + times, no explicit dates — excludes PWYC/ASL notes).
            clauses = []
            prose = ''
            for pm in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL):
                text = html_mod.unescape(re.sub(r'<[^>]+>', ' ', pm.group(1)))
                text = re.sub(r'\s+', ' ', text).strip()
                if not text or len(text) > 250:
                    continue
                if re.search(r'\d{4}', text) or re.search(MONTH_RE, text, re.IGNORECASE):
                    continue  # contains explicit dates → not the schedule line
                got = _parse_showtime_clauses(text)
                if got:
                    clauses, prose = got, text
                    break

            desc = f"{title} at Asheville Community Theatre" + (f" ({stage})" if stage else "")
            desc += f". {h4}." + (f" {prose}" if prose else "")

            if not clauses:
                # Second chance: an explicit dated performance list, e.g.
                # "Friday, August 7, 2026 at 7:30 PM Saturday, August 8, ...".
                # Require >=3 dated entries in one paragraph so PWYC/ASL
                # single-date notes don't qualify.
                for pm in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL):
                    text = html_mod.unescape(re.sub(r'<[^>]+>', ' ', pm.group(1)))
                    matches = DATED_PERF_RE.findall(text)
                    if len(matches) < 3:
                        continue
                    events = []
                    for mon, d, yr, hh, mm, ap in matches:
                        hour, minute = _time_to_hm(hh, mm or None, ap)
                        try:
                            dtstart = datetime(int(yr), MONTHS[mon.lower()], int(d),
                                               hour, minute, tzinfo=TZ)
                        except ValueError:
                            self.logger.warning(f"Bad dated performance in list ({url})")
                            continue
                        if dtstart < now:
                            continue
                        events.append({
                            'title': title,
                            'dtstart': dtstart,
                            'dtend': dtstart + timedelta(hours=2),
                            'location': location,
                            'description': desc,
                            'url': url,
                        })
                    return events

            if not clauses:
                # Fallback: one all-day event spanning the run
                if end_d < today:
                    return []
                self.logger.info(f"{title!r}: no parseable showtimes; "
                                 f"emitting all-day run span {h4!r} ({url})")
                return [{
                    'title': title,
                    'dtstart': max(start_d, today),
                    'dtend': end_d + timedelta(days=1),
                    'location': location,
                    'description': desc,
                    'url': url,
                }]

            events = []
            day = start_d
            while day <= end_d:
                for days_of_week, times in clauses:
                    if day.weekday() in days_of_week:
                        for hour, minute in times:
                            dtstart = datetime(day.year, day.month, day.day,
                                               hour, minute, tzinfo=TZ)
                            if dtstart < now:
                                continue
                            events.append({
                                'title': title,
                                'dtstart': dtstart,
                                'dtend': dtstart + timedelta(hours=2),
                                'location': location,
                                'description': desc,
                                'url': url,
                            })
                day += timedelta(days=1)
            return events

        # --- Variant 2: explicit date(s) + times ---
        em = EXPLICIT_RE.search(h4)
        if em:
            mon, day_list, year, times_str = em.groups()
            month = MONTHS[mon.lower()]
            year = int(year)
            day_nums = [int(d) for d in re.findall(r'\d{1,2}', day_list)]
            times = [_time_to_hm(t.group(1), t.group(2), t.group(3))
                     for t in TIME_TOKEN_RE.finditer(times_str)]
            if not times:
                self.logger.warning(f"Skipping {title!r}: no times in {h4!r} ({url})")
                return []
            events = []
            for d in day_nums:
                for hour, minute in times:
                    try:
                        dtstart = datetime(year, month, d, hour, minute, tzinfo=TZ)
                    except ValueError:
                        self.logger.warning(f"Bad date in {h4!r} ({url})")
                        continue
                    if dtstart < now:
                        continue
                    desc = (f"{title} at Asheville Community Theatre"
                            + (f" ({stage})" if stage else "") + f". {h4}.")
                    events.append({
                        'title': title,
                        'dtstart': dtstart,
                        'dtend': dtstart + timedelta(hours=2),
                        'location': location,
                        'description': desc,
                        'url': url,
                    })
            return events

        # --- Variant 3: year-less date list with time(s), e.g.
        # "8PM Friday, November 21 & Saturday, November 22" ---
        if not re.search(r'\d{4}', h4):
            md_pairs = MONTH_DAY_RE.findall(h4)
            times = [_time_to_hm(t.group(1), t.group(2), t.group(3))
                     for t in TIME_TOKEN_RE.finditer(h4)]
            if md_pairs and times:
                events = []
                for mon, d in md_pairs:
                    month, dnum = MONTHS[mon.lower()], int(d)
                    year = today.year
                    try:
                        if date(year, month, dnum) < today:
                            year += 1  # no year given and date passed: assume next year
                        for hour, minute in times:
                            dtstart = datetime(year, month, dnum, hour, minute, tzinfo=TZ)
                            if dtstart < now:
                                continue
                            desc = (f"{title} at Asheville Community Theatre"
                                    + (f" ({stage})" if stage else "") + f". {h4}.")
                            events.append({
                                'title': title,
                                'dtstart': dtstart,
                                'dtend': dtstart + timedelta(hours=2),
                                'location': location,
                                'description': desc,
                                'url': url,
                            })
                    except ValueError:
                        self.logger.warning(f"Bad year-less date in {h4!r} ({url})")
                return events

        self.logger.info(f"Skipping {title!r}: unparseable run line {h4!r} ({url})")
        return []

    def fetch_events(self) -> list[dict[str, Any]]:
        shows = self._list_shows()
        if not shows:
            return []

        self.logger.info(f"Fetching {len(shows)} show pages (parallel)...")
        all_events = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self._parse_show, s): s['link'] for s in shows}
            for future in as_completed(futures):
                all_events.extend(future.result())

        self.logger.info(f"Got {len(all_events)} future performances")
        return all_events


def main():
    parser = argparse.ArgumentParser(description="Scrape Asheville Community Theatre shows")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = AshevilleCommunityTheatreScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
