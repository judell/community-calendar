#!/usr/bin/env python3
"""Record which sources ran, so the loader can scope its stale sweep.

A build run writes one manifest per city next to its calendars, listing the
``source_id`` stem of every source whose ingestion succeeded (issue #233).
The loader sweeps only those sources, so a quiet source is cleaned while a
failed one keeps its rows. A missing manifest means no runner reported and
the loader falls back to the pre-#233 payload-presence behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

FILENAME = "ran_sources.txt"
CALENDAR_MARKER = "BEGIN:VCALENDAR"


def is_calendar_body(text: str) -> bool:
    """True when the text is a complete calendar, not a block page or a truncation.

    A body that opens a calendar but never closes it (a cut-off download) is a
    failed ingestion, not a quiet source: combine_ics extracts no complete
    events from it, so recording it would sweep rows the source still has.
    """
    return CALENDAR_MARKER in text and "END:VCALENDAR" in text


def is_calendar(path: Path) -> bool:
    """True when the file holds a calendar, not a block page or error body."""
    try:
        return is_calendar_body(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return False


def record_ran(ics_path: Path) -> None:
    """Append the calendar's stem to the manifest sitting beside it.

    Appends rather than writes so the scraper and feed runners can both
    contribute to one city's manifest; the loader de-duplicates.
    """
    manifest = ics_path.parent / FILENAME
    with manifest.open("a") as f:
        f.write(ics_path.stem + "\n")
