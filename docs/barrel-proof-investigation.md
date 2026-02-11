# Barrel Proof Lounge Data Quality Investigation

**Date:** February 2026  
**Investigator:** Shelley (AI coding assistant)  
**Status:** Fix deployed, awaiting build results

## Overview

This document details an investigation into data quality issues with Barrel Proof Lounge events in the Santa Rosa community calendar. A user browsing the calendar clicked through to the venue's website and noticed the information didn't match—kicking off this investigation.

## Who I Am

I'm Shelley, an AI coding assistant with experience in software engineering and architecture. I help investigate issues, write code, and maintain systems. I work in a terminal environment but have access to both scripting tools and a web browser, allowing me to analyze problems from multiple angles.

## How This Investigation Was Conducted

This investigation combined two approaches:

1. **Scripting and data analysis** — Querying our event database, examining JSON feeds, testing API endpoints, and writing code to parse HTML

2. **Live website navigation** — Using a browser to visit barrelprooflounge.com, their Eventbrite page, and our calendar, taking screenshots at each step

Throughout the session, I shared screenshots of what I was seeing in the browser. The user was able to replicate the same navigation and confirmed the screenshots matched exactly what they saw on their end. This visual back-and-forth was critical for establishing shared understanding of the problem—we were literally looking at the same screens showing the same discrepancies.

## The Problem

A user was browsing the Santa Rosa community calendar as a normal user would. They saw a Barrel Proof Lounge event, clicked the link to get more details, and landed on barrelprooflounge.com. What they saw on the venue's website didn't match what our calendar had shown them:

- Events were listed on the venue site that weren't in our calendar
- Times shown on the venue site differed from what we had

This is exactly the kind of data quality issue that erodes user trust—when clicking through reveals "the real info is different."

## Investigation Process

### Step 1: Website Analysis

I examined barrelprooflounge.com and found:
- WordPress site using Elementor
- Events displayed via "Widget for Eventbrite API" plugin
- Homepage shows upcoming events with dates, times, descriptions, and RSVP links
- Event Calendar page returned 500 error (broken)

Key events visible on their homepage (Feb 10-11, 2026):
- Poetry Salon Happy Hour: 5:00 pm – 7:00 pm
- Tuesday Night Comedy Showcase with Tony Sparks: 8:00 pm – 10:00 pm
- Live Music Happy Hour – Pickin' Peaches: 5:00 pm – 7:00 pm
- Wednesday Night Comedy Open Mic: **6:00 pm – 9:00 pm**
- Big Stage Karaoke: 9:00 pm – 1:30 am

### Step 2: Our Feed Analysis

I examined `cities/santarosa/events.json` and found Barrel Proof events sourced from:
- North Bay Bohemian
- Press Democrat  
- GoLocal Cooperative

### Step 3: Discrepancies Found

#### Issue 1: Missing Event
**"Tuesday Night Comedy Showcase with Tony Sparks"** - A recurring Tuesday event at 8pm was completely absent from our feeds. None of the three aggregator sources had captured it.

#### Issue 2: Wrong Time
**"Wednesday Night Comedy Open Mic"** showed **7:00 pm (19:00)** in our feeds, but the venue's website clearly displays **6:00 pm – 9:00 pm**. The promotional image on their site even shows "SHOW 6PM-9PM".

### Step 4: Root Cause Analysis

I traced the data upstream:

1. **Eventbrite Organizer Page** (eventbrite.com/o/barrel-proof-lounge-52973374973)
   - Has 31 upcoming events
   - Tony Sparks show IS listed here
   - Wednesday Comedy Open Mic JSON-LD shows `startDate: "2026-01-07T19:00:00-08:00"` (7pm)

2. **Eventbrite JSON-LD vs Website Display**
   - Eventbrite's structured data says 7pm
   - Venue's website displays 6pm
   - The venue likely made a data entry error on Eventbrite when creating the recurring event
   - Their website pulls display times from their internal CMS (correct) while Eventbrite API returns the wrong metadata

3. **Aggregator Coverage**
   - Bohemian, Press Democrat, and GoLocal all appear to source from Eventbrite or each other
   - None had the Tony Sparks show
   - All had the wrong 7pm time for Comedy Open Mic

### Step 5: Our Eventbrite Scraper

I tested our existing `eventbrite_scraper.py`:
- Scrapes generic location search: `eventbrite.com/d/ca--santa-rosa/all-events/`
- Only found 20 events (Eventbrite's search result limit)
- Did not include Barrel Proof events because they weren't in the top search results

## Solution Implemented

Created a dedicated scraper (`scrapers/barrel_proof.py`) that:

1. **Scrapes directly from barrelprooflounge.com** rather than Eventbrite or aggregators
2. **Extracts accurate times** from the HTML which displays correct data from their internal system
3. **Captures event titles, times, descriptions, and Eventbrite links**
4. **Outputs standard ICS format** for integration with our pipeline

### Technical Details

The venue's homepage HTML contains event data in this structure:
```html
<a title="Eventbrite link to EVENT TITLE">EVENT TITLE</a>
<time>February 11, 2026, 6:00 pm – 9:00 pm</time>
```

The scraper parses these elements and generates ICS events with:
- Correct start/end times from the displayed text
- Eventbrite URLs from `data-eb-id` attributes
- Venue location hardcoded (501 Mendocino Ave, Santa Rosa)

### Files Changed

| File | Change |
|------|--------|
| `scrapers/barrel_proof.py` | New scraper (created) |
| `.github/workflows/generate-calendar.yml` | Added scraper to Santa Rosa workflow |
| `scripts/combine_ics.py` | Added "Barrel Proof Lounge" source name mapping |

## Verification

Local test of the new scraper:

```
$ python scrapers/barrel_proof.py
Fetching: https://barrelprooflounge.com/
Found 5 events
  02/10 05:00PM - Poetry Salon Happy Hour Presented by Timothy Williams
  02/10 08:00PM - Tuesday Night Comedy Showcase with Tony Sparks  ← WAS MISSING
  02/11 05:00PM - Live Music Happy Hour – Pickin' Peaches!
  02/11 06:00PM - Wednesday Night Comedy Open Mic                 ← NOW CORRECT (was 7pm)
  02/11 09:00PM - Big Stage Karaoke Wednesdays with KJ Danny D
```

## Build Results

**Status:** Awaiting workflow completion

*Results will be added here once the GitHub Actions build completes.*

---

## Lessons Learned

1. **Third-party aggregators can have incomplete data** - The Bohemian, Press Democrat, and GoLocal all missed the Tony Sparks show

2. **Eventbrite metadata can be wrong** - The venue entered 7pm instead of 6pm; their website shows the correct time but the API returns incorrect data

3. **Venue websites are authoritative** - When in doubt, scrape directly from the source rather than relying on intermediaries

4. **Multiple data sources help identify issues** - Having the venue's website to compare against revealed problems that wouldn't be obvious from aggregator data alone

## Recommendations

1. **Consider adding more direct venue scrapers** for high-value venues with active event calendars

2. **Periodic audits** - Spot-check popular venues against their websites to catch data drift

3. **User feedback mechanism** - Make it easy for users to report "this event info seems wrong" with a link to the source
