# Report Format

Use a single Markdown file with YAML front matter. The Markdown body is
for humans; the front matter is the machine-readable record.

This keeps reports:

- easy to diff and review in git
- editable without a custom tool
- strict enough for validation and summary scripts

## Goals

- one file per report
- stable IDs for findings and actions
- fixed status vocabulary
- explicit links to evidence
- concise enough to scan quickly

## Canonical Shape

The report file is:

1. YAML front matter
2. Markdown body with a small set of fixed sections

The front matter is the structured source of truth. The body may
summarize or elaborate, but it should not contradict the front matter.

## Required Front Matter

```yaml
report_id: davis-2026-08-06-31122804137
title: Davis build audit
city: davis
date: 2026-08-06
commit: 06d923e87a481d84c4976857d920670dec108ece
overall_status: partial
summary:
  total_checks: 12
  passed: 8
  failed: 3
  warning: 1
findings:
  - id: F001
    status: pass
    title: Mondavi scraper removed from Davis workflow
    scope: davis
    evidence:
      - type: workflow
        ref: .github/workflows/generate-calendar.yml
    action_ids: []
actions:
  - id: A001
    status: open
    title: Compare local and upstream Davis error sets
    owner: agent
artifacts:
  - label: Upstream run
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31122804137
```

## Required Markdown Sections

Use exactly these top-level headings:

```md
# Outcome
# Findings
# Actions
# Artifacts
```

The body should stay brief:

- `Outcome`: one table or short paragraph
- `Findings`: one subsection per finding ID
- `Actions`: one checkbox list item or paragraph per action ID
- `Artifacts`: exact file paths, run URLs, or log names

## Status Vocabularies

Use these fixed values.

Report `overall_status`:

- `pass`
- `partial`
- `fail`
- `warning`
- `pending`

Finding `status`:

- `pass`
- `fail`
- `warning`
- `pending`
- `info`

Action `status`:

- `open`
- `blocked`
- `done`
- `deferred`

## ID Rules

- Findings use `F###`, for example `F001`
- Actions use `A###`, for example `A001`
- IDs are stable within the life of a report
- Findings may reference related actions with `action_ids`

## Evidence Rules

Every finding should point to evidence:

- workflow run URL
- local log file
- JSON report file
- repo file path
- issue URL

Use exact references, not vague descriptions.

## Example

```md
---
report_id: davis-2026-08-06-31122804137
title: Davis build audit
city: davis
date: 2026-08-06
commit: 06d923e87a481d84c4976857d920670dec108ece
overall_status: partial
summary:
  total_checks: 6
  passed: 3
  failed: 2
  warning: 1
findings:
  - id: F001
    status: pass
    title: Mondavi scraper removed from Davis workflow
    scope: davis
    evidence:
      - type: workflow
        ref: .github/workflows/generate-calendar.yml
    action_ids: []
  - id: F002
    status: fail
    title: UC Davis Library feed returned 429 locally
    scope: davis
    evidence:
      - type: log
        ref: local-build.log
      - type: report
        ref: local-build-report.json
    action_ids: [A001]
actions:
  - id: A001
    status: open
    title: Compare local and upstream behavior for the UC Davis Library feed
    owner: agent
artifacts:
  - label: Upstream run
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31122804137
  - label: Local build log
    type: log
    ref: local-build.log
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Upstream run | pending | Waiting for runner allocation |
| Local build | partial | Completed with feed-level errors |

# Findings

## F001 Mondavi scraper removed from Davis workflow

No Mondavi execution remains in the Davis workflow.

## F002 UC Davis Library feed returned 429 locally

The local build reported rate limiting for the library ICS feed.

# Actions

- [ ] A001 Compare local and upstream behavior for the UC Davis Library feed

# Artifacts

- Upstream run: `https://github.com/judell/community-calendar/actions/runs/31122804137`
- Local build log: `local-build.log`
```

## Parsing Guidance

Tooling should:

1. parse the YAML front matter
2. validate it against [docs/report-schema.json](docs/report-schema.json)
3. treat the Markdown body as narrative support

If the body and front matter disagree, front matter wins.
