#!/usr/bin/env python3
"""
Scraper for Davis Chamber of Commerce events
https://web.davischamber.com/events

Uses the MemberClicks XML API endpoint.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import re
import html
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests
import xml.etree.ElementTree as ET

from lib.base import BaseScraper


class DavisChamberScraper(BaseScraper):
    """Scraper for Davis Chamber of Commerce events."""

    name = "Davis Chamber of Commerce"
    domain = "davischamber.com"

    XML_URL = "https://web.davischamber.com/External/WCControls/V12/WebDeps/Calendar/xml/newCalendarXML.aspx"
    BASE_URL = "https://web.davischamber.com"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from MemberClicks XML API."""
        events = []
        
        # Fetch current month plus next 6 months
        now = datetime.now()
        for month_offset in range(self.months_ahead + 1):
            month_date = now + timedelta(days=month_offset * 30)
            start = month_date.replace(day=1)
            # Get end of month (start of next month)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
            end = end - timedelta(days=1)  # Last day of current month
            end = end.replace(hour=23, minute=59, second=59)
            
            month_events = self._fetch_month(start, end)
            events.extend(month_events)
        
        # Deduplicate by event ID
        seen_ids = set()
        unique_events = []
        for event in events:
            event_id = event.get('event_id')
            if event_id and event_id not in seen_ids:
                seen_ids.add(event_id)
                unique_events.append(event)
        
        return unique_events

    def _fetch_month(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Fetch events for a specific date range."""
        start_str = start.strftime("%Y-%m-%d %H:%M:%S.000")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S.999")
        
        url = f"{self.XML_URL}?startdate={start_str}&enddate={end_str}"
        self.logger.info(f"Fetching {start.strftime('%Y-%m')}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return self._parse_xml(response.text)
        except Exception as e:
            self.logger.error(f"Error fetching events: {e}")
            return []

    def _parse_xml(self, xml_content: str) -> list[dict[str, Any]]:
        """Parse events from XML content."""
        events = []
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            self.logger.error(f"XML parse error: {e}")
            return events
        
        tz = ZoneInfo('America/Los_Angeles')
        
        for item in root.findall('.//newCalendarDatav3'):
            try:
                event = self._parse_event(item, tz)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.warning(f"Failed to parse event: {e}")
                continue
        
        return events

    def _parse_event(self, item: ET.Element, tz: ZoneInfo) -> dict[str, Any] | None:
        """Parse a single event from XML element."""
        title = self._get_text(item, 'title')
        if not title:
            return None
        
        # Parse UTC times
        start_utc_str = self._get_text(item, 'StartDateTimeUtc')
        end_utc_str = self._get_text(item, 'EndDateTimeUtc')
        
        if not start_utc_str:
            return None
        
        # Parse ISO format: 2026-02-13T16:00:00+00:00
        try:
            dtstart = datetime.fromisoformat(start_utc_str).astimezone(tz)
            dtend = datetime.fromisoformat(end_utc_str).astimezone(tz) if end_utc_str else dtstart
        except ValueError as e:
            self.logger.warning(f"Failed to parse datetime: {e}")
            return None
        
        # Build location from address fields
        venue = self._get_text(item, 'Venue')
        addr1 = self._get_text(item, 'Address1')
        addr2 = self._get_text(item, 'Address2')
        city = self._get_text(item, 'City')
        state = self._get_text(item, 'State')
        zip_code = self._get_text(item, 'Zip')
        
        location_parts = []
        if venue:
            location_parts.append(venue)
        if addr1:
            location_parts.append(addr1)
        if addr2:
            location_parts.append(addr2)
        city_state_zip = ', '.join(filter(None, [city, state]))
        if zip_code:
            city_state_zip += f' {zip_code}'
        if city_state_zip:
            location_parts.append(city_state_zip)
        
        location = ', '.join(location_parts) if location_parts else 'Davis, CA'
        
        # Parse description (contains HTML)
        descr_html = self._get_text(item, 'Descr') or ''
        description = self._clean_html(descr_html)
        
        # Get event ID for URL and dedup
        event_id = self._get_text(item, 'id')
        
        # Build event URL
        url = None
        custom_url = self._get_text(item, 'customDetailsUrl')
        if custom_url:
            url = custom_url
        elif event_id:
            # URL format: /events/{title-slug}-{id}/details
            title_slug = re.sub(r'[^a-zA-Z0-9]+', '%20', title)
            url = f"{self.BASE_URL}/events/{title_slug}-{event_id}/details"
        
        # Get event type
        event_type = self._get_text(item, 'EventType')
        if event_type:
            description = f"{event_type}\n\n{description}" if description else event_type
        
        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'url': url,
            'location': location,
            'description': description.strip() if description else '',
            'event_id': event_id,
        }

    def _get_text(self, element: ET.Element, tag: str) -> str | None:
        """Get text content of a child element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _clean_html(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        if not html_content:
            return ''
        
        # Unescape HTML entities
        text = html.unescape(html_content)
        
        # Remove HTML tags
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()


if __name__ == '__main__':
    DavisChamberScraper.main()
