#!/usr/bin/env python3
"""Scraper for Aga Khan Museum upcoming events."""

from __future__ import annotations

import html
import re
from datetime import date, datetime, time, timedelta
from typing import Iterable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from lib.base import BaseScraper


MONTH_RE = (
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
)


def _clean(text: str | None) -> str:
    text = html.unescape(text or "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class AgaKhanMuseumScraper(BaseScraper):
    name = "Aga Khan Museum"
    domain = "agakhanmuseum.org"
    timezone = "America/Toronto"
    page_url = "https://agakhanmuseum.org/"
    default_url = "https://agakhanmuseum.org/#upcoming-events"
    venue_address = "77 Wynford Drive, Toronto, ON M3C 1K1"

    def __init__(self) -> None:
        super().__init__()
        self.tz = ZoneInfo(self.timezone)

    def fetch_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self.fetch_text_with_curl(url), "html.parser")

    def fetch_upcoming_urls(self) -> list[str]:
        soup = self.fetch_soup(self.page_url)
        anchor = soup.select_one("#upcoming-events")
        if not anchor:
            raise ValueError("Upcoming events anchor not found")

        section = anchor.find_parent("section")
        if not section:
            raise ValueError("Upcoming events section not found")

        urls: list[str] = []
        seen: set[str] = set()
        for link in section.select("a.c-event-card__link[href]"):
            url = link.get("href", "").strip()
            if not url:
                continue
            url = urljoin(self.page_url, url)
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
        return urls

    def parse_date_fragment(self, fragment: str, default_year: int | None = None) -> date:
        fragment = _clean(fragment).replace(".", "")
        # Extract the "Month DD(, YYYY)" portion so decorated labels such as
        # "Doors Open • May 23, 2026" still parse.
        match = re.search(
            rf"\b({MONTH_RE})\s+(\d{{1,2}})(?:,?\s*(\d{{4}}))?\b", fragment, re.I
        )
        if match:
            month_name, day_str, year_str = match.groups()
            if year_str:
                fragment = f"{month_name} {day_str}, {year_str}"
            elif default_year:
                fragment = f"{month_name} {day_str}, {default_year}"
            else:
                # No year anywhere ("November 18"): assume the next occurrence.
                today = datetime.now(self.tz).date()
                for fmt in ("%B %d, %Y", "%b %d, %Y"):
                    try:
                        candidate = datetime.strptime(
                            f"{month_name} {day_str}, {today.year}", fmt
                        ).date()
                    except ValueError:
                        continue
                    if candidate < today - timedelta(days=45):
                        candidate = candidate.replace(year=today.year + 1)
                    return candidate
                fragment = f"{month_name} {day_str}, {today.year}"
        elif default_year and not re.search(r"\b\d{4}\b", fragment):
            fragment = f"{fragment}, {default_year}"
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(fragment, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unparseable date fragment: {fragment}")

    def parse_showtime_pairs(self, text: str) -> list[tuple[date, time]]:
        """Parse multi-showtime labels: "August 28 • 8 pm August 29 • 8 pm August 30 • 2 pm"."""
        normalized = _clean(text)
        pairs = re.findall(
            rf"\b({MONTH_RE}\s+\d{{1,2}}(?:,?\s*\d{{4}})?)\s*•\s*"
            rf"(\d{{1,2}}(?::\d{{2}})?\s*(?:am|pm))",
            normalized,
            re.I,
        )
        if len(pairs) < 2:
            return []
        year_match = re.search(r"(\d{4})", normalized)
        default_year = int(year_match.group(1)) if year_match else None
        showtimes: list[tuple[date, time]] = []
        for date_part, time_part in pairs:
            day = self.parse_date_fragment(date_part, default_year)
            showtimes.append((day, self.parse_time_value(time_part)))
        return showtimes

    def strip_weekdays(self, text: str) -> str:
        text = text.replace("New Date:", "").strip()
        text = text.replace("–", "-").replace("—", "-")
        text = re.sub(
            r"\b(?:Mon|Tue|Tues|Wed|Thu|Thur|Thurs|Fri|Sat|Sun|"
            r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+",
            "",
            text,
        )
        text = re.sub(r"\s*-\s*", "-", text)
        return _clean(text)

    def expand_date_label(self, text: str) -> list[date]:
        cleaned = self.strip_weekdays(text)
        year_match = re.search(r"(\d{4})", cleaned)
        default_year = int(year_match.group(1)) if year_match else None

        if " and " in cleaned:
            parts = [_clean(part) for part in cleaned.split(" and ")]
            return [self.parse_date_fragment(part, default_year) for part in parts]

        if "-" in cleaned:
            start_part, end_part = [_clean(part) for part in cleaned.split("-", 1)]
            end_date = self.parse_date_fragment(end_part, default_year)
            start_date = self.parse_date_fragment(start_part, end_date.year)
            dates: list[date] = []
            current = start_date
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)
            return dates

        return [self.parse_date_fragment(cleaned, default_year)]

    def parse_time_value(self, value: str) -> time:
        value = _clean(value).lower().replace(".", "")
        for fmt in ("%I:%M %p", "%I %p"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Unparseable time value: {value}")

    def parse_time_label(self, text: str) -> dict:
        normalized = _clean(text).lower().replace("–", "-").replace("—", "-").replace(".", "")
        if "-" in normalized:
            start_text, end_text = [_clean(part) for part in normalized.split("-", 1)]
            start_meridiem = re.search(r"\b(am|pm)\b", start_text)
            end_meridiem = re.search(r"\b(am|pm)\b", end_text)
            if not start_meridiem and end_meridiem:
                start_text = f"{start_text} {end_meridiem.group(1)}"
            if not end_meridiem and start_meridiem:
                end_text = f"{end_text} {start_meridiem.group(1)}"
            return {
                "kind": "range",
                "start": self.parse_time_value(start_text),
                "end": self.parse_time_value(end_text),
            }

        meridiem_match = re.search(r"\b(am|pm)\b", normalized)
        shared_meridiem = meridiem_match.group(1) if meridiem_match else None
        parts = [_clean(part) for part in re.split(r",|\band\b", normalized) if _clean(part)]
        times: list[time] = []
        for part in parts:
            if shared_meridiem and not re.search(r"\b(am|pm)\b", part):
                part = f"{part} {shared_meridiem}"
            times.append(self.parse_time_value(part))
        return {"kind": "list", "times": times}

    def combine_dt(self, day: date, at: time) -> datetime:
        return datetime.combine(day, at).replace(tzinfo=self.tz)

    def build_location(self, value: str | None) -> str:
        value = _clean(value)
        if not value:
            return f"Aga Khan Museum, {self.venue_address}"
        if "aga khan museum" in value.lower():
            return value
        return f"{value}, Aga Khan Museum, {self.venue_address}"

    def extract_description(self, soup: BeautifulSoup) -> str:
        parts: list[str] = []
        for paragraph in soup.select("section.c-container .c-col-text-area p"):
            text = _clean(paragraph.get_text(" ", strip=True))
            if not text or text == "&":
                continue
            parts.append(text)
            if len(parts) >= 3 or sum(len(p) for p in parts) >= 700:
                break
        return "\n\n".join(parts)

    def build_event(
        self,
        *,
        title: str,
        event_url: str,
        location: str,
        description: str,
        dtstart: datetime | date,
        dtend: datetime | date | None = None,
        image_url: str | None = None,
        uid_suffix: str | None = None,
    ) -> dict:
        uid_base = uid_suffix or f"{title}|{dtstart.isoformat()}"
        return {
            "title": title,
            "dtstart": dtstart,
            "dtend": dtend,
            "url": event_url,
            "location": location,
            "description": description,
            "image_url": image_url,
            "uid": f"{re.sub(r'[^a-z0-9]+', '-', uid_base.lower()).strip('-')}@{self.domain}",
        }

    def build_standard_events(
        self,
        *,
        title: str,
        event_url: str,
        location: str,
        description: str,
        image_url: str | None,
        date_label: str,
        time_label: str | None,
    ) -> list[dict]:
        showtimes = self.parse_showtime_pairs(date_label)
        if showtimes:
            return [
                self.build_event(
                    title=title,
                    event_url=event_url,
                    location=location,
                    description=description,
                    dtstart=self.combine_dt(day, start_time),
                    image_url=image_url,
                )
                for day, start_time in showtimes
            ]

        dates = self.expand_date_label(date_label)
        if not dates:
            return []

        if time_label:
            time_info = self.parse_time_label(time_label)
            if time_info["kind"] == "range":
                events = []
                for day in dates:
                    events.append(
                        self.build_event(
                            title=title,
                            event_url=event_url,
                            location=location,
                            description=description,
                            dtstart=self.combine_dt(day, time_info["start"]),
                            dtend=self.combine_dt(day, time_info["end"]),
                            image_url=image_url,
                        )
                    )
                return events

            events = []
            for day in dates:
                for start_time in time_info["times"]:
                    events.append(
                        self.build_event(
                            title=title,
                            event_url=event_url,
                            location=location,
                            description=description,
                            dtstart=self.combine_dt(day, start_time),
                            image_url=image_url,
                        )
                    )
            return events

        if len(dates) == 1:
            return [
                self.build_event(
                    title=title,
                    event_url=event_url,
                    location=location,
                    description=description,
                    dtstart=dates[0],
                    dtend=dates[0] + timedelta(days=1),
                    image_url=image_url,
                )
            ]

        return [
            self.build_event(
                title=title,
                event_url=event_url,
                location=location,
                description=description,
                dtstart=dates[0],
                dtend=dates[-1] + timedelta(days=1),
                image_url=image_url,
            )
        ]

    def build_bmo_free_wednesdays(
        self,
        *,
        title: str,
        event_url: str,
        location: str,
        description: str,
        image_url: str | None,
    ) -> list[dict]:
        now = datetime.now(self.tz)
        cutoff = now + timedelta(days=self.months_ahead * 31)
        current = now.date()
        while current.weekday() != 2:
            current += timedelta(days=1)

        events: list[dict] = []
        while current <= cutoff.date():
            start = self.combine_dt(current, time(16, 0))
            end = self.combine_dt(current, time(20, 0))
            if end >= now:
                events.append(
                    self.build_event(
                        title=title,
                        event_url=event_url,
                        location=location,
                        description=description,
                        dtstart=start,
                        dtend=end,
                        image_url=image_url,
                    )
                )
            current += timedelta(days=7)
        return events

    def parse_popup_week(self, label: str, month_name: str, year: int) -> list[date]:
        label = label.replace("–", "-").replace("—", "-")
        if "-" not in label:
            return []
        start_day, end_day = [_clean(part) for part in label.split("-", 1)]
        if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", start_day, re.I):
            start = self.parse_date_fragment(start_day, year)
        else:
            start = self.parse_date_fragment(f"{month_name} {start_day}", year)
        if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)", end_day, re.I):
            end = self.parse_date_fragment(end_day, year)
        else:
            end = self.parse_date_fragment(f"{month_name} {end_day}", year)
        days: list[date] = []
        current = start
        while current <= end:
            days.append(current)
            current += timedelta(days=1)
        return days

    def build_popup_events(
        self,
        *,
        soup: BeautifulSoup,
        title: str,
        event_url: str,
        location: str,
        description: str,
        image_url: str | None,
    ) -> list[dict]:
        now = datetime.now(self.tz)
        month_name = ""
        events: list[dict] = []
        year_match = re.search(r"\b(20\d{2})\b", title)
        popup_year = int(year_match.group(1)) if year_match else now.year

        for block in soup.select("div.c-col-biographies"):
            month_heading = block.select_one("div.c-wysiwyg.c-col-header h2")
            if month_heading:
                month_name = _clean(month_heading.get_text(" ", strip=True))

            for card in block.select("div.c-col-bio__details-container"):
                performer = _clean(card.select_one("h3.c-col-bio__name").get_text(" ", strip=True)) if card.select_one("h3.c-col-bio__name") else ""
                date_label = _clean(card.select_one("h4.c-col-bio__role").get_text(" ", strip=True)) if card.select_one("h4.c-col-bio__role") else ""
                if not performer or not date_label or not month_name:
                    continue

                for day in self.parse_popup_week(date_label, month_name, popup_year):
                    if day < now.date():
                        continue
                    if day.weekday() == 2:
                        starts = [time(17, 0), time(18, 0), time(19, 0)]
                    elif day.weekday() in (5, 6):
                        starts = [time(12, 0), time(13, 0), time(15, 0)]
                    else:
                        starts = []
                    for start_time in starts:
                        events.append(
                            self.build_event(
                                title=f"{title}: {performer}",
                                event_url=event_url,
                                location=location,
                                description=description,
                                dtstart=self.combine_dt(day, start_time),
                                image_url=image_url,
                                uid_suffix=f"{performer}|{day.isoformat()}|{start_time.isoformat()}",
                            )
                        )
        return events

    def parse_detail_page(self, url: str) -> list[dict]:
        soup = self.fetch_soup(url)
        masthead = None
        for section in soup.select("section.c-masthead"):
            if section.select_one("div.c-masthead__container h1.c-masthead__title"):
                masthead = section
                break
        if masthead is None:
            return []

        title_el = masthead.select_one("div.c-masthead__container h1.c-masthead__title")
        date_el = masthead.select_one("p.c-masthead__date-label")
        time_el = masthead.select_one("p.c-masthead__time-label")
        venue_el = masthead.select_one("p.c-masthead__venues-label")
        image_url = masthead.select_one("figure.c-masthead__img img")

        title = _clean(title_el.get_text(" ", strip=True)) if title_el else ""
        date_label = _clean(date_el.get_text(" ", strip=True)) if date_el else ""
        time_label = _clean(time_el.get_text(" ", strip=True)) if time_el else ""
        venue_label = _clean(venue_el.get_text(" ", strip=True)) if venue_el else ""
        image_src = image_url.get("src") if image_url else None
        location = self.build_location(venue_label)
        description = self.extract_description(soup)

        if not title:
            return []

        if url.rstrip("/").endswith("bmo-free-wednesdays"):
            return self.build_bmo_free_wednesdays(
                title=title,
                event_url=url,
                location=location,
                description=description,
                image_url=image_src,
            )

        if url.rstrip("/").endswith("2026-td-pop-up-performances"):
            return self.build_popup_events(
                soup=soup,
                title=title,
                event_url=url,
                location=location,
                description=description,
                image_url=image_src,
            )

        if not date_label:
            return []

        return self.build_standard_events(
            title=title,
            event_url=url,
            location=location,
            description=description,
            image_url=image_src,
            date_label=date_label,
            time_label=time_label or None,
        )

    def dedupe_events(self, events: Iterable[dict]) -> list[dict]:
        deduped: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for event in events:
            dtstart = event.get("dtstart")
            key = (event.get("title", ""), dtstart.isoformat() if dtstart else "")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(event)
        return deduped

    def fetch_events(self) -> list[dict]:
        urls = self.fetch_upcoming_urls()
        all_events: list[dict] = []
        for url in urls:
            try:
                all_events.extend(self.parse_detail_page(url))
            except Exception as exc:
                self.logger.warning(f"Failed to parse {url}: {exc}")
        now = datetime.now(self.tz)
        filtered = []
        for event in self.dedupe_events(all_events):
            dtstart = event.get("dtstart")
            if isinstance(dtstart, datetime):
                if dtstart >= now:
                    filtered.append(event)
            elif isinstance(dtstart, date):
                if dtstart >= now.date():
                    filtered.append(event)
        return filtered


if __name__ == "__main__":
    AgaKhanMuseumScraper.main()
