# Test Fixtures

This directory contains minimal ICS test fixtures for timezone pipeline tests.

## Purpose

These fixtures test the timezone handling pipeline (`ics_to_json.py`, `combine_ics.py`) across different scenarios:
- Bare datetimes (no TZID)
- TZID matching city timezone
- Cross-timezone events (TZID differs from city)
- UTC events
- Recurring events (RRULE)

## Structure

```
fixtures/
├── santarosa/          # America/Los_Angeles
├── bloomington/        # America/Indiana/Indianapolis  
├── montclair/          # America/New_York
└── toronto/            # America/Toronto
```

## Fixtures by Scenario

### Bare Datetimes (No TZID)
- `santarosa/sonoma_parks.ics` - Events without TZID parameter

### Matching Timezone
- `santarosa/uptowntheatrenapa.ics` - TZID=America/Los_Angeles (matches city)

### Cross-Timezone Events
- `santarosa/eventbrite_phoenix.ics` - TZID=US/Eastern (in Pacific city)
- `bloomington/mobilize_indivisible_central_indiana.ics` - TZID=America/Los_Angeles (in Indiana)
- `bloomington/gcal_bloomington_in_gov_c657mi332p5sjpq2lcht9imu60.ics` - TZID=America/New_York
- `montclair/eventbrite_montclair_book_center.ics` - TZID=America/Los_Angeles (in Eastern city)
- `toronto/indigenous.ics` - TZID=America/Halifax (in Toronto)

### UTC Events
- `toronto/uoft_engineering.ics` - Events in UTC (Z suffix)

### Recurring Events (RRULE)
- `santarosa/new_world_ballet.ics` - RRULE with TZID preservation

## Maintenance

### Adding New Fixtures

1. Create minimal ICS file with 2-3 events
2. Include VTIMEZONE block if using TZID
3. Use future dates (2026+) to avoid expiration
4. Add test in `tests/test_timezone_pipeline.py`

### Minimal ICS Template

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Fixture//Test//EN
BEGIN:VEVENT
UID:test-unique-id
DTSTART:20260615T100000
DTEND:20260615T110000
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR
```

### With TZID

Include VTIMEZONE block before VEVENT and use TZID parameter:

```ics
DTSTART;TZID=America/Los_Angeles:20260615T100000
```

## Testing

```bash
# Run all timezone tests
python -m pytest tests/test_timezone_pipeline.py -v

# Run only fixture tests
python -m pytest tests/test_timezone_pipeline.py::TestRealIcsFiles -v
```

## Related

- Tests: `tests/test_timezone_pipeline.py`
- Pipeline: `scripts/ics_to_json.py`, `scripts/combine_ics.py`
- Issue #14: Missing test fixtures
