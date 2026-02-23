#!/usr/bin/env python3
"""
Scraper for Jack London State Historic Park events.
https://jacklondonpark.com/events/
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from lib.base import BaseScraper


class JackLondonParkScraper(BaseScraper):
    """Scraper for Jack London State Historic Park events."""

    name = "Jack London State Historic Park"
    domain = "jacklondonpark.com"

    BASE_URL = "https://jacklondonpark.com"
    EVENTS_URL = "https://jacklondonpark.com/events/"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the events page."""
        self.logger.info(f"Fetching {self.EVENTS_URL}")
        response = requests.get(self.EVENTS_URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        events = []

        # Find all event links
        event_links = soup.select('a.wh-thumb-link[href*="/events/"]')

        for link in event_links:
            event_url = link.get('href')
            if not event_url:
                continue

            if not event_url.startswith('http'):
                event_url = self.BASE_URL + event_url

            # Skip the main events page itself
            if event_url.rstrip('/') == f"{self.BASE_URL}/events":
                continue

            try:
                event = self._scrape_event_page(event_url)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.warning(f"Error scraping {event_url}: {e}")
                continue

        return events

    def _scrape_event_page(self, url: str) -> dict[str, Any] | None:
        """Scrape a single event page."""
        self.logger.debug(f"Scraping {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Get title
        title_el = soup.select_one('article h2')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)

        # Get date and time from the "When:" section
        # Look for pattern like: "When: Sunday, February 22, 2026, 9:30 am to 12:00 pm"
        when_text = None
        
        # First try: div with "When:" that contains the full date/time inline
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if text.startswith('When:') and re.search(r'\d{4}', text):
                when_text = text
                break
        
        # Second try: p with "When:" that contains the full date/time
        if not when_text:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text.startswith('When:') and re.search(r'\d{4}', text):
                    when_text = text
                    break
        
        # Third try: look for standalone date paragraph after WHEN:
        if not when_text:
            for p in soup.select('article p'):
                text = p.get_text(strip=True)
                if re.match(r'^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),', text):
                    when_text = text
                    break

        if not when_text:
            self.logger.warning(f"No date found for {url}")
            return None
        
        # Parse the when text
        # Remove "When:" prefix if present
        when_text = re.sub(r'^When:\s*', '', when_text, flags=re.I)
        
        # Extract date: "Sunday, February 22, 2026"
        date_match = re.search(r'([A-Za-z]+,\s*)?([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})', when_text)
        if not date_match:
            self.logger.warning(f"Could not parse date from '{when_text}'")
            return None

        month_name = date_match.group(2)
        day = int(date_match.group(3))
        year = int(date_match.group(4))

        try:
            date = datetime.strptime(f"{month_name} {day}, {year}", "%B %d, %Y")
        except ValueError:
            self.logger.warning(f"Could not parse date: {month_name} {day}, {year}")
            return None

        # Parse time: "9:30 am to 12:00 pm" or "9:00 a.m. – 1:30 p.m."
        start_dt = date
        end_dt = None

        # Normalize a.m./p.m. to am/pm for easier parsing
        normalized_when = re.sub(r'a\.m\.', 'am', when_text, flags=re.I)
        normalized_when = re.sub(r'p\.m\.', 'pm', normalized_when, flags=re.I)

        time_match = re.search(
            r'(\d{1,2}):(\d{2})\s*(am|pm)(?:\s*(?:to|-|–|—)\s*(\d{1,2}):(\d{2})\s*(am|pm))?',
            normalized_when, re.I
        )
        if time_match:
            start_h = int(time_match.group(1))
            start_m = int(time_match.group(2))
            start_ampm = time_match.group(3).lower()

            if start_ampm == 'pm' and start_h != 12:
                start_h += 12
            elif start_ampm == 'am' and start_h == 12:
                start_h = 0

            start_dt = date.replace(hour=start_h, minute=start_m)

            if time_match.group(4) and time_match.group(5) and time_match.group(6):
                end_h = int(time_match.group(4))
                end_m = int(time_match.group(5))
                end_ampm = time_match.group(6).lower()

                if end_ampm == 'pm' and end_h != 12:
                    end_h += 12
                elif end_ampm == 'am' and end_h == 12:
                    end_h = 0

                end_dt = date.replace(hour=end_h, minute=end_m)

        # Get description
        description = ""
        article_body = soup.select_one('.article-body')
        if article_body:
            paras = article_body.select('p')
            desc_parts = []
            for p in paras[:3]:
                text = p.get_text(strip=True)
                if text and not text.startswith('WHEN:') and not text.startswith('WHERE:'):
                    desc_parts.append(text)
            description = ' '.join(desc_parts)[:500]

        location = "Jack London State Historic Park, 2400 London Ranch Road, Glen Ellen, CA 95442"

        return {
            'title': title,
            'dtstart': start_dt,
            'dtend': end_dt or start_dt,
            'url': url,
            'location': location,
            'description': description,
        }


if __name__ == '__main__':
    JackLondonParkScraper.main()
