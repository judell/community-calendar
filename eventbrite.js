const puppeteer = require('puppeteer');
const fs = require('fs');

// Location-specific configurations
const LOCATION_CONFIGS = {
    'santarosa': {
        'url': 'https://www.eventbrite.com/d/ca--santa-rosa/all-events/',
        'timezone': 'US/Pacific',
        'prodid': '-//Eventbrite Santa Rosa Events//',
        'calname': 'Eventbrite Santa Rosa Events'
    },
    'bloomington': {
        'url': 'https://www.eventbrite.com/d/in--bloomington/all-events/',
        'timezone': 'America/Indiana/Indianapolis',
        'prodid': '-//Eventbrite Bloomington Events//',
        'calname': 'Eventbrite Bloomington Events'
    }
};

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length !== 3) {
    console.error('Usage: node common_eventbrite.js <location> <year> <month>');
    process.exit(1);
}

const location = args[0].toLowerCase();
const targetYear = parseInt(args[1], 10);
const targetMonth = parseInt(args[2], 10);

if (!LOCATION_CONFIGS[location] || isNaN(targetYear) || isNaN(targetMonth) || targetMonth < 1 || targetMonth > 12) {
    console.error('Invalid location, year, or month. Please provide a valid location, year, and month (1-12).');
    process.exit(1);
}

const locationConfig = LOCATION_CONFIGS[location];

async function scrapeEvents(url, targetYear, targetMonth) {
    const browser = await puppeteer.launch({ 
        headless: 'new',
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
    });
    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(60000);
    
    // Set a realistic user agent to avoid bot detection
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1920, height: 1080 });

    console.log(`Navigating to ${url}...`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
    
    // Wait for events to load
    try {
        await page.waitForSelector('[data-testid="search-event"]', { timeout: 30000 });
        console.log('Events loaded successfully');
    } catch (e) {
        console.error('Failed to find events on page. Page might be blocked or have different structure.');
        const html = await page.content();
        console.log('Page content preview:', html.substring(0, 500));
        await browser.close();
        return [];
    }

    let eventsInMonth = [];
    const maxPages = 40; // Maximum number of pages to process

    async function extractEventsOnPage() {
        console.log("Extracting events data...");
        const events = await page.evaluate((targetYear, targetMonth) => {
            const eventElements = document.querySelectorAll('[data-testid="search-event"]');
            const eventList = [];
            
            // Helper to get today/tomorrow dates
            const now = new Date();
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);

            eventElements.forEach(event => {
                const name = event.querySelector('h3')?.innerText || 'No title provided';

                const dateTimeElement = Array.from(event.querySelectorAll('p')).find(p => /\b(?:AM|PM)\b/.test(p.innerText));

                let formattedDateTime = 'Invalid date';
                if (dateTimeElement) {
                    const dateTimeText = dateTimeElement.innerText.trim();
                    try {
                        // Handle "Today • 8:00 PM" or "Tomorrow • 7:00 PM"
                        const todayMatch = dateTimeText.match(/Today\s*•\s*(\d{1,2}:\d{2}\s*[APM]+)/i);
                        const tomorrowMatch = dateTimeText.match(/Tomorrow\s*•\s*(\d{1,2}:\d{2}\s*[APM]+)/i);
                        
                        // Handle "Sat, Mar 7 • 1:30 PM"
                        const dateMatch = dateTimeText.match(/(\w+),?\s*(\w+\s+\d{1,2})\s*•?\s*(\d{1,2}:\d{2}\s*[APM]+)/);
                        
                        let dateTime = null;
                        
                        if (todayMatch) {
                            const time = todayMatch[1];
                            const [hours, minutes] = time.match(/(\d+):(\d+)/).slice(1);
                            const isPM = /PM/i.test(time);
                            let hour = parseInt(hours);
                            if (isPM && hour !== 12) hour += 12;
                            if (!isPM && hour === 12) hour = 0;
                            dateTime = new Date(today);
                            dateTime.setHours(hour, parseInt(minutes), 0, 0);
                        } else if (tomorrowMatch) {
                            const time = tomorrowMatch[1];
                            const [hours, minutes] = time.match(/(\d+):(\d+)/).slice(1);
                            const isPM = /PM/i.test(time);
                            let hour = parseInt(hours);
                            if (isPM && hour !== 12) hour += 12;
                            if (!isPM && hour === 12) hour = 0;
                            dateTime = new Date(tomorrow);
                            dateTime.setHours(hour, parseInt(minutes), 0, 0);
                        } else if (dateMatch) {
                            const [_, dayOfWeek, date, time] = dateMatch;
                            // Try current year first, then next year if date is in the past
                            let fullDate = `${date}, ${targetYear} ${time}`;
                            dateTime = new Date(fullDate);
                            // If the date is more than 2 months in the past, assume next year
                            if (dateTime < new Date(now.getTime() - 60*24*60*60*1000)) {
                                fullDate = `${date}, ${targetYear + 1} ${time}`;
                                dateTime = new Date(fullDate);
                            }
                        }
                        
                        if (dateTime && !isNaN(dateTime.getTime())) {
                            formattedDateTime = dateTime.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
                        }
                    } catch (error) {
                        // Silent fail, will be marked as Invalid date
                    }
                }

                const location = event.querySelector('[data-event-location]')?.getAttribute('data-event-location') || 'No location provided';
                const link = event.querySelector('a.event-card-link')?.href || 'No link provided';

                eventList.push({
                    name,
                    date: formattedDateTime,
                    location,
                    link
                });
            });

            return eventList;
        }, targetYear, targetMonth);

        eventsInMonth.push(events);
    }

    async function handlePagination() {
        let pageNumber = 1;

        while (pageNumber <= maxPages) {
            await extractEventsOnPage();

            console.log(`\nAccumulated events after page ${pageNumber}:`);
            eventsInMonth.forEach((pageEvents, index) => {
                console.log(`${index + 1}`);
                pageEvents.forEach(event => {
                    console.log(`  ${event.date}`);
                });
            });

            const lastPageEvents = eventsInMonth[eventsInMonth.length - 1];
            
            // Count valid events and check if any are in target month
            let validEventCount = 0;
            let eventsInTargetMonth = 0;
            let eventsPastTargetMonth = 0;
            
            for (let event of lastPageEvents) {
                if (event.date === 'Invalid date') continue;
                validEventCount++;
                
                const year = parseInt(event.date.slice(0, 4), 10);
                const month = parseInt(event.date.slice(4, 6), 10);

                if (year === targetYear && month === targetMonth) {
                    eventsInTargetMonth++;
                } else if (year > targetYear || (year === targetYear && month > targetMonth)) {
                    eventsPastTargetMonth++;
                }
            }
            
            console.log(`Page ${pageNumber}: ${lastPageEvents.length} events, ${validEventCount} valid dates, ${eventsInTargetMonth} in target month, ${eventsPastTargetMonth} past target`);

            // Only stop if we have valid events and ALL of them are past the target month
            if (validEventCount > 0 && eventsInTargetMonth === 0 && eventsPastTargetMonth === validEventCount) {
                console.log("\nExit condition met. All valid events on this page are past the target month. Stopping pagination.");
                break;
            }
            
            // Also stop if we got no events at all (empty page)
            if (lastPageEvents.length === 0) {
                console.log("\nNo events found on page. Stopping pagination.");
                break;
            }

            if (pageNumber >= maxPages) {
                console.log("\nMaximum page limit reached. Stopping pagination.");
                break;
            }

            console.log("Checking for 'Next Page' button...");
            const nextPageButton = await page.$('button[data-testid="page-next"]');
            if (!nextPageButton) {
                console.log("No 'Next Page' button found. Ending pagination.");
                break;
            }

            console.log("Clicking 'Next Page' button...");
            await nextPageButton.click();

            console.log("Waiting for the next page of events to load...");
            try {
                await page.waitForSelector('[data-testid="search-event"]', { visible: true, timeout: 60000 });
                console.log("Next page loaded, continuing to extract events.");
            } catch (error) {
                console.error("Error waiting for the next page to load:", error);
                break;
            }

            pageNumber++;
        }
    }

    await handlePagination();
    await browser.close();

    return eventsInMonth.flat();
}

