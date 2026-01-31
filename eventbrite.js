const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

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
    console.error('Usage: node eventbrite.js <location> <year> <month>');
    process.exit(1);
}

const location = args[0].toLowerCase();
const targetYear = parseInt(args[1], 10);
const targetMonth = parseInt(args[2], 10);

if (!LOCATION_CONFIGS[location] || isNaN(targetYear) || isNaN(targetMonth) || targetMonth < 1 || targetMonth > 12) {
    console.error('Invalid location, year, or month.');
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
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    });

    const page = await browser.newPage();
    
    // Set viewport and user agent
    await page.setViewport({ width: 1920, height: 1080 });
    
    console.log(`Navigating to ${url}...`);
    
    try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
    } catch (e) {
        console.error(`Failed to load page: ${e.message}`);
        await browser.close();
        return [];
    }

    // Check if we hit a block page
    const pageContent = await page.content();
    if (pageContent.includes('Human Verification') || pageContent.includes('Access Denied')) {
        console.error('Blocked by bot detection');
        await browser.close();
        return [];
    }

    // Extract JSON-LD data from the page
    const events = await page.evaluate(() => {
        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
        const allEvents = [];
        
        scripts.forEach(script => {
            try {
                const data = JSON.parse(script.textContent);
                if (data['@type'] === 'ItemList' && data.itemListElement) {
                    data.itemListElement.forEach(item => {
                        if (item.item && item.item['@type'] === 'Event') {
                            allEvents.push(item.item);
                        }
                    });
                }
            } catch (e) {}
        });
        
        return allEvents;
    });

    console.log(`Found ${events.length} events on first page`);

    // Paginate through results
    let allEvents = [...events];
    let pageNum = 1;
    const maxPages = 20;

    while (pageNum < maxPages) {
        pageNum++;
        const nextUrl = `${url}?page=${pageNum}`;
        
        console.log(`Fetching page ${pageNum}...`);
        
        try {
            await page.goto(nextUrl, { waitUntil: 'networkidle2', timeout: 30000 });
        } catch (e) {
            console.log(`Failed to load page ${pageNum}, stopping`);
            break;
        }

        const pageEvents = await page.evaluate(() => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            const events = [];
            
            scripts.forEach(script => {
                try {
                    const data = JSON.parse(script.textContent);
                    if (data['@type'] === 'ItemList' && data.itemListElement) {
                        data.itemListElement.forEach(item => {
                            if (item.item && item.item['@type'] === 'Event') {
                                events.push(item.item);
                            }
                        });
                    }
                } catch (e) {}
            });
            
            return events;
        });

        if (pageEvents.length === 0) {
            console.log('No more events found, stopping');
            break;
        }

        console.log(`  Found ${pageEvents.length} events`);
        allEvents = allEvents.concat(pageEvents);

        // Check if we've gone past target month
        let pastTargetCount = 0;
        for (const event of pageEvents) {
            if (event.startDate) {
                const date = new Date(event.startDate);
                if (date.getFullYear() > targetYear || 
                    (date.getFullYear() === targetYear && date.getMonth() + 1 > targetMonth)) {
                    pastTargetCount++;
                }
            }
        }
        
        if (pastTargetCount === pageEvents.length) {
            console.log('All events past target month, stopping');
            break;
        }
    }

    await browser.close();
    
    // Filter to target month and deduplicate
    const seen = new Set();
    const filtered = allEvents.filter(event => {
        if (!event.startDate || !event.url) return false;
        if (seen.has(event.url)) return false;
        seen.add(event.url);
        
        const date = new Date(event.startDate);
        return date.getFullYear() === targetYear && date.getMonth() + 1 === targetMonth;
    });

    console.log(`Total events in ${targetYear}-${targetMonth}: ${filtered.length}`);
    return filtered;
}

function createICSContent(events, locationConfig, targetYear, targetMonth) {
    let ics = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:${locationConfig.prodid}
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:${locationConfig.calname}
X-WR-TIMEZONE:${locationConfig.timezone}
`;

    for (const event of events) {
        const startDate = new Date(event.startDate);
        const endDate = event.endDate ? new Date(event.endDate) : startDate;
        
        const formatDate = (d) => d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
        
        let location = '';
        if (event.location && event.location.name) {
            location = event.location.name;
            if (event.location.address) {
                const addr = event.location.address;
                const parts = [addr.streetAddress, addr.addressLocality, addr.addressRegion].filter(Boolean);
                if (parts.length) location += ', ' + parts.join(', ');
            }
        }

        ics += `BEGIN:VEVENT
SUMMARY:${(event.name || 'Untitled').replace(/\n/g, ' ')}
DTSTART:${formatDate(startDate)}
DTEND:${formatDate(endDate)}
URL:${event.url || ''}
LOCATION:${location.replace(/\n/g, ' ')}
DESCRIPTION:${(event.description || '').replace(/\n/g, '\\n').substring(0, 500)}
UID:${event.url}-${event.startDate}
END:VEVENT
`;
    }

    ics += 'END:VCALENDAR';
    return ics;
}

async function main() {
    console.log(`Scraping Eventbrite for ${location}, ${targetYear}-${targetMonth}`);
    
    const events = await scrapeEvents(locationConfig.url, targetYear, targetMonth);
    const ics = createICSContent(events, locationConfig, targetYear, targetMonth);
    
    const paddedMonth = targetMonth.toString().padStart(2, '0');
    const filename = `./${location}/eventbrite_${targetYear}_${paddedMonth}.ics`;
    
    fs.writeFileSync(filename, ics);
    console.log(`Wrote ${filename}`);
}

main().catch(console.error);
