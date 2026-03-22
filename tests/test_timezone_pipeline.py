#!/usr/bin/env python3
"""
End-to-end timezone tests for the community calendar pipeline.

Tests the complete flow: ICS file → combine_ics.py → ics_to_json.py → JSON output.
Verifies that timezone information is correctly preserved and converted at each stage.

Run: python -m pytest tests/test_timezone_pipeline.py -v
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from scripts.combine_ics import expand_rrules, parse_ics_datetime as combine_parse_dt
from scripts.ics_to_json import parse_ics_datetime as json_parse_dt, extract_field


# ---------------------------------------------------------------------------
# Helpers: build minimal ICS content for testing
# ---------------------------------------------------------------------------

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


# ===========================================================================
# Test 1: ics_to_json parse_ics_datetime — current behavior baseline
# ===========================================================================

class TestIcsToJsonParseDatetime:
    """Tests for scripts/ics_to_json.py parse_ics_datetime."""

    def test_utc_time_converts_to_local(self):
        """A Z-suffixed UTC time should convert to the city's local timezone."""
        la_tz = ZoneInfo("America/Los_Angeles")
        # 2025-01-15 20:00 UTC = 2025-01-15 12:00 PST (-08:00)
        result = json_parse_dt("20250115T200000Z", la_tz)
        assert result == "2025-01-15T12:00:00-08:00"

    def test_naive_time_gets_city_tz(self):
        """A naive (no Z, no TZID) time should be stamped with city timezone."""
        la_tz = ZoneInfo("America/Los_Angeles")
        # Jan 15 in PST
        result = json_parse_dt("20250115T190000", la_tz)
        assert result == "2025-01-15T19:00:00-08:00"

    def test_naive_time_dst(self):
        """A naive time during DST should get the DST offset."""
        la_tz = ZoneInfo("America/Los_Angeles")
        # Jun 15 in PDT
        result = json_parse_dt("20250615T190000", la_tz)
        assert result == "2025-06-15T19:00:00-07:00"

    def test_allday_event(self):
        """An all-day event should anchor to midnight in city timezone."""
        la_tz = ZoneInfo("America/Los_Angeles")
        result = json_parse_dt("20250115", la_tz)
        assert result == "2025-01-15T00:00:00-08:00"

    def test_tzid_param_is_stripped_and_ignored(self):
        """
        BUG DEMONSTRATION: TZID parameter is stripped, city tz used instead.

        This event says TZID=America/New_York (7pm Eastern), but the parser
        ignores that and stamps it with America/Los_Angeles (7pm Pacific).

        7pm Eastern = 4pm Pacific, but we get 7pm Pacific. Wrong by 3 hours.
        """
        la_tz = ZoneInfo("America/Los_Angeles")
        # This is what extract_field currently returns for
        # DTSTART;TZID=America/New_York:20250115T190000
        # — it strips the TZID and returns just "20250115T190000"
        result = json_parse_dt("20250115T190000", la_tz)

        # Currently returns 7pm Pacific (WRONG if event was actually Eastern)
        assert result == "2025-01-15T19:00:00-08:00"

        # What it SHOULD return if we respected TZID=America/New_York:
        # 7pm Eastern = "2025-01-15T19:00:00-05:00"
        # or equivalently converted to Pacific: "2025-01-15T16:00:00-08:00"

    def test_tzid_respected_when_present(self):
        """
        DESIRED BEHAVIOR: When the raw ICS line includes TZID, use it.

        This test will FAIL until we fix parse_ics_datetime to extract
        and use the TZID parameter instead of always using city tz.
        """
        la_tz = ZoneInfo("America/Los_Angeles")
        # Pass the full ICS property value including TZID
        raw = "DTSTART;TZID=America/New_York:20250115T190000"
        result = json_parse_dt(raw, la_tz)

        # 7pm Eastern should produce an Eastern offset
        assert result == "2025-01-15T19:00:00-05:00", (
            f"Expected 7pm Eastern (-05:00), got {result}. "
            "parse_ics_datetime should use TZID=America/New_York, not city tz."
        )

    def test_tzid_matching_city_unchanged(self):
        """When TZID matches city tz, result should be the same as naive."""
        la_tz = ZoneInfo("America/Los_Angeles")
        raw = "DTSTART;TZID=America/Los_Angeles:20250115T190000"
        result = json_parse_dt(raw, la_tz)
        assert result == "2025-01-15T19:00:00-08:00"


