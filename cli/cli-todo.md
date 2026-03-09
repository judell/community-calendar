# cc-cli TODO

## Done (implemented)
- Resume support via .cc-cli-state.json
- Ticketmaster prompt: "Consumer Key" clarification
- GitHub OAuth: "leave Enable Device Flow unchecked"
- Google OAuth: detailed inline walkthrough
- City directory creation (ensures cities/<name>/feeds.txt exists with sample feeds)
- Optional city removal (defaults to keeping other cities for sample data)
- `-R repo` on all gh commands (secrets, variables, pages, workflow)
- Generic download_feeds.py replaces per-city curl blocks in workflow
- `cc-cli build` — triggers generate-calendar workflow
- `cc-cli status` — shows recent workflow runs
- CLI does git commit+push with suppressed output
- Enable workflows prompt in "Next steps"

## Next build
- Spinner/elapsed time during "Waiting for project to be ready" (currently silent, looks stuck)
- During init, remove upstream-only workflows (regression-tests.yml)
- During init, strip per-city scrape blocks from generate-calendar.yml
- During init, ensure download_feeds.py exists (fork may predate it)
- During init, add ics_categories column (missing from DDL, needed for upsert)
- Make XMLUI city picker dynamic (query distinct cities from Supabase)

## Future subcommands
- `cc-cli logs` — tail latest workflow run logs
- `cc-cli add-source <url> [city]` — wrapper around add_feed.py (test + add to feeds.txt)
- `cc-cli deploy` — redeploy edge functions, re-run DDL
- `cc-cli add-city <name>` — scaffold new city directory, optionally seed feeds.txt

## Architecture
- Separate generated files from source (gh-pages branch for build artifacts, clean main)
  - Solves merge conflicts for forks that both run nightly generation
  - Keeps main branch reviewable (no events.json churn)
