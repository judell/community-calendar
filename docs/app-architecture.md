# App Architecture

The app uses [XMLUI](https://xmlui.org) — a declarative UI framework — with Supabase as the backend.

## XMLUI Frontend

**`Main.xmlui`** - Declarative UI that fetches events from Supabase:

```xml
<App name="Community Calendar">
  <DataSource
    id="events"
    url="{appGlobals.supabaseUrl + '/rest/v1/events?...'}"
    headers="{{ apikey: appGlobals.supabasePublishableKey }}"
  />
  <List data="{events}">
    <!-- Event display -->
  </List>
</App>
```

**`config.json`** - XMLUI configuration with Supabase credentials.

**`index.html`** - Loads XMLUI, reads `?city=` URL param, initializes Supabase auth (GitHub OAuth), defines helper functions for date formatting and auth state management.

## Components

```
components/
├── EventCard.xmlui                   # Event display card with snippet + detail modal
├── PickItem.xmlui                    # Pick item in My Picks view
├── PickEditor.xmlui                  # Modal for confirming picks + optional recurrence enrichment
├── AddToCalendar.xmlui               # ICS download button (includes RRULE when available)
├── CaptureDialog.xmlui               # Poster capture: image → Claude API → PickEditor
├── AudioCaptureDialog.xmlui          # Audio capture: mic/file → Whisper → Claude → PickEditor
├── EnrichmentDialog.xmlui            # Enrichment management dialog
├── MyPicksDialog.xmlui               # My Picks view dialog
└── SourcesDialog.xmlui               # Sources modal
```

## Local Development

Run locally with `python3 -m http.server 8080`, then visit `http://localhost:8080/?city=santarosa`. The app fetches live data from Supabase, so events display without a build.

**Auth redirect for localhost:** GitHub OAuth redirects through Supabase back to your app. For this to work locally, `http://localhost:8080/**` must be in the Supabase dashboard under **Authentication > URL Configuration > Redirect URLs**. The wildcard is required — `http://localhost:8080` without `/**` won't match URLs with query parameters like `?city=santarosa`.

## XMLUI Resources

- [XMLUI Documentation](https://xmlui.org)
- [DataSource Component](https://docs.xmlui.org/components/DataSource)
- [Supabase + XMLUI Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/xmlui)
- [Supabase + XMLUI Blog Post](https://blog.xmlui.org/blog/supabase-and-xmlui) - Auth pattern reference
