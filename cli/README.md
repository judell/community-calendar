# cc-cli

Command-line tool to set up a Community Calendar fork with its own Supabase backend.

## Prerequisites

- **Go** (1.22+) — only needed if building from source
- **GitHub CLI (`gh`)** — required for all operations
  - Install: https://cli.github.com/
  - Authenticate: `gh auth login`

## Install

Download the binary for your platform from the [Releases page](https://github.com/judell/community-calendar/releases).

```
chmod +x cc-cli-*
sudo mv cc-cli-* /usr/local/bin/cc-cli
```

**macOS users:** Gatekeeper will block the unsigned binary. After downloading, run:

```
xattr -d com.apple.quarantine cc-cli-*
```

Or build from source:

```
cd cli
go build -o cc-cli .
```

## Usage

### `cc-cli init`

Guided setup that:

1. Forks and clones the upstream repo (if not already in one)
2. Creates a Supabase project
3. Walks you through OAuth app creation (GitHub + Google)
4. Configures auth providers
5. Applies the database schema
6. Deploys edge functions
7. Sets GitHub Actions secrets and variables
8. Enables GitHub Pages
9. Removes upstream-only workflows and scraper steps
10. Commits and pushes

Progress is saved to `.cc-cli-state.json` so you can resume if interrupted.

After init completes, visit your fork's Actions tab and click "I understand my workflows, go ahead and enable them", then:

```
cc-cli build
```

### `cc-cli build`

Triggers the Generate Calendar workflow on your fork.

### `cc-cli status`

Shows recent workflow runs.

## What you'll need

- A [Supabase](https://supabase.com) account and access token
- A [GitHub OAuth App](https://github.com/settings/developers) (Client ID + Secret)
- A [Google OAuth App](https://console.cloud.google.com/apis/credentials) (Client ID + Secret)
- An [Anthropic API key](https://console.anthropic.com) (for event classification)
- Optionally: [OpenAI](https://platform.openai.com) and [Ticketmaster](https://developer.ticketmaster.com) API keys
