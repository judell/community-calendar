# cc-cli

Command-line tool to set up a Community Calendar fork with its own Supabase backend.

## Prerequisites

- **Go** (1.22+) — only needed if building from source
- **GitHub CLI (`gh`)** — required for all operations
  - Install: https://cli.github.com/
  - Authenticate: `gh auth login`

## Install

Since `gh` is already required, the easiest way to install is:

```
# macOS Apple Silicon (M1/M2/M3/M4)
gh release download -R judell/community-calendar -p 'cc-cli-darwin-arm64'
sudo mv cc-cli-darwin-arm64 /usr/local/bin/cc-cli
chmod +x /usr/local/bin/cc-cli

# macOS Intel
gh release download -R judell/community-calendar -p 'cc-cli-darwin-amd64'
sudo mv cc-cli-darwin-amd64 /usr/local/bin/cc-cli
chmod +x /usr/local/bin/cc-cli

# Linux x86_64
gh release download -R judell/community-calendar -p 'cc-cli-linux-amd64'
sudo mv cc-cli-linux-amd64 /usr/local/bin/cc-cli
chmod +x /usr/local/bin/cc-cli

# Linux ARM64
gh release download -R judell/community-calendar -p 'cc-cli-linux-arm64'
sudo mv cc-cli-linux-arm64 /usr/local/bin/cc-cli
chmod +x /usr/local/bin/cc-cli

# Windows (run in PowerShell)
gh release download -R judell/community-calendar -p 'cc-cli-windows-amd64.exe'
Rename-Item cc-cli-windows-amd64.exe cc-cli.exe
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
- A [GitHub OAuth App](https://github.com/settings/developers) (Client ID + Secret) — required for admin login
- Optionally: a [Google OAuth App](https://console.cloud.google.com/apis/credentials) (Client ID + Secret) — enables Google login for users
- An [Anthropic API key](https://console.anthropic.com) (for event classification and image recognition)
- Optionally: [OpenAI](https://platform.openai.com) API key (for audio transcription) and [Ticketmaster](https://developer.ticketmaster.com) API key (for venue-based event discovery)
