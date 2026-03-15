# Authentication Setup

Community Calendar uses Supabase Auth with three sign-in methods: GitHub OAuth, Google OAuth, and magic link (email).

## Automated setup (cc-cli)

If you use `cc-cli init`, steps 4 and 5 handle GitHub and Google OAuth for you:

- **Step 4** walks you through creating OAuth apps at GitHub and Google, prompting for the callback URL (`https://<your-project>.supabase.co/auth/v1/callback`) and collecting client IDs and secrets.
- **Step 5** calls `UpdateAuthConfig` to enable both providers and set the redirect allow list.

You still need to set up magic link manually (see below).

## Manual setup

### GitHub OAuth

1. Go to https://github.com/settings/developers → "New OAuth App"
2. Homepage URL: your GitHub Pages URL (e.g. `https://<user>.github.io/community-calendar/`)
3. Callback URL: `https://<project-ref>.supabase.co/auth/v1/callback`
4. Copy Client ID and Client Secret
5. In Supabase dashboard: Authentication → Sign In / Providers → GitHub → paste credentials

### Google OAuth

1. Go to https://console.cloud.google.com/apis/credentials
2. Create or select a project
3. Set up OAuth consent screen (External, your email)
4. Create credentials → OAuth client ID → Web application
5. Authorized redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`
6. Copy Client ID and Client Secret
7. In Supabase dashboard: Authentication → Sign In / Providers → Google → paste credentials

### Magic link (email OTP)

Magic link requires a custom SMTP provider because Supabase's built-in email service is limited to 2 emails/hour.

#### 1. Set up Resend (or another SMTP provider)

- Sign up at https://resend.com (free tier: 100 emails/day)
- Add a domain you own (e.g. `calendar.yourdomain.com`)
- Add the DNS records Resend gives you (DKIM TXT, SPF TXT, MX) at your DNS provider
- Wait for domain verification (usually minutes, can take up to an hour)
- Create an API key

#### 2. Configure Supabase SMTP

In Supabase dashboard: Authentication → Email (under Notifications):

- **Sender email:** `noreply@calendar.yourdomain.com`
- **Sender name:** Community Calendar
- **Host:** `smtp.resend.com`
- **Port:** `465`
- **Username:** `resend`
- **Password:** your Resend API key (starts with `re_`)

#### 3. Enable email provider

In Supabase dashboard: Authentication → Sign In / Providers → Email — enable with magic link support.

### Redirect URLs

In Supabase dashboard: Authentication → URL Configuration:

- **Site URL:** your production URL (e.g. `https://<user>.github.io/community-calendar/`)
- **Redirect URLs:** add both production and localhost for development:
  - `https://<user>.github.io/community-calendar/**`
  - `http://localhost:8080/**`

## How it works in the app

- `index.html` initializes the Supabase JS client and pre-populates `window.authUser` / `window.authSession` from localStorage on page load
- `Main.xmlui` reads these into reactive XMLUI global vars (`global.authUser`, `global.authSession`)
- All auth methods cause a page reload, so the globals are always current after sign-in
- `SignInDialog.xmlui` presents all three options; magic link calls `window.signInWithEmail` which uses `sb.auth.signInWithOtp`
- Sign-out clears localStorage and reloads

## Access control

- **Anyone:** search, browse, add-to-calendar, download ICS, hide sources (ephemeral — not saved)
- **Authenticated users:** all above + bookmark/pick events, subscribe to picks feed, capture events (camera/audio), hide sources (persisted to `user_settings`)
- **Admin users:** all above + override event categories (pencil icon), gated by `admin_github_users` and `admin_google_users` tables

The `isAdmin` variable in Main.xmlui is derived from the `adminGithubAccess` and `adminGoogleAccess` DataSources and is visible to all components.

### RLS

- `picks`, `feed_tokens`, `user_settings` scoped by `auth.uid()`
- `events` and `event_enrichments` are public-read
