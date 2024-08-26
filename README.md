# Usage

```
cal.py [-h] [--dry-run DRY_RUN] [--generate] [--location] [--timezone TIMEZONE] [--year YEAR] [--month MONTH]

Generate an HTML calendar from iCalendar feeds or perform a dry run.

options:
  -h, --help           Show this help message and exit.
  --dry-run DRY_RUN    Perform a dry run on a single iCalendar URL.
  --generate           Generate an HTML calendar from {LOCATION_FOLDER}/feeds.txt, a list of iCalendar feeds.
  --location           Folder for feeds.txt and output (e.g. 2024-08.html).
  --timezone TIMEZONE  Default timezone (default: America/Indiana/Indianapolis).
  --year YEAR          Year for calendar generation.
  --month MONTH        Month for calendar generation.
```

# Bloomington example

Community calendar for [August 2024](https://jonudell.info/bloomington/2024-08.html)

## Rendered calendar

![image](https://github.com/user-attachments/assets/280beee9-d752-47c7-be70-d1b710f08bcc)

## Source feeds and stats

![image](https://github.com/user-attachments/assets/80dfb127-eae3-4a7c-af50-65bc576a6b15)

# Timezone Handling Strategy

## Overview

The calendar generation system deals with events from multiple sources, potentially in different timezones, and needs to display them correctly in a user-specified timezone. This document outlines the strategy used to handle these timezone conversions accurately.

## Key Challenges

1. Source calendars may specify events in different timezones.
2. Some events may be specified without explicit timezone information.
3. The system needs to display all events in a consistent, user-specified timezone.
4. All-day events need special handling to prevent date shifts during timezone conversions.

## Strategy

The system uses a three-step approach:

1. Determine the source timezone for each calendar.
2. Parse and localize each event to its source timezone, then convert to the target timezone.
3. Group events by their original date in the source timezone to ensure correct placement in the calendar.

## Key Functions and Their Roles

### `determine_timezone(vtimezone_info, x_wr_timezone, default_timezone)`

- **Role**: Determines the source timezone for a calendar.
- **Strategy**:
  1. Check for VTIMEZONE information in the calendar.
  2. If not found, use X-WR-TIMEZONE property.
  3. Fall back to the user-specified default timezone.
  4. Use UTC as a last resort.

### `parse_vtimezone(cal)`

- **Role**: Extracts detailed timezone information from the calendar's VTIMEZONE component.
- **Usage**: Provides input for `determine_timezone` function.

### `parse_and_localize_event(event, source_tz, target_tz)`

- **Role**: Converts individual events from their source timezone to the target timezone.
- **Strategy**:
  1. Handle naive datetime objects by assuming they're in the source timezone.
  2. Convert aware datetime objects to the target timezone.
  3. Preserve the original date in the source timezone for correct grouping.
  4. Special handling for all-day events to prevent date shifts.

### `group_events_by_date(events, year, month)`

- **Role**: Groups processed events by their original date in the source timezone.
- **Importance**: Ensures events appear on the correct date in the calendar, regardless of timezone conversions.

## Implementation Details

1. **Source Timezone Determination**:
   - The `fetch_and_process_calendar` function uses `determine_timezone` to set the `source_tz`.
   - This ensures all events from a single calendar are treated with the same source timezone.

2. **Event Localization and Conversion**:
   - Each event is processed by `parse_and_localize_event`.
   - This function handles the conversion from source to target timezone.
   - It also calculates a `grouping_date` based on the event's original date in the source timezone.

3. **Event Grouping**:
   - The `group_events_by_date` function uses the `grouping_date` to place events in the correct day.
   - This prevents issues where timezone conversions might shift an event to a different day.

4. **All-Day Event Handling**:
   - All-day events are detected in `parse_and_localize_event`.
   - These events are not converted to the target timezone to prevent date shifts.

## Considerations for Developers

- When modifying timezone-related code, always consider the impact on both timed and all-day events.
- Be cautious of naive datetime objects and always ensure proper timezone awareness.
- When adding new event sources, ensure they properly specify their timezone information.
- Consider edge cases like events spanning midnight or daylight saving time transitions.

By following this strategy, the system aims to accurately represent events from various sources in a unified, user-specified timezone while maintaining the correct date associations for all events.

