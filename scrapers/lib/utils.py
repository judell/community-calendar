"""Common utilities for scrapers."""

import hashlib
import logging
import random
import re
import time
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


def fetch_with_retry(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    timeout: int = 30,
    headers: Optional[dict] = None,
) -> str:
    """Fetch URL with exponential backoff retry."""
    headers = headers or DEFAULT_HEADERS
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Request failed, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)


def generate_uid(title: str, dtstart: datetime, domain: str) -> str:
    """Generate a unique ID for an event."""
    uid_str = f"{title}-{dtstart.isoformat()}"
    uid_hash = hashlib.md5(uid_str.encode()).hexdigest()
    return f"{uid_hash}@{domain}"


def append_source(description: str, source: str) -> str:
    """Append source attribution to description."""
    desc = (description or '').rstrip()
    if desc:
        return f"{desc}\n\nSource: {source}"
    return f"Source: {source}"


def parse_date_flexible(text: str, target_year: Optional[int] = None) -> Optional[datetime]:
    """
    Parse date from various formats:
    - "Feb 03" or "Feb 3"
    - "February 3, 2026"
    - "02.03.26" (MM.DD.YY)
    - "2026-02-03"
    
    Returns datetime at midnight, or None if unparseable.
    """
    if not text:
        return None
    
    text = text.strip()
    
    # ISO format: 2026-02-03
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        return datetime(year, month, day)
    
    # MM.DD.YY format
    dot_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', text)
    if dot_match:
        month, day, year = map(int, dot_match.groups())
        year = 2000 + year
        return datetime(year, month, day)
    
    # "February 3, 2026" or "Feb 3, 2026"
    full_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', text)
    if full_match:
        month_str, day, year = full_match.groups()
        month = MONTH_MAP.get(month_str.lower())
        if month:
            return datetime(int(year), month, int(day))
    
    # "Feb 03" - needs target_year
    short_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})', text)
    if short_match and target_year:
        month_str, day = short_match.groups()
        month = MONTH_MAP.get(month_str.lower())
        if month:
            return datetime(target_year, month, int(day))
    
    return None


def parse_time_flexible(text: str) -> Optional[tuple[int, int]]:
    """
    Parse time from various formats:
    - "6:00 PM" or "6:00PM" or "6PM"
    - "18:00"
    
    Returns (hour, minute) in 24-hour format, or None if unparseable.
    """
    if not text:
        return None
    
    text = text.strip().upper()
    
    # 12-hour format: 6:00 PM, 6:00PM, 6PM
    match_12 = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)', text)
    if match_12:
        hour = int(match_12.group(1))
        minute = int(match_12.group(2) or 0)
        ampm = match_12.group(3)
        
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
        
        return (hour, minute)
    
    # 24-hour format: 18:00
    match_24 = re.search(r'(\d{1,2}):(\d{2})', text)
    if match_24:
        hour, minute = map(int, match_24.groups())
        if 0 <= hour <= 23:
            return (hour, minute)
    
    return None
