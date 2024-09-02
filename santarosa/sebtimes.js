const puppeteer = require('puppeteer');
const fs = require('fs');

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length !== 2) {
    console.error('Usage: node sebastopol_calendar_scraper.js <year> <month>');
    process.exit(1);
}

const targetYear = parseInt(args[0], 10);
const targetMonth = parseInt(args[1], 10);

if (isNaN(targetYear) || isNaN(targetMonth) || targetMonth < 1 || targetMonth > 12) {
    console.error('Invalid year or month. Please provide a valid year and month (1-12).');
    process.exit(1);
}

(async () => {
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(60000);

    const baseUrl = 'https://sebastopolcalendar.com/events/list/page/';
    let currentPage = 1;

    let eventsInMonth = [];
    const maxPages = 40; // Maximum number of pages to process

    async function extractEventsOnPage() {
        console.log("Extracting events data...");
        const events = await page.evaluate((targetYear, targetMonth) => {
            const eventElements = document.querySelectorAll('.tribe-events-calendar-list__event-details');
            const eventList = [];

            eventElements.forEach(event => {
                const name = event.querySelector('.tribe-events-calendar-list__event-title')?.innerText.trim() || 'No title provided';
                const dateElement = event.querySelector('.tribe-events-calendar-list__event-datetime');
                let formattedDateTime = 'Invalid date';

                if (dateElement) {
                    const dateTimeText = dateElement.innerText.trim();
                    const match = dateTimeText.match(/(\w+ \d{1,2}) @ (\d{1,2}:\d{2} [ap]m) - /i);
                    if (match) {
                        const [_, date, time] = match;
                        const fullDate = `${date}, ${targetYear} ${time}`;
                        const dateTime = new Date(fullDate);
                        formattedDateTime = dateTime.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
                    }
                }

                const location = event.querySelector('.tribe-events-calendar-list__event-venue')?.innerText.trim() || 'No location provided';
                const link = event.querySelector('.tribe-events-calendar-list__event-title-link')?.href || 'No link provided';

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
        while (currentPage <= maxPages) {
            const url = baseUrl + currentPage;
            console.log(`Navigating to ${url}`);
            await page.goto(url, { waitUntil: 'networkidle2' });

            await extractEventsOnPage();

            console.log(`\nAccumulated events after page ${currentPage}:`);
            eventsInMonth.forEach((pageEvents, index) => {
                console.log(`Page ${index + 1}`);
                pageEvents.forEach(event => {
                    console.log(`  ${event.date} - ${event.name}`);
                });
            });

            const lastPageEvents = eventsInMonth[eventsInMonth.length - 1];
            let allPastTargetDate = true;

            for (let event of lastPageEvents) {
                const lastEventDateStr = event.date;
                if (lastEventDateStr !== 'Invalid date') {
                    const year = parseInt(lastEventDateStr.slice(0, 4), 10);
                    const month = parseInt(lastEventDateStr.slice(4, 6), 10);

                    if (year === targetYear && month === targetMonth) {
                        allPastTargetDate = false;
                        break;
                    }
                }
            }

            if (allPastTargetDate) {
                console.log("\nExit condition met. All events on this page are past the target month. Stopping pagination.");
                break;
            }

            if (currentPage >= maxPages) {
                console.log("\nMaximum page limit reached. Stopping pagination.");
                break;
            }

            currentPage++;
        }
    }

    await handlePagination();

    let icsContent = `BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Sebastopol Calendar Events
X-WR-TIMEZONE:US/Pacific
BEGIN:VTIMEZONE
TZID:US/Pacific
X-LIC-LOCATION:US/Pacific
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

    eventsInMonth.flat().forEach(event => {
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

  const paddedTargetMonth = targetMonth.toString().padStart(2, '0');    
  const fileName = `sebtimes_${targetYear}_${paddedTargetMonth}.ics`;
    fs.writeFileSync(fileName, icsContent);
    console.log(`${fileName} file generated successfully!`);

    await browser.close();
})();