#!/usr/bin/env python3
"""
Scraper for City of Toronto council and committee meetings.
Data from Toronto Open Data CKAN portal.
https://open.toronto.ca/dataset/city-council-and-committees-meeting-schedule-reports/
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

from lib.ckan import CKANScraper

TZ = ZoneInfo("America/Toronto")


class TorontoMeetingsScraper(CKANScraper):
    name = "City of Toronto Meetings"
    domain = "toronto.ca"
    timezone = "America/Toronto"

    ckan_base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    resource_id = "08c8aedb-afba-41f5-830e-bbfb305ebbc7"

    def build_sort(self) -> str:
        return "Date asc"

    def map_record(self, record: dict) -> Optional[dict[str, Any]]:
        committee = record.get('Committee', '')
        date_str = record.get('Date', '')
        start_time = record.get('Start Time', '')
        end_time = record.get('End Time', '')
        location = record.get('Location', '')
        mtg_num = record.get('MTG #', '')

        if not date_str or not committee:
            return None

        # Parse date (YYYY-MM-DD)
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            self.logger.warning(f"Unparseable date: {date_str}")
            return None

        # Filter to future dates
        if date.date() < datetime.now().date():
            return None

        # Parse start time (e.g. "09:30 AM")
        dtstart = self._parse_time(date, start_time)
        dtend = self._parse_time(date, end_time)

        title = committee
        if mtg_num:
            title = f"{committee} — Meeting #{mtg_num}"

        return {
            'title': title,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': location,
            'url': 'https://www.toronto.ca/city-government/council/',
            'description': f"Committee: {committee}",
        }

    def _parse_time(self, date: datetime, time_str: str) -> datetime:
        """Parse time like '09:30 AM' or '13:30 PM' and combine with date."""
        if not time_str:
            return date.replace(hour=9, minute=0, tzinfo=TZ)

        # Handle inconsistent format: "13:30 PM" should just be 13:30
        time_str = time_str.strip()
        for fmt in ('%I:%M %p', '%H:%M %p', '%H:%M'):
            try:
                t = datetime.strptime(time_str, fmt)
                return date.replace(hour=t.hour, minute=t.minute, tzinfo=TZ)
            except ValueError:
                continue

        return date.replace(hour=9, minute=0, tzinfo=TZ)


if __name__ == '__main__':
    TorontoMeetingsScraper.main()
