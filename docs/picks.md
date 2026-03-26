# Personal Picks

Users authenticate and save personal event picks, then subscribe to a personal ICS feed in their calendar app.

```
┌─────────────────────────────────────────────────────────┐
│  User authenticates via GitHub OAuth (user icon)        │
│                    ↓                                    │
│  Browse events, click checkbox to add to picks          │
│                    ↓                                    │
│  Click calendar icon to view My Picks dialog            │
│                    ↓                                    │
│  Personal ICS feed URL with unique token                │
│                    ↓                                    │
│  Subscribe in Google Calendar / Apple Calendar          │
└─────────────────────────────────────────────────────────┘
```

## OAuth Flow

App → Supabase → GitHub → Supabase → App. The `signIn()` function in `index.html` navigates directly to the Supabase auth endpoint (not using the Supabase JS `signInWithOAuth` method). Identity comes from the GitHub account the user is logged into. Session stored in localStorage (`sb-*-auth-token`), not cookies. To test with a different identity, use incognito or revoke the app at GitHub → Settings → Applications.

## Admin Access

Privileged UI features (audio capture) are gated by server-side tables (`admin_github_users`), not by hardcoded GitHub usernames in frontend code. The app queries this table via a DataSource and conditionally shows admin UI.

## Database Tables

- `picks` - user_id + event_id with joined events data (RLS-protected)
- `feed_tokens` - unique token per user for ICS feed URL

## Implementation Details

- Feed token created automatically on first sign-in (page reloads to sync DataSource)
- Picking: checkbox opens PickEditor modal for confirmation + optional recurrence enrichment
- Unpicking: one-click checkbox remove (no modal), deletes pick + any associated enrichment
- "all" / "my picks" radio group toggles between full feed and personal picks view
- DataSource refresh via `refreshCounter` in Main.xmlui.xs + ChangeListener in Main.xmlui

## Edge Function: my-picks

- Validates token, returns user's picks as ICS (default) or JSON (`?format=json`)
- Deploy with `--no-verify-jwt` to allow calendar app subscriptions (token provides auth)
- Example: `https://<project>.supabase.co/functions/v1/my-picks?token=<feed_token>`
- Note: Calendar apps poll ICS feeds periodically (Google: 12-24h, Apple: 15min-1h)

## Cross-Source Duplicate Handling

- Same event from different sources (e.g., GoLocal + Cal Theatre) gets merged in display
- Dedupe tracks `mergedIds` array for all source variants
- Picks work across sources: checking/unchecking normalizes to the primary ID

## Responsive UI

- Modal dialog uses `minWidth="70vw"` for mobile compatibility
- Text uses `overflowMode="flow"` for proper wrapping