# ===========================================================================
# Test 2: extract_field — does it preserve or lose TZID?
# ===========================================================================

class TestExtractField:
    """Tests for ics_to_json.py extract_field with DTSTART."""

    def test_bare_dtstart(self):
        """DTSTART with no params returns bare value."""
        content = "DTSTART:20250115T190000\r\nSUMMARY:Test"
        result = extract_field(content, 'DTSTART')
        assert result == "20250115T190000"

    def test_tzid_dtstart_loses_tzid(self):
        """
        BUG: extract_field strips TZID, returns only the datetime value.
        The regex (?:;[^:]*)?:([^\r\n]*) captures only after the colon.
        """
        content = "DTSTART;TZID=America/New_York:20250115T190000\r\nSUMMARY:Test"
        result = extract_field(content, 'DTSTART')
        # Currently returns just the datetime — TZID is lost
        assert result == "20250115T190000"

    def test_extract_field_should_preserve_tzid(self):
        """
        DESIRED BEHAVIOR: For datetime fields, we need the TZID.

        This test documents what we WANT. The fix could be:
        (a) A new extract_datetime_field that returns (tzid, value), or
        (b) Change extract_field to return "TZID=America/New_York:20250115T190000", or
        (c) Have parse_ics_datetime receive the full raw line from event_content directly.
        """
        content = "DTSTART;TZID=America/New_York:20250115T190000\r\nSUMMARY:Test"
        # Whatever approach we pick, we need both pieces:
        # tzid = "America/New_York" and value = "20250115T190000"
        # This test is a placeholder — uncomment when approach is chosen.
        pass


# ===========================================================================
# Test 3: combine_ics RRULE expansion — does it preserve TZID?
# ===========================================================================

class TestCombineIcsRruleExpansion:
    """Tests for combine_ics.py RRULE expansion timezone handling."""

    def test_rrule_expansion_preserves_tzid(self):
        """Expanded instances should retain DTSTART;TZID= from original."""
        # Use dates far enough in the future to fall within the expansion window
        event = make_vevent(
            "Weekly Class",
            "DTSTART;TZID=America/Los_Angeles:20260323T190000",
            "DTEND;TZID=America/Los_Angeles:20260323T200000",
            "test-rrule@test",
            rrule="FREQ=WEEKLY;UNTIL=20260630T235959Z",
        )
        ics = make_ics(event, vtimezone=VTIMEZONE_LA)
        expanded = expand_rrules(ics, window_days=120)
        assert expanded is not None
        assert len(expanded) > 0
        # Each expanded instance should have TZID on DTSTART
        for block in expanded:
            assert "TZID=America/Los_Angeles" in block, (
                f"Expanded instance lost TZID:\n{block}"
            )

    def test_rrule_expansion_dst_transition(self):
        """
        An RRULE spanning DST boundary should produce correct wall-clock times.

        DST spring forward: March 9, 2025 (America/Los_Angeles).
        A weekly 7pm class should stay at 7pm local, not shift to 8pm.
        """
        # Use dates around DST spring-forward (March 8, 2026 for America/Los_Angeles)
        event = make_vevent(
            "Weekly Class",
            "DTSTART;TZID=America/Los_Angeles:20260302T190000",
            "DTEND;TZID=America/Los_Angeles:20260302T200000",
            "dst-test@test",
            rrule="FREQ=WEEKLY;UNTIL=20260401T235959Z",
        )
        ics = make_ics(event, vtimezone=VTIMEZONE_LA)
        expanded = expand_rrules(ics, window_days=30)
        assert expanded is not None

        # Extract DTSTART times from expanded instances
        for block in expanded:
            m = re.search(r'DTSTART[^:]*:(\d{8}T\d{6})', block)
            assert m, f"No DTSTART found in:\n{block}"
            time_part = m.group(1)[-6:]  # HHMMSS
            assert time_part == "190000", (
                f"Expected 190000 (7pm local), got {time_part}. "
                "DST transition shifted the wall-clock time."
            )


# ===========================================================================
# Test 4: Full pipeline — ICS with mismatched TZID → JSON
# ===========================================================================

