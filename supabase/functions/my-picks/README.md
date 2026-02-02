# my-picks Edge Function

Generates an ICS calendar feed from a user's picked events.

## Deployment

```bash
# Install Supabase CLI if needed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref dzpdualvwspgqghrysyz

# Deploy the function (--no-verify-jwt allows calendar apps to subscribe without auth header)
supabase functions deploy my-picks --no-verify-jwt
```

## Usage

```
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>
```

Returns an ICS file with the user's picked events.

### Subscribe in Calendar Apps

**Google Calendar:**
1. Settings → Add calendar → From URL
2. Paste the feed URL

**Apple Calendar:**
1. File → New Calendar Subscription
2. Paste the feed URL

**Outlook:**
1. Add calendar → Subscribe from web
2. Paste the feed URL

## Response

- **Success**: Returns `text/calendar` ICS file
- **Missing token**: 400 Bad Request
- **Invalid token**: 401 Unauthorized
- **Error**: 500 Internal Server Error
