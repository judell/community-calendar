#!/usr/bin/env python3
"""
Scraper for University of Toronto events
https://www.utoronto.ca/events

The aggregate page shows ~5 events per department (capped).
This scraper also follows "More" links to get full department listings.

Department pages use several Drupal themes:
- "events-uoft": Humanities, Environment, CDTPS, OISE, KPE, Fields
- "node-event" (Daniels): date in .date span, title in .name span
- "listing-item--events" (Law, Music): day/month in BEM date elements
- "event-item" (DLSPH): custom WordPress with .event-listing-date
- AJAX-loaded (Arts & Science, Temerty, UTSC): skipped (need JS)
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; community-calendar/1.0)'}


class UofTEventsScraper(BaseScraper):
    """Scraper for University of Toronto events page."""

    name = "University of Toronto"
    domain = "utoronto.ca"
    timezone = "America/Toronto"

    EVENTS_URL = "https://www.utoronto.ca/events"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from aggregate page + department pages."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")

        resp = requests.get(self.EVENTS_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Collect "More" links and their department names
        more_links = {}
        for a in soup.find_all('a', class_='btn'):
            text = a.get_text(strip=True)
            if text.startswith('More '):
                dept = text.replace('More ', '').replace(' events', '').replace(' Events', '').strip()
                url = a.get('href', '')
                if url:
                    more_links[dept] = url

        self.logger.info(f"Found {len(more_links)} department 'More' links")

        # Parse aggregate page tables (baseline)
        aggregate_events = self._parse_aggregate(soup)
        self.logger.info(f"Aggregate page: {len(aggregate_events)} events")

        # Track URLs we've already seen (from aggregate page) to avoid duplicates
        seen_urls = {e['url'] for e in aggregate_events if e.get('url')}

        # Follow each "More" link for deeper coverage
        dept_events = []
        for dept, url in more_links.items():
            full_url = urljoin(self.EVENTS_URL, url)
            new_events = self._scrape_department(dept, full_url, seen_urls)
            dept_events.extend(new_events)

        self.logger.info(f"Department pages: {len(dept_events)} additional events")

        all_events = aggregate_events + dept_events
        self.logger.info(f"Total: {len(all_events)} events")
        return all_events

    def _parse_aggregate(self, soup) -> list[dict[str, Any]]:
        """Parse the aggregate page tables."""
        events = []
        tables = soup.find_all('table')
        for table in tables:
            # Find department name from the "More" button after this table
            more_btn = table.find_next('a', class_='btn')
            dept = ''
            if more_btn:
                text = more_btn.get_text(strip=True)
                if text.startswith('More '):
                    dept = text.replace('More ', '').replace(' events', '').replace(' Events', '').strip()

            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if not cells:
                    continue
                event = self._parse_table_row(cells, dept)
                if event:
                    events.append(event)
        return events

    def _parse_table_row(self, cells, department: str = '') -> Optional[dict[str, Any]]:
        """Parse a table row from the aggregate page."""
        try:
            link = cells[0].find('a')
            if not link:
                return None
            title = link.get_text(strip=True)
            url = link.get('href', '')

            if len(cells) < 2:
                return None
            date_text = cells[1].get_text(strip=True)
            dtstart, dtend = self._parse_date(date_text)
            if not dtstart:
                return None

            # Third cell may override department
            if len(cells) >= 3:
                cell_dept = cells[2].get_text(strip=True)
                if cell_dept:
                    department = cell_dept

            return self._make_event(title, url, dtstart, dtend, department)

        except Exception as e:
            self.logger.warning(f"Error parsing row: {e}")
            return None

    def _scrape_department(self, dept: str, url: str, seen_urls: set) -> list[dict[str, Any]]:
        """Scrape a department page for events not on the aggregate page."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                self.logger.warning(f"{dept}: HTTP {resp.status_code}")
                return []
        except Exception as e:
            self.logger.warning(f"{dept}: fetch error: {e}")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []

        # Try each parser pattern in order
        for parser in [
            self._parse_events_uoft,      # Humanities, Environment, CDTPS, OISE, KPE, Fields
            self._parse_daniels,           # Daniels (node-event with DD.MM.YY dates)
            self._parse_listing_events,    # Law, Music (BEM-style)
            self._parse_dlsph,             # DLSPH (WordPress event-item)
            self._parse_views_row_links,   # Generic fallback: any views-row with links
        ]:
            results = parser(soup, dept, url)
            if results:
                events = results
                break

        # Deduplicate against aggregate page
        new_events = []
        for e in events:
            if e.get('url') and e['url'] in seen_urls:
                continue
            seen_urls.add(e.get('url', ''))
            new_events.append(e)

        if new_events:
            self.logger.info(f"{dept}: {len(new_events)} new events (from {len(events)} total)")
        return new_events

    # --- Department page parsers ---

    def _parse_events_uoft(self, soup, dept: str, base_url: str) -> list[dict[str, Any]]:
        """Parse Drupal 'events-uoft' theme (Humanities, Environment, CDTPS, etc.)."""
        nodes = soup.find_all(class_='node-events-uoft')
        if not nodes:
            return []

        events = []
        for node in nodes:
            title_el = node.find('h3')
            if not title_el:
                continue
            link = title_el.find('a')
            title = title_el.get_text(strip=True)
            url = urljoin(base_url, link['href']) if link else ''

            date_el = node.find(class_=lambda c: c and 'date-formatted' in c)
            if not date_el:
                date_el = node.find(class_='date-display-single')
            date_text = date_el.get_text(strip=True) if date_el else ''
            dtstart, dtend = self._parse_date(date_text) if date_text else (None, None)
            if not dtstart:
                continue

            events.append(self._make_event(title, url, dtstart, dtend, dept))
        return events

    def _parse_daniels(self, soup, dept: str, base_url: str) -> list[dict[str, Any]]:
        """Parse Daniels-style events (node-event with DD.MM.YY dates)."""
        articles = soup.find_all('article', class_='node-event')
        if not articles:
            return []

        tz = ZoneInfo(self.timezone)
        events = []
        for article in articles:
            link = article.find('a')
            if not link:
                continue
            url = urljoin(base_url, link.get('href', ''))

            name_el = article.find(class_='name') or article.find(class_='field--name-title')
            title = name_el.get_text(strip=True) if name_el else link.get_text(strip=True)

            date_el = article.find(class_='date')
            if not date_el:
                continue
            date_text = date_el.get_text(strip=True)
            # Format: DD.MM.YY
            m = re.match(r'(\d{2})\.(\d{2})\.(\d{2})', date_text)
            if not m:
                continue
            day, month, year = m.groups()
            try:
                dtstart = datetime(2000 + int(year), int(month), int(day), tzinfo=tz)
            except ValueError:
                continue

            events.append(self._make_event(title, url, dtstart, None, dept))
        return events

    def _parse_listing_events(self, soup, dept: str, base_url: str) -> list[dict[str, Any]]:
        """Parse Law/Music-style BEM listing items."""
        items = soup.find_all(class_=lambda c: c and 'listing-item--events' in c
                              and 'content' not in c and 'date' not in c
                              and 'img' not in c and 'title' not in c
                              and 'wrapper' not in c)
        if not items:
            return []

        tz = ZoneInfo(self.timezone)
        events = []
        for item in items:
            title_el = item.find('h3')
            if not title_el:
                continue
            link = title_el.find('a')
            title = title_el.get_text(strip=True)
            url = urljoin(base_url, link['href']) if link else ''

            day_el = item.find(class_=lambda c: c and 'date-day' in c)
            month_el = item.find(class_=lambda c: c and 'date-month' in c)
            if not day_el or not month_el:
                continue

            day = day_el.get_text(strip=True)
            # Month element has both full and abbreviated; get the hidden full version
            month_full = month_el.find(class_='u-visually--hidden')
            month_text = month_full.get_text(strip=True) if month_full else month_el.get_text(strip=True)

            # Assume current year or next year
            now = datetime.now(tz)
            dtstart = self._make_dt(month_text, day, str(now.year), tz)
            if dtstart and dtstart.month < now.month:
                dtstart = self._make_dt(month_text, day, str(now.year + 1), tz)
            if not dtstart:
                continue

            events.append(self._make_event(title, url, dtstart, None, dept))
        return events

    def _parse_dlsph(self, soup, dept: str, base_url: str) -> list[dict[str, Any]]:
        """Parse DLSPH-style WordPress events (event-item class)."""
        items = soup.find_all(class_='event-item')
        if not items:
            return []

        events = []
        for item in items:
            title_el = item.find(class_='title')
            if not title_el:
                continue
            link = title_el.find('a')
            title = (link or title_el).get_text(strip=True)
            url = urljoin(base_url, link['href']) if link else ''

            date_el = item.find(class_='event-listing-date')
            if not date_el:
                continue
            date_text = date_el.get_text(strip=True)
            dtstart, dtend = self._parse_date(date_text)
            if not dtstart:
                continue

            events.append(self._make_event(title, url, dtstart, dtend, dept))
        return events

    def _parse_views_row_links(self, soup, dept: str, base_url: str) -> list[dict[str, Any]]:
        """Generic fallback: extract events from Drupal views-row divs."""
        rows = soup.find_all(class_='views-row')
        if not rows:
            return []

        events = []
        for row in rows:
            # Skip non-event rows (e.g., banners)
            link = row.find('a', href=lambda h: h and '/event' in h)
            if not link:
                continue
            title = link.get_text(strip=True)
            url = urljoin(base_url, link['href'])

            # Try to find a date anywhere in the row
            date_text = ''
            for el in row.find_all(class_=lambda c: c and 'date' in str(c).lower()):
                date_text = el.get_text(strip=True)
                if date_text:
                    break
            if not date_text:
                # Look for date-like text in the row
                text = row.get_text()
                m = re.search(r'(\w+ \d{1,2},? \d{4})', text)
                if m:
                    date_text = m.group(1)

            dtstart, dtend = self._parse_date(date_text) if date_text else (None, None)
            if not dtstart:
                continue

            events.append(self._make_event(title, url, dtstart, dtend, dept))
        return events

    # --- Helpers ---

    def _make_event(self, title: str, url: str, dtstart, dtend, department: str) -> dict[str, Any]:
        """Create a standard event dict."""
        location = 'University of Toronto'
        if department:
            location = f"{department}, University of Toronto"
        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': f"Department: {department}" if department else '',
        }

    def _parse_date(self, text: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """Parse date text into start and optional end datetimes.

        Formats:
          February 14, 2026
          Feb 21 2026
          February 13 to 15, 2026
          February 13 to February 15, 2026
          February 10 to March 10, 2026
          February 25, to August 1, 2026
        """
        tz = ZoneInfo(self.timezone)
        text = re.sub(r',\s*to\s', ' to ', text)

        # Range: "Month D to Month D, YYYY"
        m = re.match(r'(\w+)\s+(\d+)\s+to\s+(\w+)\s+(\d+),?\s+(\d{4})', text)
        if m:
            start_month, start_day, end_month, end_day, year = m.groups()
            dtstart = self._make_dt(start_month, start_day, year, tz)
            dtend = self._make_dt(end_month, end_day, year, tz)
            return dtstart, dtend

        # Range same month: "Month D to D, YYYY"
        m = re.match(r'(\w+)\s+(\d+)\s+to\s+(\d+),?\s+(\d{4})', text)
        if m:
            month, start_day, end_day, year = m.groups()
            dtstart = self._make_dt(month, start_day, year, tz)
            dtend = self._make_dt(month, end_day, year, tz)
            return dtstart, dtend

        # Single date: "Month D, YYYY" or "Month D YYYY"
        m = re.match(r'(\w+)\s+(\d+),?\s+(\d{4})', text)
        if m:
            month, day, year = m.groups()
            dtstart = self._make_dt(month, day, year, tz)
            return dtstart, None

        self.logger.warning(f"Unparseable date: {text}")
        return None, None

    def _make_dt(self, month: str, day: str, year: str, tz) -> Optional[datetime]:
        """Create a datetime from month name, day, year."""
        for fmt in ('%B %d %Y', '%b %d %Y'):
            try:
                dt = datetime.strptime(f"{month} {day} {year}", fmt)
                return dt.replace(tzinfo=tz)
            except ValueError:
                continue
        self.logger.warning(f"Cannot parse date parts: {month} {day} {year}")
        return None


if __name__ == '__main__':
    UofTEventsScraper.main()
