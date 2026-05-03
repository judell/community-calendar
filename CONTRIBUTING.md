# Contributing to Community Calendar

## How to Add Calendar Sources

The Supabase `feeds` table is the source of truth for all ICS feed sources. The file `cities/<city>/feeds.txt` is auto-generated from the database during each build — do not edit it by hand.

### Adding ICS feeds

Add entries to `cities/<city>/pending_feeds.txt`:

```
# Display Name
https://example.com/events/?ical=1

# Another Source
https://www.meetup.com/some-group/events/ical/
```

Each feed is a comment line with the display name, followed by the URL.

**Naming rule:** the `# Display Name` comment is the user-visible source attribution under each event card in the calendar UI. Use the bare canonical venue/source name only — no parenthetical context, no event counts, no strategy notes. Verification details, run-time counts, and discovery notes belong in `cities/<city>/SOURCES_CHECKLIST.md` (or a city-local `STRATEGIES_REVIEW.md`), not here.

You can test a URL before adding it:

```bash
python scripts/add_feed.py URL city "Source Name" --test
```

After your PR is merged, the next build automatically processes `pending_feeds.txt` — inserting the feeds into the database and resetting the file to its template.

### Adding scrapers

Scrapers require two things that ICS feeds don't:

1. **A workflow entry** in `.github/workflows/generate-calendar.yml` to actually run the scraper
2. **A pending_feeds.txt entry** so the build inserts the scraper's metadata (display name, command) into the `feeds` table

`add_scraper.py` handles both in one step:

```bash
python scripts/add_scraper.py <scraper_name> <city> "<Display Name>"
```

If you add a scraper manually without using this script, you'll likely miss one of the two pieces — the scraper will either run but have no display name, or be in the database but never execute.

See `scrapers/README.md` for available base scrapers and their options.

### What NOT to edit

- **`cities/<city>/feeds.txt`** — auto-generated from the database each build. Your changes will be overwritten.
- **`.github/workflows/generate-calendar.yml`** for ICS feed downloads — ICS feeds are downloaded automatically from the `feeds` table. Only scraper invocations belong in the workflow.

### Documenting your research

Update `cities/<city>/SOURCES_CHECKLIST.md` with what you found — working feeds, sources that need scrapers, and non-starters. See `docs/procedures.md` for the template and discovery techniques.

### PR checklist

- [ ] Added ICS feeds to `pending_feeds.txt` (not `feeds.txt`)
- [ ] For scrapers: used `add_scraper.py`
- [ ] Updated `SOURCES_CHECKLIST.md` with findings
- [ ] Tested feed URLs with `add_feed.py --test`

## Other Guidelines

- **Testing**: Tests are browser-based (`test.html`), not Node. Open `test.html` in a browser to run.
- **Git push**: CI may push between your commits. If `git push` fails, use `git pull --rebase && git push`.
- **Forks**: If you're running your own fork, see `docs/syncing-your-fork.md` for how to set up the feeds table. Forks without a `feeds` table can still use `feeds.txt` directly — `download_feeds.py` falls back to reading it when `SUPABASE_URL` isn't set.
