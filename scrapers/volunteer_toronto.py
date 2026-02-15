#!/usr/bin/env python3
"""
Scraper for Volunteer Toronto events.

Primary target:
https://www.volunteertoronto.ca/networking/events/calendar.asp

The site appears to use legacy ASP calendar pages. This scraper tries multiple
delivery patterns in order:
1) RSS/Atom endpoints (if available)
2) ICS endpoints (if available)
3) HTML calendar/list pages (best-effort parsing)
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])

import json
import re
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar

from lib.base import BaseScraper


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; community-calendar/1.0)"
}


class VolunteerTorontoScraper(BaseScraper):
    """Scraper for Volunteer Toronto event listings."""

    name = "Volunteer Toronto"
    domain = "volunteertoronto.ca"
    timezone = "America/Toronto"

    BASE_URL = "https://www.volunteertoronto.ca"
    HTML_URLS = [
        "https://www.volunteertoronto.ca/networking/events/calendar.asp",
        "https://www.volunteertoronto.ca/events/calendar.asp",
    ]
    RSS_URLS = [
        "https://www.volunteertoronto.ca/networking/events/rss.asp",
        "https://www.volunteertoronto.ca/events/rss.asp",
        "https://www.volunteertoronto.ca/networking/events/rss.aspx",
        "https://www.volunteertoronto.ca/events/rss.aspx",
    ]
    ICS_URLS = [
        "https://www.volunteertoronto.ca/networking/events/ical.asp",
        "https://www.volunteertoronto.ca/events/ical.asp",
        "https://www.volunteertoronto.ca/networking/events/calendar.ics",
        "https://www.volunteertoronto.ca/events/calendar.ics",
    ]

    def fetch_events(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        # 1) RSS/Atom endpoints
        for url in self.RSS_URLS:
            found = self._fetch_from_rss(url)
            if found:
                events.extend(found)
                self.logger.info(f"Using RSS endpoint: {url} ({len(found)} events)")
                return self._dedupe(events)

        # 2) ICS endpoints
        for url in self.ICS_URLS:
            found = self._fetch_from_ics(url)
            if found:
                events.extend(found)
                self.logger.info(f"Using ICS endpoint: {url} ({len(found)} events)")
                return self._dedupe(events)

        # 3) HTML pages
        for url in self.HTML_URLS:
            found = self._fetch_from_html(url)
            if found:
                events.extend(found)
                self.logger.info(f"Using HTML endpoint: {url} ({len(found)} events)")
                return self._dedupe(events)

        self.logger.warning("No events found from Volunteer Toronto endpoints")
        return []

    def _fetch_url(self, url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                return None
            text = resp.text.strip()
            if not text:
                return None
            return text
        except Exception as exc:
            self.logger.debug(f"Fetch failed for {url}: {exc}")
            return None

    def _fetch_from_rss(self, url: str) -> list[dict[str, Any]]:
        text = self._fetch_url(url)
        if not text:
            return []
        if "<rss" not in text.lower() and "<feed" not in text.lower():
            return []

        feed = feedparser.parse(text)
        if not getattr(feed, "entries", None):
            return []

        events: list[dict[str, Any]] = []
        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            if not title:
                continue

            dtstart = self._pick_entry_datetime(entry)
            if not dtstart:
                continue

            dtend = None
            if getattr(entry, "updated_parsed", None):
                dtend = self._tm_to_dt(entry.updated_parsed)
                if dtend and dtend < dtstart:
                    dtend = None

            description = (
                entry.get("summary")
                or entry.get("description")
                or ""
            ).strip()
            url_value = (entry.get("link") or "").strip()

            events.append({
                "title": title,
                "dtstart": dtstart,
                "dtend": dtend,
                "url": url_value,
                "description": self._clean_text(description),
            })

        return events

    def _fetch_from_ics(self, url: str) -> list[dict[str, Any]]:
        text = self._fetch_url(url)
        if not text or "BEGIN:VCALENDAR" not in text:
            return []

        try:
            cal = Calendar.from_ical(text.encode("utf-8", errors="ignore"))
        except Exception as exc:
            self.logger.debug(f"ICS parse failed for {url}: {exc}")
            return []

        tz = ZoneInfo(self.timezone)
        events: list[dict[str, Any]] = []
        for comp in cal.walk():
            if comp.name != "VEVENT":
                continue

            summary = self._as_text(comp.get("summary"))
            if not summary:
                continue

            dtstart = self._ical_to_dt(comp.get("dtstart"), tz)
            if not dtstart:
                continue
            dtend = self._ical_to_dt(comp.get("dtend"), tz)

            location = self._as_text(comp.get("location"))
            description = self._as_text(comp.get("description"))
            link = self._as_text(comp.get("url"))

            events.append({
                "title": summary,
                "dtstart": dtstart,
                "dtend": dtend,
                "location": location,
                "description": self._clean_text(description),
                "url": link,
            })

        return events

    def _fetch_from_html(self, url: str) -> list[dict[str, Any]]:
        text = self._fetch_url(url)
        if not text:
            return []

        soup = BeautifulSoup(text, "html.parser")

        # Strategy A: JSON-LD Event objects
        jsonld_events = self._parse_jsonld_events(soup, url)
        if jsonld_events:
            return jsonld_events

        # Strategy B: visible text patterns like:
        # "9:30 - 11:00 a.m.: Event title"
        text_events = self._parse_plaintext_patterns(soup, url)
        if text_events:
            return text_events

        return []

    def _parse_jsonld_events(self, soup: BeautifulSoup, page_url: str) -> list[dict[str, Any]]:
        tz = ZoneInfo(self.timezone)
        events: list[dict[str, Any]] = []
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in scripts:
            raw = (script.string or script.get_text() or "").strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except Exception:
                continue
            for obj in self._iter_jsonld(payload):
                typ = obj.get("@type")
                if isinstance(typ, list):
                    is_event = "Event" in typ
                else:
                    is_event = isinstance(typ, str) and "Event" in typ
                if not is_event:
                    continue

                title = (obj.get("name") or "").strip()
                if not title:
                    continue
                dtstart = self._parse_dt(obj.get("startDate"), tz)
                if not dtstart:
                    continue
                dtend = self._parse_dt(obj.get("endDate"), tz)

                location = ""
                loc_obj = obj.get("location")
                if isinstance(loc_obj, dict):
                    location = (loc_obj.get("name") or "").strip()
                    addr = loc_obj.get("address")
                    if isinstance(addr, dict):
                        addr_parts = [
                            addr.get("streetAddress", ""),
                            addr.get("addressLocality", ""),
                            addr.get("addressRegion", ""),
                        ]
                        addr_text = ", ".join([p for p in addr_parts if p])
                        if addr_text and addr_text not in location:
                            location = f"{location}, {addr_text}" if location else addr_text

                desc = (obj.get("description") or "").strip()
                link = (obj.get("url") or page_url).strip()

                events.append({
                    "title": title,
                    "dtstart": dtstart,
                    "dtend": dtend,
                    "location": location,
                    "description": self._clean_text(desc),
                    "url": link,
                })
        return events

    def _parse_plaintext_patterns(self, soup: BeautifulSoup, page_url: str) -> list[dict[str, Any]]:
        tz = ZoneInfo(self.timezone)
        text = soup.get_text("\n", strip=True)
        if not text:
            return []

        # Capture month/year context from page (e.g., "August 2025")
        now = datetime.now(tz)
        month_name_to_num = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        month_num = now.month
        year_num = now.year
        m_ctx = re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
            text,
            flags=re.IGNORECASE,
        )
        if m_ctx:
            month_num = month_name_to_num[m_ctx.group(1).lower()]
            year_num = int(m_ctx.group(2))

        # Scan line-by-line; attach events to the most recent numeric day line.
        events: list[dict[str, Any]] = []
        current_day: Optional[int] = None
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        time_pat = re.compile(
            r"(?P<start>\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|am|pm)?)\s*-\s*"
            r"(?P<end>\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|am|pm)?)\s*:\s*"
            r"(?P<title>.+)$",
            flags=re.IGNORECASE,
        )

        for ln in lines:
            if re.fullmatch(r"\d{1,2}", ln):
                day_val = int(ln)
                if 1 <= day_val <= 31:
                    current_day = day_val
                continue

            mt = time_pat.search(ln)
            if not mt or current_day is None:
                continue

            dtstart = self._parse_clock(
                f"{year_num:04d}-{month_num:02d}-{current_day:02d}",
                mt.group("start"),
                tz,
            )
            dtend = self._parse_clock(
                f"{year_num:04d}-{month_num:02d}-{current_day:02d}",
                mt.group("end"),
                tz,
            )
            if not dtstart:
                continue

            title = self._clean_text(mt.group("title"))
            if not title:
                continue

            events.append({
                "title": title,
                "dtstart": dtstart,
                "dtend": dtend,
                "url": page_url,
            })

        return events

    def _iter_jsonld(self, obj: Any):
        if isinstance(obj, dict):
            if "@graph" in obj and isinstance(obj["@graph"], list):
                for item in obj["@graph"]:
                    yield from self._iter_jsonld(item)
            else:
                yield obj
        elif isinstance(obj, list):
            for item in obj:
                yield from self._iter_jsonld(item)

    def _pick_entry_datetime(self, entry: Any) -> Optional[datetime]:
        if getattr(entry, "published_parsed", None):
            return self._tm_to_dt(entry.published_parsed)
        if getattr(entry, "updated_parsed", None):
            return self._tm_to_dt(entry.updated_parsed)

        # Some feeds put date-like values in custom fields.
        for key in ("start", "startdate", "date"):
            val = entry.get(key)
            if isinstance(val, str):
                dt = self._parse_dt(val, ZoneInfo(self.timezone))
                if dt:
                    return dt
        return None

    def _tm_to_dt(self, tm_obj: Any) -> Optional[datetime]:
        try:
            tz = ZoneInfo(self.timezone)
            return datetime(*tm_obj[:6], tzinfo=tz)
        except Exception:
            return None

    def _ical_to_dt(self, comp_val: Any, tz: ZoneInfo) -> Optional[datetime]:
        if not comp_val:
            return None
        dt = getattr(comp_val, "dt", None)
        if not dt:
            return None
        if isinstance(dt, datetime):
            return dt if dt.tzinfo else dt.replace(tzinfo=tz)
        # date -> normalize to local midnight
        try:
            return datetime(dt.year, dt.month, dt.day, tzinfo=tz)
        except Exception:
            return None

    def _parse_dt(self, value: Any, tz: ZoneInfo) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        s = value.strip()
        # Normalize am/pm punctuation
        s = s.replace("a.m.", "AM").replace("p.m.", "PM")
        # ISO first
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=tz)
        except Exception:
            pass
        # Common textual formats
        patterns = [
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %H:%M",
            "%B %d, %Y %I:%M %p",
            "%b %d, %Y %I:%M %p",
            "%B %d %Y %I:%M %p",
            "%b %d %Y %I:%M %p",
        ]
        for pat in patterns:
            try:
                return datetime.strptime(s, pat).replace(tzinfo=tz)
            except Exception:
                continue
        return None

    def _parse_clock(self, date_iso: str, time_str: str, tz: ZoneInfo) -> Optional[datetime]:
        t = time_str.strip().replace("a.m.", "AM").replace("p.m.", "PM")
        for pat in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(f"{date_iso} {t}", pat).replace(tzinfo=tz)
            except Exception:
                continue
        return None

    def _as_text(self, val: Any) -> str:
        if val is None:
            return ""
        try:
            return str(val).strip()
        except Exception:
            return ""

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _dedupe(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, datetime]] = set()
        deduped: list[dict[str, Any]] = []
        for e in events:
            title = (e.get("title") or "").strip()
            dtstart = e.get("dtstart")
            if not title or not dtstart:
                continue
            key = (title.lower(), dtstart)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(e)
        return deduped


if __name__ == "__main__":
    VolunteerTorontoScraper.main()