function createICSContent(events, locationConfig, targetYear, targetMonth) {
    let icsContent = `BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
PRODID:${locationConfig.prodid}
X-WR-CALNAME:${locationConfig.calname}
X-WR-TIMEZONE:${locationConfig.timezone}
BEGIN:VTIMEZONE
TZID:${locationConfig.timezone}
X-LIC-LOCATION:${locationConfig.timezone}
BEGIN:STANDARD
TZOFFSETFROM:-0700
TZOFFSETTO:-0800
TZNAME:PST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
TZOFFSETFROM:-0800
TZOFFSETTO:-0700
TZNAME:PDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
`;

    events.forEach(event => {
        if (event.date !== 'Invalid date') {
            const year = parseInt(event.date.slice(0, 4), 10);
            const month = parseInt(event.date.slice(4, 6), 10);

            if (year === targetYear && month === targetMonth) {
                icsContent += `BEGIN:VEVENT
SUMMARY:${event.name}
DTSTART:${event.date}
LOCATION:${event.location}
URL:${event.link}
DESCRIPTION:${event.name}
END:VEVENT
`;
            } else if (year > targetYear || (year === targetYear && month > targetMonth)) {
                console.log(`Excluding event "${event.name}" as it occurs after the target month.`);
            }
        } else {
            console.warn(`Skipping event "${event.name}" due to invalid date format.`);
        }
    });

    icsContent += "END:VCALENDAR";
    return icsContent;
}

async function main() {
    console.log(`Scraping Eventbrite events for ${location} in ${targetYear}-${targetMonth}`);
    const events = await scrapeEvents(locationConfig.url, targetYear, targetMonth);
    const icsContent = createICSContent(events, locationConfig, targetYear, targetMonth);

    const paddedTargetMonth = targetMonth.toString().padStart(2, '0');       
    const fileName = `./${location}/eventbrite_${targetYear}_${paddedTargetMonth}.ics`;
    fs.writeFileSync(fileName, icsContent);
    console.log(`${fileName} file generated successfully!`);
}

main().catch(console.error);