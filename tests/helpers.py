#!/usr/bin/env python3
"""
Shared helpers for community calendar ICS test files.

Provides make_ics(), make_vevent(), VTIMEZONE_LA, and VTIMEZONE_NY
for building minimal valid ICS content in pytest tests.

Used by:
  - tests/test_timezone_pipeline.py (original home)
  - tests/test_recurring_events.py (recurring event expansion tests)
"""


def make_ics(events_block, tz_header="X-WR-TIMEZONE:America/Los_Angeles", vtimezone=""):
    """Build a minimal valid ICS calendar string."""
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        f"{tz_header}\r\n"
        f"{vtimezone}"
        f"{events_block}"
        "END:VCALENDAR\r\n"
    )


def make_vevent(summary, dtstart, dtend, uid, rrule=None):
    """Build a VEVENT block. dtstart/dtend are full ICS property lines."""
    lines = [
        "BEGIN:VEVENT",
        dtstart,
        dtend,
        f"SUMMARY:{summary}",
        f"UID:{uid}",
    ]
    if rrule:
        lines.append(f"RRULE:{rrule}")
    lines.append("END:VEVENT")
    return "\r\n".join(lines) + "\r\n"


VTIMEZONE_LA = (
    "BEGIN:VTIMEZONE\r\n"
    "TZID:America/Los_Angeles\r\n"
    "BEGIN:STANDARD\r\n"
    "DTSTART:20241103T020000\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11\r\n"
    "TZOFFSETFROM:-0700\r\n"
    "TZOFFSETTO:-0800\r\n"
    "TZNAME:PST\r\n"
    "END:STANDARD\r\n"
    "BEGIN:DAYLIGHT\r\n"
    "DTSTART:20250309T020000\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3\r\n"
    "TZOFFSETFROM:-0800\r\n"
    "TZOFFSETTO:-0700\r\n"
    "TZNAME:PDT\r\n"
    "END:DAYLIGHT\r\n"
    "END:VTIMEZONE\r\n"
)

VTIMEZONE_NY = (
    "BEGIN:VTIMEZONE\r\n"
    "TZID:America/New_York\r\n"
    "BEGIN:STANDARD\r\n"
    "DTSTART:20241103T020000\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11\r\n"
    "TZOFFSETFROM:-0400\r\n"
    "TZOFFSETTO:-0500\r\n"
    "TZNAME:EST\r\n"
    "END:STANDARD\r\n"
    "BEGIN:DAYLIGHT\r\n"
    "DTSTART:20250309T020000\r\n"
    "RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3\r\n"
    "TZOFFSETFROM:-0500\r\n"
    "TZOFFSETTO:-0400\r\n"
    "TZNAME:EDT\r\n"
    "END:DAYLIGHT\r\n"
    "END:VTIMEZONE\r\n"
)
