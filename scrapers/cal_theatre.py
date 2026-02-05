#!/usr/bin/env python3
"""
Scraper for California Theatre (Cal Theatre) Santa Rosa events
https://www.caltheatre.com/calendar

This is a Wix site with a calendar widget. We need to use browser automation
or parse the rendered HTML since data is loaded via JavaScript.
"""

import sys
sys.path.insert(0, str(__file__).rsplit('/', 1)[0])  # Add scrapers/ to path

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import re
import argparse
import logging
import time

from lib.utils import generate_uid, append_source, DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://www.caltheatre.com'
CALENDAR_URL = f'{BASE_URL}/calendar'
VENUE_ADDRESS = "California Theatre, 528 7th St, Santa Rosa, CA 95401"

def fetch_with_selenium(year, month):
    """Fetch calendar page using Selenium for JavaScript rendering."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        logger.error("Selenium not installed. Install with: pip install selenium")
        raise
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(CALENDAR_URL)
        
        # Wait for calendar to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-hook*="calendar"]'))
        )
        
        # Navigate to target month if needed
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        months_diff = (year - current_year) * 12 + (month - current_month)
        
        if months_diff > 0:
            for _ in range(months_diff):
                next_btn = driver.find_element(By.CSS_SELECTOR, '[data-hook="calendar-next-month-button"]')
                next_btn.click()
                time.sleep(0.5)
        elif months_diff < 0:
            for _ in range(abs(months_diff)):
                prev_btn = driver.find_element(By.CSS_SELECTOR, '[data-hook="calendar-previous-month-button"]')
                prev_btn.click()
                time.sleep(0.5)
        
        time.sleep(1)  # Wait for calendar update
        
        return driver.page_source
        
    finally:
        driver.quit()

def fetch_calendar_static():
    """Attempt to fetch calendar with static request (may not work for JS sites)."""
    logger.info(f"Fetching {CALENDAR_URL}")
    response = requests.get(CALENDAR_URL, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()
    return response.text

def parse_wix_calendar_text(html_content, target_year, target_month):
    """Parse events from Wix calendar text content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Try to find calendar day cells with events
    # Wix uses data-hook attributes
    calendar_cells = soup.find_all(attrs={'data-hook': re.compile(r'calendar-day-\d+')})
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = month_names[target_month - 1]
    
    for cell in calendar_cells:
        try:
            cell_text = cell.get_text(' ', strip=True)
            
            # Extract day number from data-hook like "calendar-day-15"
            hook = cell.get('data-hook', '')
            day_match = re.search(r'calendar-day-(\d+)', hook)
            if not day_match:
                continue
            day = int(day_match.group(1))
            
            # Find events in this cell - look for time patterns
            # Format: "15 7:30 PM Event Title +1 more"
            event_patterns = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s+([^+]+?)(?:\s*\+|$)', cell_text, re.IGNORECASE)
            
            for time_str, title in event_patterns:
                title = title.strip()
                if not title or len(title) < 3:
                    continue
                
                try:
                    date_str = f"{month_name} {day}, {target_year}"
                    dt_start = datetime.strptime(f"{date_str} {time_str}", "%B %d, %Y %I:%M %p")
                except ValueError:
                    continue
                
                # Events typically 2-3 hours
                dt_end = dt_start + timedelta(hours=3)
                
                events.append({
                    'title': title,
                    'url': CALENDAR_URL,
                    'dtstart': dt_start,
                    'dtend': dt_end,
                    'location': VENUE_ADDRESS,
                    'description': f'Event at California Theatre. See {CALENDAR_URL} for details.'
                })
                
                logger.info(f"Found event: {title} on {dt_start}")
        
        except Exception as e:
            logger.warning(f"Error parsing cell: {e}")
            continue
    
    return events

def create_calendar(events, year, month):
    """Create an iCalendar from parsed events."""
    cal = Calendar()
    cal.add('prodid', '-//California Theatre Santa Rosa//caltheatre.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'Cal Theatre - {year}/{month:02d}')
    cal.add('x-wr-timezone', 'America/Los_Angeles')
    
    for event_data in events:
        event = Event()
        event.add('summary', event_data['title'])
        event.add('dtstart', event_data['dtstart'])
        event.add('dtend', event_data['dtend'])
        event.add('url', event_data['url'])
        event.add('location', event_data['location'])
        event.add('description', append_source(event_data.get('description', ''), 'Cal Theatre'))
        event.add('uid', generate_uid(event_data['title'], event_data['dtstart'], 'caltheatre.com'))
        event.add('x-source', 'Cal Theatre')
        
        cal.add_component(event)
    
    return cal

def main():
    parser = argparse.ArgumentParser(description='Scrape Cal Theatre events')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--month', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--output', type=str, help='Output filename')
    parser.add_argument('--use-selenium', action='store_true', help='Use Selenium for JS rendering')
    args = parser.parse_args()
    
    if args.use_selenium:
        html = fetch_with_selenium(args.year, args.month)
    else:
        html = fetch_calendar_static()
    
    events = parse_wix_calendar_text(html, args.year, args.month)
    
    logger.info(f"Found {len(events)} events for {args.year}-{args.month:02d}")
    
    cal = create_calendar(events, args.year, args.month)
    
    output_file = args.output or f'cal_theatre_{args.year}_{args.month:02d}.ics'
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    logger.info(f"Written to {output_file}")
    return output_file

if __name__ == '__main__':
    main()
