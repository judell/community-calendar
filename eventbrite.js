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
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(60000);

    await page.goto(url, { waitUntil: 'networkidle2' });

    let eventsInMonth = [];
    const maxPages = 40; // Maximum number of pages to process

    async function extractEventsOnPage() {
        console.log("Extracting events data...");
        const events = await page.evaluate((targetYear, targetMonth) => {
            const eventElements = document.querySelectorAll('[data-testid="search-event"]');
            const eventList = [];

            eventElements.forEach(event => {
                const name = event.querySelector('h3')?.innerText || 'No title provided';

                const dateTimeElement = Array.from(event.querySelectorAll('p')).find(p => /\b(?:AM|PM)\b/.test(p.innerText));

                let formattedDateTime = 'Invalid date';
                if (dateTimeElement) {
                    const dateTimeText = dateTimeElement.innerText.trim();
                    try {
                        const dateMatch = dateTimeText.match(/(\w+),?\s*(\w+ \d{1,2})\s*•?\s*(\d{1,2}:\d{2} [APM]+)/);
                        if (dateMatch) {
                            const [_, dayOfWeek, date, time] = dateMatch;
                            const fullDate = `${date}, ${targetYear} ${time}`;
                            const dateTime = new Date(fullDate);
                            formattedDateTime = dateTime.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
                        }
                    } catch (error) {
                        console.error(`Failed to parse date for event "${name}": ${dateTimeText}`);
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
            let allPastTargetDate = true;

            for (let event of lastPageEvents) {
                const lastEventDateStr = event.date;
                const year = parseInt(lastEventDateStr.slice(0, 4), 10);
                const month = parseInt(lastEventDateStr.slice(4, 6), 10);

                if (year === targetYear && month === targetMonth) {
                    allPastTargetDate = false;
                    break;
                }
            }

            if (allPastTargetDate) {
                console.log("\nExit condition met. All events on this page are past the target month. Stopping pagination.");
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