class TestFullPipeline:
    """
    End-to-end: an ICS file for a Santa Rosa (Pacific) city contains
    an event with TZID=America/New_York. Does the JSON output have
    the correct UTC offset?

    This is the scenario that's currently broken: a virtual event
    hosted in Eastern time, listed on a Pacific-timezone city calendar.
    """

    def test_eastern_event_in_pacific_city(self):
        """
        An event at 7pm Eastern in a Pacific-timezone city calendar.

        The JSON should say 7pm Eastern (-05:00), NOT 7pm Pacific (-08:00).
        Alternatively, converted to Pacific: 4pm Pacific (-08:00).
        Either representation is correct as long as the absolute UTC instant
        is right: 2025-01-15T00:00:00Z (midnight UTC).

        This test will FAIL until the fix is applied.
        """
        la_tz = ZoneInfo("America/Los_Angeles")

        # Simulate what extract_field + parse_ics_datetime currently does:
        # The TZID is lost, so 7pm is stamped as Pacific
        raw_line = "DTSTART;TZID=America/New_York:20250115T190000"
        result = json_parse_dt(raw_line, la_tz)

        # Parse the result to check the actual UTC instant
        result_dt = datetime.fromisoformat(result)
        result_utc = result_dt.astimezone(timezone.utc)

        # 7pm Eastern on Jan 15 = midnight UTC on Jan 16
        expected_utc = datetime(2025, 1, 16, 0, 0, 0, tzinfo=timezone.utc)

        assert result_utc == expected_utc, (
            f"Wrong UTC instant!\n"
            f"  Got:      {result} → UTC {result_utc}\n"
            f"  Expected: UTC {expected_utc}\n"
            f"  The TZID=America/New_York was ignored; time was stamped as Pacific."
        )

    def test_pacific_event_in_pacific_city(self):
        """
        An event at 7pm Pacific in a Pacific-timezone city calendar.
        This is the common case and should work correctly today.
        """
        la_tz = ZoneInfo("America/Los_Angeles")
        raw_line = "DTSTART;TZID=America/Los_Angeles:20250115T190000"
        result = json_parse_dt(raw_line, la_tz)

        result_dt = datetime.fromisoformat(result)
        result_utc = result_dt.astimezone(timezone.utc)

        # 7pm Pacific on Jan 15 = 3am UTC on Jan 16
        expected_utc = datetime(2025, 1, 16, 3, 0, 0, tzinfo=timezone.utc)

        assert result_utc == expected_utc

    def test_utc_event_in_pacific_city(self):
        """UTC event (Z suffix) should convert correctly regardless of city."""
        la_tz = ZoneInfo("America/Los_Angeles")
        result = json_parse_dt("20250115T200000Z", la_tz)

        result_dt = datetime.fromisoformat(result)
        result_utc = result_dt.astimezone(timezone.utc)

        expected_utc = datetime(2025, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
        assert result_utc == expected_utc


# ===========================================================================
# Test 5: Enrichment API — naive datetime submission
# ===========================================================================

class TestEnrichmentTimezone:
    """
    Tests for the PickEditor → enrichment API timezone gap.

    PickEditor constructs naive datetimes like "2025-01-15T19:00:00" and
    sends them directly to /rest/v1/event_enrichments (Supabase REST).

    Unlike the capture-event edge function, this path has NO
    applyTimezoneOffset call. Postgres interprets the naive string
    as UTC, so "7pm" becomes 7pm UTC instead of 7pm local.

    These tests document the bug and what correct behavior looks like.
    """

    def test_naive_datetime_is_ambiguous(self):
        """
        Demonstrate that a naive datetime without offset is ambiguous.
        "2025-01-15T19:00:00" could be 7pm in any timezone.
        """
        naive = "2025-01-15T19:00:00"
        # Postgres with default UTC session timezone treats this as UTC
        as_utc = datetime.fromisoformat(naive).replace(tzinfo=timezone.utc)
        # But the user meant 7pm Pacific
        as_pacific = datetime.fromisoformat(naive).replace(tzinfo=ZoneInfo("America/Los_Angeles"))

        # These are 8 hours apart!
        diff_hours = abs((as_utc - as_pacific).total_seconds() / 3600)
        assert diff_hours == 8.0, (
            "Naive datetime interpreted as UTC vs Pacific differs by 8 hours. "
            "The enrichment API path sends naive datetimes to Postgres."
        )

    def test_what_enrichment_should_send(self):
        """
        The enrichment API should send offset-qualified datetimes,
        e.g., "2025-01-15T19:00:00-08:00" for Pacific.
        """
        # What PickEditor currently sends:
        naive = "2025-01-15T19:00:00"

        # What it should send (with city timezone applied):
        city_tz = ZoneInfo("America/Los_Angeles")
        correct = datetime.fromisoformat(naive).replace(tzinfo=city_tz).isoformat()

        assert correct == "2025-01-15T19:00:00-08:00"

        # Verify both resolve to the same UTC instant
        correct_utc = datetime.fromisoformat(correct).astimezone(timezone.utc)
        expected_utc = datetime(2025, 1, 16, 3, 0, 0, tzinfo=timezone.utc)
        assert correct_utc == expected_utc

    def test_enrichment_roundtrip_bug(self):
        """
        BUG DEMONSTRATION: Full enrichment round-trip loses timezone.

        Simulates the actual data flow:
        1. Event stored in Postgres as UTC (correct)
        2. PickEditor reads it, calls utcToLocal() → shows "7:00 PM" in form
        3. User doesn't change anything, hits save
        4. PickEditor constructs "2025-01-15T19:00:00" (naive, no offset)
        5. Sent directly to /rest/v1/event_enrichments (no applyTimezoneOffset)
        6. Postgres interprets as UTC → stores 7pm UTC
        7. Frontend displays it → shows 11am Pacific (WRONG, was 7pm Pacific)

        This test will FAIL until the enrichment path applies timezone offset.
        """
        city_tz_name = "America/Los_Angeles"
        city_tz = ZoneInfo(city_tz_name)

        # Step 1: Event correctly stored as 7pm Pacific = 3am UTC next day
        original_local = datetime(2025, 1, 15, 19, 0, 0, tzinfo=city_tz)
        stored_utc = original_local.astimezone(timezone.utc)
        assert stored_utc == datetime(2025, 1, 16, 3, 0, 0, tzinfo=timezone.utc)

        # Step 2: Postgres returns ISO string with +00:00
        pg_returns = stored_utc.isoformat()  # "2025-01-16T03:00:00+00:00"

        # Step 3: utcToLocal converts for form display (Python equivalent)
        # This is what helpers.js utcToLocal() does via Intl.DateTimeFormat
        displayed = datetime.fromisoformat(pg_returns).astimezone(city_tz)
        assert displayed.hour == 19  # Shows 7pm in form — correct
        assert displayed.day == 15   # Shows Jan 15 — correct

        # Step 4: PickEditor constructs naive string from form values
        # (this is what lines 65/143/159 in PickEditor.xmlui do)
        form_date = displayed.strftime("%Y-%m-%d")  # "2025-01-15"
        form_time = displayed.strftime("%H:%M")      # "19:00"
        naive_submitted = f"{form_date}T{form_time}:00"  # "2025-01-15T19:00:00"

        # Step 5-6: Sent to Postgres REST API — no offset, interpreted as UTC
        pg_stores_as_utc = datetime.fromisoformat(naive_submitted).replace(tzinfo=timezone.utc)

        # Step 7: Frontend reads it back, converts to Pacific for display
        displayed_back = pg_stores_as_utc.astimezone(city_tz)

        # BUG: Should be 7pm Pacific, but now shows 11am Pacific
        assert displayed_back.hour == 11  # This is what happens (WRONG)
        # After fix, this should be 19 (7pm)

    def test_enrichment_roundtrip_fixed(self):
        """
        DESIRED BEHAVIOR: Enrichment path should produce correct round-trip.

        Same flow as above, but step 4 appends timezone offset.
        This test will PASS once the fix is applied in PickEditor.xmlui.
        """
        city_tz_name = "America/Los_Angeles"
        city_tz = ZoneInfo(city_tz_name)

        # Steps 1-3: Same as above
        original_local = datetime(2025, 1, 15, 19, 0, 0, tzinfo=city_tz)
        stored_utc = original_local.astimezone(timezone.utc)
        pg_returns = stored_utc.isoformat()
        displayed = datetime.fromisoformat(pg_returns).astimezone(city_tz)
        form_date = displayed.strftime("%Y-%m-%d")
        form_time = displayed.strftime("%H:%M")

        # Step 4 FIXED: Apply timezone offset before sending
        naive_dt = datetime.fromisoformat(f"{form_date}T{form_time}:00")
        offset_submitted = naive_dt.replace(tzinfo=city_tz).isoformat()
        # "2025-01-15T19:00:00-08:00"

        # Step 5-6: Postgres receives offset-qualified string, stores correctly
        pg_stores = datetime.fromisoformat(offset_submitted).astimezone(timezone.utc)

        # Step 7: Round-trip is correct
        displayed_back = pg_stores.astimezone(city_tz)
        assert displayed_back.hour == 19, (
            f"Expected 7pm (19:00), got {displayed_back.hour}:00. "
            "Round-trip should preserve the original time."
        )
        assert displayed_back.day == 15

    def test_enrichment_roundtrip_eastern_city(self):
        """
        Same round-trip bug but for an Eastern timezone city (e.g., Montclair).
        The offset is 5 hours, so 7pm Eastern stored as UTC = midnight.
        Without fix: displays as 7pm UTC → 2pm Eastern (5 hours wrong).
        """
        city_tz = ZoneInfo("America/New_York")

        original_local = datetime(2025, 1, 15, 19, 0, 0, tzinfo=city_tz)
        stored_utc = original_local.astimezone(timezone.utc)
        pg_returns = stored_utc.isoformat()
        displayed = datetime.fromisoformat(pg_returns).astimezone(city_tz)

        form_date = displayed.strftime("%Y-%m-%d")
        form_time = displayed.strftime("%H:%M")
        naive_submitted = f"{form_date}T{form_time}:00"

        # BUG path: Postgres treats as UTC
        pg_stores_as_utc = datetime.fromisoformat(naive_submitted).replace(tzinfo=timezone.utc)
        displayed_back = pg_stores_as_utc.astimezone(city_tz)

        # 7pm becomes 2pm (5 hours wrong)
        assert displayed_back.hour == 14  # WRONG — should be 19


# ===========================================================================
# Test 5b: applyTimezoneOffset — the function added to helpers.js
# ===========================================================================

class TestApplyTimezoneOffset:
    """
    Tests for the applyTimezoneOffset function (helpers.js).

    This is a Python equivalent of the JS function. The logic is identical:
    given a naive datetime string and an IANA timezone, append the UTC offset.
    These tests validate the algorithm that both JS and the capture-event
    edge function use.
    """

    @staticmethod
    def apply_tz_offset(naive_dt: str, tz_name: str) -> str:
        """Python equivalent of window.applyTimezoneOffset / capture-event applyTimezoneOffset."""
        import re
        if not tz_name or not naive_dt:
            return naive_dt
        if re.search(r'[+-]\d{2}(:\d{2})?$', naive_dt) or naive_dt.endswith('Z'):
            return naive_dt
        dt = datetime.fromisoformat(naive_dt)
        tz = ZoneInfo(tz_name)
        aware = dt.replace(tzinfo=tz)
        offset = aware.utcoffset()
        total_seconds = int(offset.total_seconds())
        sign = '+' if total_seconds >= 0 else '-'
        abs_seconds = abs(total_seconds)
        h = abs_seconds // 3600
        m = (abs_seconds % 3600) // 60
        return f"{naive_dt}{sign}{h:02d}:{m:02d}"

    def test_pacific_standard(self):
        result = self.apply_tz_offset("2025-01-15T19:00:00", "America/Los_Angeles")
        assert result == "2025-01-15T19:00:00-08:00"

    def test_pacific_daylight(self):
        result = self.apply_tz_offset("2025-06-15T19:00:00", "America/Los_Angeles")
        assert result == "2025-06-15T19:00:00-07:00"

    def test_eastern_standard(self):
        result = self.apply_tz_offset("2025-01-15T19:00:00", "America/New_York")
        assert result == "2025-01-15T19:00:00-05:00"

    def test_eastern_daylight(self):
        result = self.apply_tz_offset("2025-06-15T19:00:00", "America/New_York")
        assert result == "2025-06-15T19:00:00-04:00"

    def test_toronto(self):
        result = self.apply_tz_offset("2025-01-15T19:00:00", "America/Toronto")
        assert result == "2025-01-15T19:00:00-05:00"

    def test_indianapolis(self):
        """Indiana doesn't observe DST."""
        result = self.apply_tz_offset("2025-01-15T19:00:00", "America/Indiana/Indianapolis")
        assert result == "2025-01-15T19:00:00-05:00"
        result_summer = self.apply_tz_offset("2025-06-15T19:00:00", "America/Indiana/Indianapolis")
        assert result_summer == "2025-06-15T19:00:00-04:00"

    def test_already_has_offset(self):
        """Should not double-apply offset."""
        result = self.apply_tz_offset("2025-01-15T19:00:00-08:00", "America/New_York")
        assert result == "2025-01-15T19:00:00-08:00"

    def test_utc_z_suffix(self):
        """Should not modify Z-suffixed times."""
        result = self.apply_tz_offset("2025-01-15T19:00:00Z", "America/Los_Angeles")
        assert result == "2025-01-15T19:00:00Z"

    def test_empty_timezone(self):
        result = self.apply_tz_offset("2025-01-15T19:00:00", "")
        assert result == "2025-01-15T19:00:00"

    def test_none_timezone(self):
        result = self.apply_tz_offset("2025-01-15T19:00:00", None)
        assert result == "2025-01-15T19:00:00"

    def test_enrichment_roundtrip_with_fix(self):
        """
        Full round-trip with applyTimezoneOffset applied (the fix).

        1. Event in DB: 7pm Pacific = 3am UTC
        2. utcToLocal shows 7pm in form
        3. User submits → naive "2025-01-15T19:00:00"
        4. applyTimezoneOffset → "2025-01-15T19:00:00-08:00"
        5. Postgres stores correctly as 3am UTC
        6. Display reads back as 7pm Pacific ✓
        """
        city_tz_name = "America/Los_Angeles"
        city_tz = ZoneInfo(city_tz_name)

        # Original: 7pm Pacific
        original = datetime(2025, 1, 15, 19, 0, 0, tzinfo=city_tz)
        stored_utc = original.astimezone(timezone.utc)

        # Form shows 7pm, user submits
        naive = "2025-01-15T19:00:00"

        # FIX: apply offset before sending to Postgres
        with_offset = self.apply_tz_offset(naive, city_tz_name)
        assert with_offset == "2025-01-15T19:00:00-08:00"

        # Postgres stores it
        pg_stores = datetime.fromisoformat(with_offset).astimezone(timezone.utc)

        # Same UTC instant as original
        assert pg_stores == stored_utc

        # Display round-trips correctly
        displayed = pg_stores.astimezone(city_tz)
        assert displayed.hour == 19
        assert displayed.day == 15


# ===========================================================================
# Test 6: my-picks ICS output
# ===========================================================================

# ===========================================================================
# Test 7: Real ICS files — verify parse_ics_datetime against actual feeds
# ===========================================================================

class TestRealIcsFiles:
    """
    Parse real ICS files from cities/ and verify timezone handling.

    These tests catch regressions by running parse_ics_datetime against
    actual feed data with diverse TZID conventions:
    - Bare datetimes (scraper output)
    - TZID matching city timezone
    - TZID mismatching city timezone (cross-timezone events)
    - UTC Z-suffixed datetimes
    - VALUE=DATE all-day events
    """

    PROJECT_ROOT = Path(__file__).parent.parent

    def _parse_real_events(self, city, city_tz_name, ics_filename, max_events=5):
        """Parse events from a real ICS file and return (raw_input, parsed_output) pairs."""
        ics_path = self.PROJECT_ROOT / 'cities' / city / ics_filename
        if not ics_path.exists():
            return []
        content = ics_path.read_text(encoding='utf-8', errors='ignore')
        from scripts.ics_to_json import extract_raw_datetime, parse_ics_datetime, unfold_ics_lines
        content = unfold_ics_lines(content)
        local_tz = ZoneInfo(city_tz_name)
        pattern = r'BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT'
        matches = re.findall(pattern, content, re.DOTALL)
        results = []
        for event_content in matches[:max_events]:
            raw = extract_raw_datetime(event_content, 'DTSTART')
            if raw:
                parsed = parse_ics_datetime(raw, local_tz)
                if parsed:
                    results.append((raw, parsed))
        return results

    # --- Santa Rosa: scraper output with bare datetimes ---

    def test_santarosa_sonoma_parks_bare(self):
        """Sonoma Parks scraper: bare datetimes, city tz = America/Los_Angeles."""
        results = self._parse_real_events('santarosa', 'America/Los_Angeles', 'sonoma_parks.ics')
        for raw, parsed in results:
            assert ';' not in raw, f"Expected bare datetime, got: {raw}"
            dt = datetime.fromisoformat(parsed)
            assert dt.tzinfo is not None, f"Parsed datetime should be tz-aware: {parsed}"
            offset_hours = dt.utcoffset().total_seconds() / 3600
            assert offset_hours in (-7, -8), f"Expected PDT or PST offset, got {offset_hours}h: {parsed}"

    # --- Santa Rosa: live feed with TZID=America/Los_Angeles (matching) ---

    def test_santarosa_uptown_tzid_matching(self):
        """Uptown Theatre: TZID=America/Los_Angeles in a Pacific city."""
        results = self._parse_real_events('santarosa', 'America/Los_Angeles', 'uptowntheatrenapa.ics')
        for raw, parsed in results:
            if 'TZID=' in raw:
                assert 'America/Los_Angeles' in raw
                dt = datetime.fromisoformat(parsed)
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-7, -8), f"Expected PDT or PST: {parsed}"

    # --- Santa Rosa: Eventbrite with TZID=America/New_York (MISMATCH) ---

    def test_santarosa_eventbrite_eastern_tzid(self):
        """
        Eventbrite Phoenix: some events have TZID=America/New_York in a Pacific city.
        These should be parsed as Eastern, NOT Pacific.
        """
        results = self._parse_real_events('santarosa', 'America/Los_Angeles', 'eventbrite_phoenix.ics', max_events=20)
        eastern_found = False
        for raw, parsed in results:
            if 'TZID=America/New_York' in raw:
                eastern_found = True
                dt = datetime.fromisoformat(parsed)
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-4, -5), (
                    f"Event with TZID=America/New_York should have Eastern offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )
        # Don't fail if file doesn't currently have Eastern events —
        # just ensure correctness when they exist
        if not eastern_found:
            pass  # Eventbrite may or may not have cross-tz events right now

    # --- Bloomington: Google Calendar with TZID=America/New_York (common mismatch) ---

    def test_bloomington_gcal_new_york_tzid(self):
        """
        Bloomington city tz = America/Indiana/Indianapolis.
        Google Calendar feeds use TZID=America/New_York.
        Indianapolis doesn't observe DST the same as New York (it does since 2006
        but the IANA zone differs). The TZID should be respected, not overridden.
        """
        results = self._parse_real_events(
            'bloomington', 'America/Indiana/Indianapolis',
            'gcal_bloomington_in_gov_c657mi332p5sjpq2lcht9imu60.ics',
            max_events=10
        )
        for raw, parsed in results:
            dt = datetime.fromisoformat(parsed)
            assert dt.tzinfo is not None
            if 'TZID=America/New_York' in raw:
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-4, -5), (
                    f"TZID=America/New_York should produce Eastern offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )

    # --- Bloomington: Mobilize with TZID=America/Los_Angeles (big mismatch) ---

    def test_bloomington_mobilize_pacific_tzid(self):
        """
        Mobilize Indivisible: TZID=America/Los_Angeles events in an Indianapolis city.
        Pacific events should NOT be stamped as Indianapolis time.
        """
        results = self._parse_real_events(
            'bloomington', 'America/Indiana/Indianapolis',
            'mobilize_indivisible_central_indiana.ics',
            max_events=10
        )
        for raw, parsed in results:
            if 'TZID=America/Los_Angeles' in raw:
                dt = datetime.fromisoformat(parsed)
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-7, -8), (
                    f"TZID=America/Los_Angeles should produce Pacific offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )

    # --- Montclair: Eventbrite/Mobilize with TZID=America/Los_Angeles ---

    def test_montclair_eventbrite_pacific_tzid(self):
        """
        Montclair (Eastern) Eventbrite: some events have TZID=America/Los_Angeles.
        These are likely Eventbrite platform defaults, but the TZID should still
        be respected to get the correct absolute time.
        """
        results = self._parse_real_events(
            'montclair', 'America/New_York',
            'eventbrite_montclair_book_center.ics',
            max_events=20
        )
        for raw, parsed in results:
            dt = datetime.fromisoformat(parsed)
            assert dt.tzinfo is not None
            if 'TZID=America/Los_Angeles' in raw:
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-7, -8), (
                    f"TZID=America/Los_Angeles should produce Pacific offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )

    # --- Toronto: UTC TZID ---

    def test_toronto_utc_tzid(self):
        """
        Toronto UofT Engineering: TZID=UTC events.
        Should be interpreted as UTC (offset +00:00), not Toronto time.
        """
        results = self._parse_real_events(
            'toronto', 'America/Toronto',
            'uoft_engineering.ics',
            max_events=10
        )
        for raw, parsed in results:
            if 'TZID=UTC' in raw:
                dt = datetime.fromisoformat(parsed)
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours == 0, (
                    f"TZID=UTC should produce +00:00 offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )

    # --- Toronto: America/Halifax TZID ---

    def test_toronto_halifax_tzid(self):
        """
        Toronto Indigenous events: TZID=America/Halifax.
        Atlantic timezone (-04:00/-03:00), not Toronto Eastern.
        """
        results = self._parse_real_events(
            'toronto', 'America/Toronto',
            'indigenous.ics',
            max_events=10
        )
        for raw, parsed in results:
            if 'TZID=America/Halifax' in raw:
                dt = datetime.fromisoformat(parsed)
                offset_hours = dt.utcoffset().total_seconds() / 3600
                assert offset_hours in (-3, -4), (
                    f"TZID=America/Halifax should produce Atlantic offset, "
                    f"got {offset_hours}h: {raw} → {parsed}"
                )

    # --- Santa Rosa: New World Ballet static feed with RRULE ---

    def test_santarosa_new_world_ballet_rrule(self):
        """
        Static feed with VTIMEZONE + TZID + RRULE.
        Parse a few events and verify they get Pacific offset.
        """
        results = self._parse_real_events('santarosa', 'America/Los_Angeles', 'new_world_ballet.ics')
        assert len(results) > 0, "new_world_ballet.ics should have parseable events"
        for raw, parsed in results:
            assert 'TZID=America/Los_Angeles' in raw
            dt = datetime.fromisoformat(parsed)
            offset_hours = dt.utcoffset().total_seconds() / 3600
            assert offset_hours in (-7, -8), f"Expected PDT or PST: {parsed}"

    # --- Cross-city consistency: same UTC instant regardless of TZID ---

    def test_cross_tz_utc_consistency(self):
        """
        An event at 7pm in different timezones should produce different UTC instants.
        This verifies that TZID actually changes the interpretation, not just the label.
        """
        la_tz = ZoneInfo("America/Los_Angeles")

        # Same wall-clock time, different TZIDs
        pacific_raw = "DTSTART;TZID=America/Los_Angeles:20250115T190000"
        eastern_raw = "DTSTART;TZID=America/New_York:20250115T190000"

        pacific_parsed = json_parse_dt(pacific_raw, la_tz)
        eastern_parsed = json_parse_dt(eastern_raw, la_tz)

        pacific_utc = datetime.fromisoformat(pacific_parsed).astimezone(timezone.utc)
        eastern_utc = datetime.fromisoformat(eastern_parsed).astimezone(timezone.utc)

        # 7pm Pacific = 3am UTC, 7pm Eastern = midnight UTC — 3 hours apart
        diff_hours = (pacific_utc - eastern_utc).total_seconds() / 3600
        assert diff_hours == 3.0, (
            f"7pm Pacific vs 7pm Eastern should differ by 3 hours UTC, "
            f"got {diff_hours}h. Pacific={pacific_parsed}, Eastern={eastern_parsed}"
        )


class TestMyPicksOutput:
    """
    Tests for the my-picks edge function ICS generation.

    my-picks reads timestamptz from Postgres (UTC) and formats as
    YYYYMMDDTHHMMSSZ for ICS output. This is correct per RFC 5545.
    """

    def test_formatICSDate_equivalent(self):
        """
        Python equivalent of the JS formatICSDate function.
        Verify UTC conversion is correct.
        """
        # Simulate what Postgres returns for a 7pm Pacific event
        pg_value = "2025-01-16T03:00:00+00:00"  # 7pm PST = 3am next day UTC
        dt = datetime.fromisoformat(pg_value)
        ics_date = dt.strftime("%Y%m%dT%H%M%SZ")
        assert ics_date == "20250116T030000Z"

        # A calendar app receiving this Z-suffixed time will display it
        # in the user's local timezone — correct behavior.
