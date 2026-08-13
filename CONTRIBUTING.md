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

The CLI alternative validates the feed and registers it (`--test`
validates only — nothing written):

```bash
python scripts/add_feed.py URL city "Source Name"          # validate + register
python scripts/add_feed.py URL city "Source Name" --test   # validate only
```

After your PR is merged, the next build automatically processes `pending_feeds.txt` — inserting the feeds into the database and resetting the file to its template.

### Adding scrapers

Scraper execution is DB-first: the build runs whatever active scraper
rows exist in the `feeds` table. There is nothing to add to the
workflow — one command registers everything:

```bash
python scripts/add_scraper.py <scraper_name> <city> "<Display Name>"
```

For parameterized base scrapers, pass the scraper's site-specific
arguments and an output filename:

```bash
python scripts/add_scraper.py tribe_rest davis "My Venue" \
  --extra-args '--api-base "https://myvenue.org" --name "My Venue" --timezone America/Los_Angeles' \
  --output-name myvenue
```

The scraper is always tested first — the exact command being
registered, including `--extra-args` — and registration aborts if the
test fails. Add `--test` to validate only, writing nothing. On
success the script appends a scraper entry to
`cities/<city>/pending_feeds.txt`; the next build inserts it into the
`feeds` table (validated at insert time) and the DB-first runner
executes it in that same build.

See `scrapers/README.md` for the available base scrapers and how to
form each one's arguments (widget IDs, venue IDs, API bases, etc.).

### Removing sources

Use the Manage Feeds dialog (admin icon) — its Delete button removes
the source's row and all its events in one atomic server operation, for
scrapers and ICS feeds alike.

### What NOT to edit

- **`cities/<city>/feeds.txt`** — auto-generated from the database each
  build; a read-only, human-readable reference for what the database
  drives. Your changes will be overwritten.
- **`.github/workflows/generate-calendar.yml`** — carries no per-source
  lines at all: ICS feeds download from the `feeds` table and scrapers
  execute from it too.

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
