#!/usr/bin/env python3
"""
Scraper for Duke Arts events.
https://arts.duke.edu/events/

Duke Arts uses FacetWP on WordPress. The initial page load includes 85 of ~129
events in a `.facetwp-template` div. Each event is an `<article>` with date,
title, presenter, excerpt, and URL.

Usage:
    python scrapers/duke_arts.py --output cities/raleighdurham/duke_arts.ics
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime, timedelta
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper
from lib.utils import DEFAULT_HEADERS


class DukeArtsScraper(BaseScraper):
    """Scraper for Duke Arts via FacetWP HTML parsing."""

    name = "Duke Arts"
    domain = "arts.duke.edu"
    timezone = "America/New_York"

    EVENTS_URL = "https://arts.duke.edu/events/"

    # Date patterns after sr-only spans are removed
    # "Tue, Feb 17 at 1:00pm" or "Feb 21 – Feb 22"
    DATE_TIME_RE = re.compile(
        r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+'
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s+'
        r'at\s+(\d{1,2}:\d{2}(?:am|pm))'
    )
    DATE_RANGE_RE = re.compile(
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\s*'
        r'[–—-]\s*'
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})'
    )

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Duke Arts events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        response = requests.get(
            self.EVENTS_URL,
            headers=DEFAULT_HEADERS,
            timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        template = soup.find('div', class_='facetwp-template')
        if not template:
            self.logger.warning("No facetwp-template found")
            return []

        articles = template.find_all('article', class_='post-event')
        self.logger.info(f"Found {len(articles)} event articles")

        events = []
        now = datetime.now()
        current_year = now.year

        for article in articles:
            event = self._parse_article(article, current_year)
            if event:
                events.append(event)

        return events

    def _parse_article(self, article, current_year: int) -> dict[str, Any] | None:
        """Parse a single article element."""
        # Title
        h3 = article.find('h3')
        if not h3:
            return None
        title = ' '.join(h3.text.split())  # normalize whitespace

        # URL — prefer more-info-link, fall back to post-header
        more_info = article.find('a', class_='more-info-link')
        header_link = article.find('a', class_='post-header')
        url = ''
        if more_info and more_info.get('href'):
            url = more_info['href']
        elif header_link and header_link.get('href'):
            url = header_link['href']

        # Date
        date_div = article.find('div', class_='event-date-alt')
        if not date_div:
            return None

        # Remove sr-only spans to get clean text
        for span in date_div.find_all('span', class_='sr-only'):
            span.decompose()
        date_text = date_div.text.strip()

        dtstart, dtend = self._parse_date(date_text, current_year)
        if not dtstart:
            return None

        # Presenter
        presenter = article.find('a', class_='post-term')
        presenter_name = presenter.text.strip() if presenter else ''

        # Description
        excerpt = article.find('p', class_='excerpt')
        excerpt_text = excerpt.text.strip() if excerpt else ''

        description = ''
        if presenter_name:
            description = f"Presenter: {presenter_name}"
        if excerpt_text:
            if description:
                description += f"\n\n{excerpt_text}"
            else:
                description = excerpt_text

        # Location — Duke events are on campus
        location = "Duke University, Durham, NC"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': description,
        }

    def _parse_date(self, text: str, year: int):
        """Parse date text into (dtstart, dtend) datetimes."""
        # Try "Day, Mon DD at H:MMam/pm"
        m = self.DATE_TIME_RE.search(text)
        if m:
            date_str = m.group(1)  # "Feb 17"
            time_str = m.group(2)  # "1:00pm"
            try:
                dtstart = datetime.strptime(f"{date_str} {year} {time_str}", '%b %d %Y %I:%M%p')
                # If parsed date is far in the past, try next year
                if dtstart.month < datetime.now().month - 2:
                    dtstart = dtstart.replace(year=year + 1)
                dtend = dtstart + timedelta(hours=2)
                return dtstart, dtend
            except ValueError:
                return None, None

        # Try "Mon DD – Mon DD" (date range, no time)
        m = self.DATE_RANGE_RE.search(text)
        if m:
            start_str = m.group(1)  # "Feb 21"
            end_str = m.group(2)    # "Feb 22"
            try:
                dtstart = datetime.strptime(f"{start_str} {year}", '%b %d %Y')
                dtend = datetime.strptime(f"{end_str} {year}", '%b %d %Y')
                if dtstart.month < datetime.now().month - 2:
                    dtstart = dtstart.replace(year=year + 1)
                    dtend = dtend.replace(year=year + 1)
                # Set reasonable default times for all-day ranges
                dtstart = dtstart.replace(hour=10)
                dtend = dtend.replace(hour=22)
                return dtstart, dtend
            except ValueError:
                return None, None

        return None, None


if __name__ == '__main__':
    DukeArtsScraper.main()
