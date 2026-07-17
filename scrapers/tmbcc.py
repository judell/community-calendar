#!/usr/bin/env python3
"""
Scraper for the Tibetan Mongolian Buddhist Cultural Center (tmbcc.org),
3655 Snoddy Rd, Bloomington IN.

WordPress site; mod_security blocks ?ical=1 and there is no events plugin.
Events (retreats, LOSAR celebrations, the Summer Prayer Festival, etc.)
are announced as ordinary BLOG POSTS whose bodies are usually just poster
images — so the event date must be parsed from the post TITLE (with the
post body text scanned as a fallback).

Date patterns handled:
    "Sept. 8th-20th"                  (day range)
    "May 28th, 29th, & 30th"          (day list -> one spanning event)
    "August 8th, 9th & 10th"
    "April 19 & 20th, 2025"           (explicit year)
    "March 1st"                       (single day)
    "Sept 30 - Oct 2"                 (cross-month range)
    "Saturday, July 26 at 10am"       (with time)

The RSS pubDate / wp-json post date is the PUBLISH date, never the event
date. It is only used to infer the year when the title carries none:
announcements precede events, so the event year is the publish year unless
that would put the event well before the publish date, in which case it
rolls to the next year. Posts with no confidently parseable future date
are logged and skipped — precision over recall.

Primary source is the wp-json posts API (bypasses mod_security); the RSS
feed at /feed/ is the fallback. Multi-day retreats become one spanning
event. Untimed events default to a 9:00 AM start (5:00 PM end on the last
day) — dates are never guessed, but a daytime default hour is applied.

Usage:
    python scrapers/tmbcc.py --output cities/bloomington/tmbcc.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import argparse
import html as html_mod
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from lib.base import BaseScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8',
}

WP_JSON_URL = 'https://tmbcc.org/wp-json/wp/v2/posts?per_page=30&_fields=date,link,title,content'
RSS_URL = 'https://tmbcc.org/feed/'

DEFAULT_LOCATION = 'Tibetan Mongolian Buddhist Cultural Center, 3655 Snoddy Rd, Bloomington, IN 47401'

MONTHS = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}

MONTH_PAT = (
    r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|'
    r'Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
)
# Month followed by a day number — a bare month word ("may", "march") never
# counts as a date without one.
ANCHOR_RE = re.compile(
    MONTH_PAT + r'\.?\s+(\d{1,2})(?!\d)(?:st|nd|rd|th)?\b', re.IGNORECASE)
# Continuation tokens after the anchor: ", 29th", "& 30th", "- 20th",
# "to Oct 2", "and 10th" ...
TAIL_RE = re.compile(
    r'\s*(?:,|&|and|to|through|thru|[-–—])\s*(?:' + MONTH_PAT + r'\.?\s+)?(\d{1,2})(?!\d)(?:st|nd|rd|th)?\b',
    re.IGNORECASE)
YEAR_AFTER_RE = re.compile(r'^\s*,?\s*(20\d{2})\b')
YEAR_ANY_RE = re.compile(r'\b(20\d{2})\b')
TIME_RE = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b', re.IGNORECASE)


def clean_text(raw: str) -> str:
    """Strip HTML tags/entities and normalize whitespace."""
    txt = html_mod.unescape(raw or '')
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = txt.replace('’', "'").replace('‘', "'")
    return re.sub(r'\s+', ' ', txt).strip()


def parse_time(text: str) -> Optional[tuple[int, int]]:
    """Find an explicit am/pm time like '10am' or '10:30 a.m.'."""
    m = TIME_RE.search(text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    if not (1 <= hour <= 12) or minute > 59:
        return None
    if m.group(3).lower() == 'p' and hour != 12:
        hour += 12
    elif m.group(3).lower() == 'a' and hour == 12:
        hour = 0
    return hour, minute


def parse_date_span(text: str) -> Optional[dict[str, Any]]:
    """
    Find the first month-day date phrase in text and consume any
    day-list / range continuation. Returns {'dates': [(month, day), ...],
    'year': int|None, 'time': (h, m)|None} or None.
    """
    m = ANCHOR_RE.search(text)
    if not m:
        return None

    month = MONTHS[m.group(1).lower()]
    day = int(m.group(2))
    if not (1 <= day <= 31):
        return None
    dates = [(month, day)]

    pos = m.end()
    while True:
        t = TAIL_RE.match(text, pos)
        if not t:
            break
        if t.group(1):
            month = MONTHS[t.group(1).lower()]
        d = int(t.group(2))
        if 1 <= d <= 31:
            dates.append((month, d))
        pos = t.end()

    year = None
    y = YEAR_AFTER_RE.match(text[pos:])
    if y:
        year = int(y.group(1))
    else:
        y = YEAR_ANY_RE.search(text)
        if y:
            year = int(y.group(1))

    return {'dates': dates, 'year': year, 'time': parse_time(text)}


class TmbccScraper(BaseScraper):
    """Scrape event announcements from TMBCC blog posts."""

    name = "Tibetan Mongolian Buddhist Cultural Center"
    domain = "tmbcc.org"
    timezone = "America/Indiana/Indianapolis"

    def _fetch(self, url: str) -> Optional[str]:
        req = Request(url, headers=HEADERS)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except (HTTPError, URLError, TimeoutError) as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _fetch_posts(self) -> list[dict[str, Any]]:
        """Return posts as [{title, text, link, published(date)}]."""
        posts = self._fetch_posts_wpjson()
        if posts:
            return posts
        self.logger.info("wp-json unavailable, falling back to RSS")
        return self._fetch_posts_rss()

    def _fetch_posts_wpjson(self) -> list[dict[str, Any]]:
        content = self._fetch(WP_JSON_URL)
        if not content:
            return []
        try:
            items = json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.warning(f"wp-json parse failed: {e}")
            return []
        posts = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                published = datetime.fromisoformat(item['date']).date()
            except (KeyError, ValueError, TypeError):
                continue
            posts.append({
                'title': clean_text((item.get('title') or {}).get('rendered', '')),
                'text': clean_text((item.get('content') or {}).get('rendered', '')),
                'link': item.get('link', ''),
                'published': published,
            })
        self.logger.info(f"Fetched {len(posts)} posts via wp-json")
        return posts

    def _fetch_posts_rss(self) -> list[dict[str, Any]]:
        content = self._fetch(RSS_URL)
        if not content:
            return []
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.logger.warning(f"RSS parse failed: {e}")
            return []
        ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
        posts = []
        for item in root.findall('.//item'):
            title_el = item.find('title')
            pub_el = item.find('pubDate')
            if title_el is None or pub_el is None or not pub_el.text:
                continue
            try:
                from email.utils import parsedate_to_datetime
                published = parsedate_to_datetime(pub_el.text).date()
            except (ValueError, TypeError):
                continue
            enc = item.find('content:encoded', ns)
            link_el = item.find('link')
            posts.append({
                'title': clean_text(title_el.text or ''),
                'text': clean_text(enc.text if enc is not None else ''),
                'link': (link_el.text or '').strip() if link_el is not None else '',
                'published': published,
            })
        self.logger.info(f"Fetched {len(posts)} posts via RSS")
        return posts

    def _resolve_year(self, month: int, day: int, published: date) -> int:
        """Announcements precede events: publish year, unless that lands
        well before the publish date — then next year."""
        year = published.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            return year
        if candidate < published - timedelta(days=14):
            year += 1
        return year

    def _post_to_event(self, post: dict[str, Any]) -> Optional[dict[str, Any]]:
        title = post['title']
        # Titles carry the date for every observed post; body text (usually
        # just a poster image) is the fallback.
        span = parse_date_span(title) or parse_date_span(post['text'])
        if not span:
            self.logger.info(f"Skipping (no parseable date): {title!r}")
            return None

        tz = ZoneInfo(self.timezone)
        year = span['year']
        first_m, first_d = span['dates'][0]
        if year is None:
            year = self._resolve_year(first_m, first_d, post['published'])

        # Materialize each (month, day) with year rollover for spans that
        # cross into January (e.g. "Dec 30 - Jan 2").
        try:
            days = []
            y = year
            prev_month = first_m
            for mo, d in span['dates']:
                if mo < prev_month:
                    y += 1
                prev_month = mo
                days.append(date(y, mo, d))
        except ValueError as e:
            self.logger.info(f"Skipping (invalid date {e}): {title!r}")
            return None

        start_day, end_day = min(days), max(days)
        if span['time']:
            hour, minute = span['time']
        else:
            hour, minute = 9, 0  # daytime default; date itself is parsed, not guessed
        dtstart = datetime(start_day.year, start_day.month, start_day.day, hour, minute, tzinfo=tz)
        if end_day > start_day:
            dtend = datetime(end_day.year, end_day.month, end_day.day, 17, 0, tzinfo=tz)
        else:
            dtend = dtstart + timedelta(hours=2)

        now = datetime.now(tz)
        if dtend < now:
            self.logger.debug(f"Skipping past event ({start_day}): {title!r}")
            return None
        # Announcements more than ~18 months out are almost certainly a
        # year-inference error — refuse rather than emit a wrong date.
        if dtstart > now + timedelta(days=550):
            self.logger.info(f"Skipping (implausibly far out, {start_day}): {title!r}")
            return None

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': post['link'] or 'https://tmbcc.org/',
            'location': DEFAULT_LOCATION,
            'description': post['text'][:500],
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        posts = self._fetch_posts()
        events = []
        seen = set()
        for post in posts:
            event = self._post_to_event(post)
            if not event:
                continue
            key = (event['title'].lower(), event['dtstart'].date())
            if key in seen:
                continue
            seen.add(key)
            events.append(event)
        self.logger.info(f"Parsed {len(events)} upcoming events from {len(posts)} posts")
        return events


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Tibetan Mongolian Buddhist Cultural Center events from blog posts")
    parser.add_argument('--output', '-o', help='Output ICS file')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    scraper = TmbccScraper()
    scraper.run(args.output)


if __name__ == '__main__':
    main()
