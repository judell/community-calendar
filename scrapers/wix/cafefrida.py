#!/usr/bin/env python3
"""
Scraper for Cafe Frida Gallery events.
https://www.cafefridagallery.com/events

Events are server-side rendered in a Wix Repeater component.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

import html
import re
import urllib.request
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from lib.base import BaseScraper


PACIFIC = ZoneInfo('America/Los_Angeles')


class CafeFridaScraper(BaseScraper):
    """Scraper for Cafe Frida Gallery events."""

    name = "Cafe Frida Gallery"
    domain = "cafefridagallery.com"

    URL = "https://www.cafefridagallery.com/events"
    LOCATION = "Cafe Frida Gallery, 305 S A St, Santa Rosa, CA"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch and parse events from the website."""
        self.logger.info(f"Fetching {self.URL}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = urllib.request.Request(self.URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read().decode('utf-8')

        return self._parse_events(html_content)

    def _parse_events(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from HTML using regex."""
        events = []

        # Find each listitem block containing an event
        listitem_pattern = r'role="listitem"[^>]*>(.*?)(?=role="listitem"|</section>)'
        listitems = re.findall(listitem_pattern, html_content, re.DOTALL)

        for item_html in listitems:
            try:
                event = self._parse_event_item(item_html)
                if event:
                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")
            except Exception as e:
                self.logger.warning(f"Error parsing event: {e}")
                continue

        return events

    def _parse_event_item(self, item_html: str) -> dict[str, Any] | None:
        """Parse a single event item."""
        # Extract title
        title_match = re.search(
            r'class="[^"]*comp-l93ch30e[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
            item_html, re.DOTALL
        )
        if not title_match:
            return None
        title = re.sub(r'<[^>]+>', '', title_match.group(1))
        title = html.unescape(title).strip()

        if not title:
            return None

        # Extract date
        date_match = re.search(
            r'class="[^"]*comp-l93egplp[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
            item_html, re.DOTALL
        )
        date_str = ''
        if date_match:
            date_str = re.sub(r'<[^>]+>', '', date_match.group(1))
            date_str = html.unescape(date_str).strip()

        # Extract time
        time_match = re.search(
            r'class="[^"]*comp-l94lcdfy[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
            item_html, re.DOTALL
        )
        time_str = ''
        if time_match:
            time_str = re.sub(r'<[^>]+>', '', time_match.group(1))
            time_str = html.unescape(time_str).strip()

        # Extract description
        desc_match = re.search(
            r'class="[^"]*comp-l93ch30n[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>',
            item_html, re.DOTALL
        )
        description = ''
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1))
            description = html.unescape(description).strip()

        # Extract category
        cat_match = re.search(
            r'class="[^"]*comp-l93ch2zz[^"]*"[^>]*>.*?<h6[^>]*>(.*?)</h6>',
            item_html, re.DOTALL
        )
        category = ''
        if cat_match:
            category = re.sub(r'<[^>]+>', '', cat_match.group(1))
            category = html.unescape(category).strip()

        # Parse date: "Sunday, February 1, 2026" or "February 1, 2026"
        event_date = None
        if date_str:
            dm = re.search(r'(\w+)\s+(\d+),\s+(\d{4})', date_str)
            if dm:
                month_str, day, year = dm.groups()
                try:
                    event_date = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                except ValueError:
                    pass

        if not event_date:
            return None

        # Parse time: "11:30am-1:30pm"
        time_str_clean = time_str.lower().replace(' ', '')
        tm = re.match(r'(\d{1,2}):?(\d{2})?(am|pm)-(\d{1,2}):?(\d{2})?(am|pm)', time_str_clean)
        if tm:
            sh, sm, sap, eh, em, eap = tm.groups()
            sm = sm or '00'
            em = em or '00'

            start_hour = int(sh)
            if sap == 'pm' and start_hour != 12:
                start_hour += 12
            elif sap == 'am' and start_hour == 12:
                start_hour = 0

            end_hour = int(eh)
            if eap == 'pm' and end_hour != 12:
                end_hour += 12
            elif eap == 'am' and end_hour == 12:
                end_hour = 0

            dt_start = event_date.replace(hour=start_hour, minute=int(sm), tzinfo=PACIFIC)
            dt_end = event_date.replace(hour=end_hour, minute=int(em), tzinfo=PACIFIC)
        else:
            dt_start = event_date.replace(hour=12, minute=0, tzinfo=PACIFIC)
            dt_end = event_date.replace(hour=13, minute=0, tzinfo=PACIFIC)

        if category:
            description = f"[{category}] {description}"

        return {
            'title': title,
            'url': self.URL,
            'dtstart': dt_start,
            'dtend': dt_end,
            'location': self.LOCATION,
            'description': description
        }


if __name__ == '__main__':
    CafeFridaScraper.main()
