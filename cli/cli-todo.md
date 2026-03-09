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
- Strip per-city scrape blocks from workflow during init (forks use feeds.txt only)
- Warn if download_feeds.py missing (fork may predate it)
- ics_categories column covered by DDL (02_events.sql)
- Disable non-essential workflows during init (via GitHub API)

## Next build
- Move DisableNonEssentialWorkflows from init to `cc-cli build` (first run): init can't disable workflows because they aren't enabled yet on forks; `cc-cli build` should disable extras before triggering
- `cc-cli init` does fork+clone: user installs binary from release, runs `cc-cli init` which forks judell/community-calendar, clones it, then continues with setup
- Spinner/elapsed time during "Waiting for project to be ready" (currently silent, looks stuck)
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
