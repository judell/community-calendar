#!/usr/bin/env python3
"""
Scraper for Mystic Theatre Petaluma events
https://www.mystictheatre.com/calendar

The calendar is embedded via SeeTickets widget. We parse the structured HTML
which contains event details in well-defined CSS classes.
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


class MysticTheatreScraper(BaseScraper):
    """Scraper for Mystic Theatre Petaluma events."""

    name = "Mystic Theatre"
    domain = "mystictheatre.com"

    BASE_URL = 'https://www.mystictheatre.com'
    CALENDAR_URL = f'{BASE_URL}/calendar'
    VENUE_ADDRESS = "Mystic Theatre, 23 Petaluma Blvd N, Petaluma, CA 94952"

    def fetch_events(self) -> list[dict[str, Any]]:
        """Fetch events from Mystic Theatre calendar page."""
        self.logger.info(f"Fetching {self.CALENDAR_URL}")
        response = requests.get(self.CALENDAR_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        events = self._parse_seetickets_calendar(response.text)
        
        if not events:
            self.logger.warning("No events found - page structure may have changed")

        return events

    def _parse_seetickets_calendar(self, html_content: str) -> list[dict[str, Any]]:
        """Parse events from SeeTickets calendar widget HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        # Find all event cards
        event_cards = soup.select('.seetickets-list-event-container.mdc-card')
        self.logger.info(f"Found {len(event_cards)} event cards")

        for card in event_cards:
            try:
                event = self._parse_event_card(card)
                if event:
                    events.append(event)
                    self.logger.info(f"Found event: {event['title']} on {event['dtstart']}")
            except Exception as e:
                self.logger.warning(f"Error parsing event card: {e}")
                continue

        return events

    def _parse_event_card(self, card) -> dict[str, Any] | None:
        """Parse a single event card."""
        # Title
        title_el = card.select_one('.title a')
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        
        # Date - format: "Thu Feb 12"
        date_el = card.select_one('.date')
        if not date_el:
            return None
        date_str = date_el.get_text(strip=True)
        
        # Show time
        show_el = card.select_one('.see-showtime')
        show_time = show_el.get_text(strip=True) if show_el else None
        
        # Doors time
        doors_el = card.select_one('.see-doortime')
        doors_time = doors_el.get_text(strip=True) if doors_el else None
        
        # Parse date and time
        dtstart = self._parse_datetime(date_str, show_time or doors_time)
        if not dtstart:
            self.logger.warning(f"Could not parse date for: {title}")
            return None
        
        # Estimate end time (3 hours for concerts)
        dtend = dtstart + timedelta(hours=3)
        
        # Ticket URL
        ticket_url = title_el.get('href', self.CALENDAR_URL)
        
        # Venue - may include room info
        venue_el = card.select_one('.venue')
        venue = venue_el.get_text(strip=True) if venue_el else self.VENUE_ADDRESS
        # Clean up "at " prefix
        if venue.lower().startswith('at '):
            venue = venue[3:]
        # Add city if not present
        if 'petaluma' not in venue.lower():
            venue = f"{venue}, Petaluma, CA"
        
        # Genre
        genre_el = card.select_one('.genre')
        genre = genre_el.get_text(strip=True) if genre_el else None
        
        # Header/presenter (e.g., "Grindhouse Comedy Presents")
        header_el = card.select_one('.header')
        header = header_el.get_text(strip=True) if header_el else None
        
        # Subtitle/supporting acts
        subtitle_el = card.select_one('.subtitle')
        subtitle = subtitle_el.get_text(strip=True) if subtitle_el else None
        
        # Ages and price
        ages_el = card.select_one('.ages')
        ages = ages_el.get_text(strip=True) if ages_el else None
        price_el = card.select_one('.price')
        price = price_el.get_text(strip=True) if price_el else None
        
        # Build description
        desc_parts = []
        if header:
            desc_parts.append(header)
        if subtitle:
            desc_parts.append(subtitle)
        if genre:
            desc_parts.append(f"Genre: {genre}")
        if ages:
            desc_parts.append(f"Ages: {ages}")
        if price:
            desc_parts.append(f"Price: {price}")
        if doors_time and show_time and doors_time != show_time:
            desc_parts.append(f"Doors: {doors_time}, Show: {show_time}")
        desc_parts.append(f"Tickets: {ticket_url}")
        
        description = '\n'.join(desc_parts)
        
        return {
            'title': title,
            'url': ticket_url,
            'dtstart': dtstart,
            'dtend': dtend,
            'location': venue,
            'description': description,
        }

    def _parse_datetime(self, date_str: str, time_str: str | None) -> datetime | None:
        """
        Parse date and time strings into datetime.
        
        Date format: "Thu Feb 12" or "Sat Mar 5"
        Time format: "8:00PM" or "7:30 PM"
        """
        if not date_str:
            return None
        
        # Default time if not provided
        if not time_str:
            time_str = "8:00PM"
        
        # Normalize time string
        time_str = time_str.upper().replace(' ', '')
        
        # Parse date - format is "Day Mon DD"
        # e.g., "Thu Feb 12", "Sat Mar 5"
        date_match = re.match(r'\w+\s+(\w+)\s+(\d+)', date_str)
        if not date_match:
            return None
        
        month_str = date_match.group(1)
        day = int(date_match.group(2))
        
        # Month name to number
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month = months.get(month_str.lower()[:3])
        if not month:
            return None
        
        # Determine year (assume current or next year)
        now = datetime.now()
        year = now.year
        test_date = datetime(year, month, day)
        
        # If the date is more than 2 weeks in the past, assume next year
        if test_date < now - timedelta(days=14):
            year += 1
        
        # Parse time
        time_match = re.match(r'(\d{1,2}):(\d{2})(AM|PM)', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            ampm = time_match.group(3)
            
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
        else:
            # Default to 8pm
            hour = 20
            minute = 0
        
        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None


if __name__ == '__main__':
    MysticTheatreScraper.main()
