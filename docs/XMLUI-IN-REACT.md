# Embedding XMLUI Components in a React App



https://github.com/user-attachments/assets/01f37d46-5531-4656-b35b-ba7e9777d22e



This documents a working proof-of-concept: rendering XMLUI components inside a React/Tailwind frontend, using the same `.xmlui` source files that power the XMLUI frontend. Two components are shared so far — **SourcesDialog** (source list, event counts, suggest-a-source form with Supabase submission) and **SignInDialog** (GitHub, Google, and magic-link auth) — both rendering and functioning identically in both frontends from the same source files.

## What this means

Shared interactive components (modals, forms, editors) can be written once as `.xmlui` files and consumed by both frontends. The XMLUI frontend uses them natively. The React frontend imports them as raw strings and renders them via XMLUI's React-based runtime. Changes to a `.xmlui` component are reflected in both frontends automatically.

## Architecture

```
React App
  └── XmluiSourcesDialog.jsx (React wrapper)
        ├── import SourcesDialog.xmlui?raw     — Vite loads markup as string
        ├── xmlUiMarkupToComponent()           — parses into compound component def
        ├── entry markup                       — inline XMLUI that instantiates + opens it
        ├── <BrowserRouter>                    — required by XMLUI internals
        │     └── <ApiInterceptorProvider>     — required by APICall component
        │           └── <AppRoot>              — XMLUI root renderer
        │                 node={entry}         — the entry point node
        │                 contributes={}       — registers the compound component
        │                 globalProps={}       — data bridge: React → XMLUI
        └── window.*                           — function bridge for XMLUI expressions
```

## Sourcing from the original .xmlui file

The React wrapper imports the `.xmlui` file as a raw string, parses it as a compound component, registers it via `contributes`, and instantiates it with a tiny entry markup:

```jsx
import sourcesXmlui from '../../../xmlui/components/SourcesDialog.xmlui?raw';

const compoundComponent = xmlUiMarkupToComponent(sourcesXmlui);

const entryNode = xmlUiMarkupToComponent(`
  <Fragment var.ready="{false}" onInit="() => { ready = true; sd.open(); }">
    <SourcesDialog id="sd" events="{appGlobals.events}" />
  </Fragment>
`);

<AppRoot
  node={entryNode.component}
  contributes={{ compoundComponents: [compoundComponent.component] }}
  globalProps={globalProps}
/>
```

## Data flow: React → XMLUI

React passes data via `globalProps` on `AppRoot`. In entry markup, access as `appGlobals.*`. Inside compound components, data arrives via `$props.*`:

```jsx
// React
<AppRoot globalProps={{ events, supabaseUrl: '...' }} />
```

```xml
<!-- Entry markup -->
<SourcesDialog events="{appGlobals.events}" />

<!-- Inside compound component -->
<Text value="{$props.events.length + ' events'}" />
```

**Important:** `appGlobals` (no `$` prefix) in entry markup. `$props` inside compound components. `$appGlobals` silently evaluates to undefined.

## Function bridge

XMLUI expressions call `window.*` functions. If the `.xmlui` component references helpers, assign them to `window` in the React wrapper:

```jsx
import { getSourceCounts, dedupeEvents } from '../lib/helpers.js';

window.getSourceCounts = getSourceCounts;
window.dedupeEvents = dedupeEvents;
window.getQueryMonths = function() { return 3; };
```

## CSS: Tailwind + XMLUI coexistence

Two conflicts arise when XMLUI components render inside a Tailwind app, plus one consequence of the fix.

### Problem 1: Tailwind preflight strips XMLUI styles

Tailwind's preflight sets `button { background-color: transparent }` and `* { border-style: solid }`, which removes XMLUI button backgrounds and adds unwanted borders.

**Fix:** Disable preflight:

```js
// tailwind.config.js
corePlugins: {
  preflight: false,
},
```

### Problem 2: XMLUI's CSS `@layer` conflicts with Tailwind at build time

XMLUI's JS imports `index.css` which uses `@layer` directives. Tailwind's PostCSS processing chokes on these. Both use layer names like `base` and `components` that collide.

**Fix:** A custom Vite plugin intercepts XMLUI's CSS import, replaces it with an empty module, and copies the CSS as a separate asset:

```js
function externalizeXmluiCss() {
  return {
    name: 'externalize-xmlui-css',
    enforce: 'pre',
    resolveId(source, importer) {
      if (source === './index.css' && importer?.includes('xmlui'))
        return { id: 'virtual:xmlui-css', external: false }
    },
    load(id) {
      if (id === 'virtual:xmlui-css') return ''
    },
    generateBundle() {
      this.emitFile({
        type: 'asset', fileName: 'xmlui.css',
        source: fs.readFileSync(
          path.resolve(__dirname, 'node_modules/xmlui/dist/lib/index.css')),
      })
    },
    transformIndexHtml() {
      return [{ tag: 'link', attrs: { rel: 'stylesheet', href: './xmlui.css' }, injectTo: 'head' }]
    },
  }
}
```

### Consequence: disabling preflight removes base resets

Without preflight, the browser defaults return (Times New Roman, no box-sizing, etc.). Re-add what the React app needs in `index.css`:

```css
*, *::before, *::after { box-sizing: border-box; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; tab-size: 4; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
}
img, svg, video, canvas { display: block; max-width: 100%; }
h1, h2, h3, h4, h5, h6, p { margin: 0; }
a { color: inherit; text-decoration: inherit; }
```

### Problem 3: Double focus ring on inputs

XMLUI wraps inputs in a `<div tabindex="-1">` that renders its own focus ring. Without preflight suppressing the browser's default `:focus` outline, both the wrapper's ring and the input's ring appear.

**Fix:** In a separate `xmlui-fixes.css` (imported after `index.css` to stay outside Tailwind's `@layer` processing):

```css
[data-part-id="input"]:focus,
[data-part-id="input"]:focus-visible,
textarea:focus,
textarea:focus-visible {
  outline: none !important;
  box-shadow: none !important;
  border-color: inherit !important;
}
```

`data-part-id="input"` is XMLUI's own attribute on inner input elements, so this doesn't affect the React app's inputs.

## Vite configuration

### Alias to pre-built XMLUI library

XMLUI's `package.json` points `main` at source TypeScript. Alias to the pre-built output to avoid SCSS compilation:

```js
resolve: {
  alias: {
    xmlui: path.resolve(__dirname, 'node_modules/xmlui/dist/lib/xmlui.js'),
    react: path.resolve(__dirname, 'node_modules/react'),
    'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
  },
},
```

The React aliases ensure XMLUI shares the same React instance (prevents hooks errors).

## npm setup

```bash
cd frontends/react
npm link /path/to/xmlui/xmlui
npm install react-router-dom
npm install --save-dev sass
```

Note: `npm install` breaks the link — re-run `npm link` after installing other packages.

## The reusable XmluiEmbed wrapper

All XMLUI embedding boilerplate lives in `XmluiEmbed.jsx`. It handles parsing, context providers, and Supabase config:

```jsx
import React, { useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AppRoot, ApiInterceptorProvider, xmlUiMarkupToComponent } from 'xmlui';

const SUPABASE_URL = 'https://dzpdualvwspgqghrysyz.supabase.co';
const SUPABASE_KEY = 'sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5';

export default function XmluiEmbed({ xmlui, entry, globalProps = {}, className, onClick }) {
  const compoundComponent = useMemo(() => xmlUiMarkupToComponent(xmlui), [xmlui]);
  const entryNode = useMemo(() => xmlUiMarkupToComponent(entry), [entry]);
  const mergedProps = useMemo(() => ({
    supabaseUrl: SUPABASE_URL,
    supabasePublishableKey: SUPABASE_KEY,
    xsVerbose: true,
    xsVerboseLogMax: 200,
    ...globalProps,
  }), [globalProps]);

  if (compoundComponent.errors?.length || entryNode.errors?.length) {
    console.error('XMLUI parse errors:', compoundComponent.errors, entryNode.errors);
    return <div>Error loading XMLUI component</div>;
  }

  return (
    <div className={className} onClick={onClick}>
      <BrowserRouter>
        <ApiInterceptorProvider>
          <AppRoot
            node={entryNode.component}
            standalone={true}
            contributes={{ compoundComponents: [compoundComponent.component] }}
            globalProps={mergedProps}
          />
        </ApiInterceptorProvider>
      </BrowserRouter>
    </div>
  );
}
```

Each shared component then just specifies what's unique — the `.xmlui` file, entry markup, props, and helpers:

```jsx
import React, { useMemo } from 'react';
import XmluiEmbed from './XmluiEmbed.jsx';
import { getSourceCounts, dedupeEvents } from '../lib/helpers.js';
import sourcesXmlui from '../../../xmlui/components/SourcesDialog.xmlui?raw';

window.getSourceCounts = getSourceCounts;
window.dedupeEvents = dedupeEvents;
window.getQueryMonths = function() { return 3; };

const entry = `
<Fragment var.ready="{false}" onInit="() => { ready = true; sd.open(); }">
  <SourcesDialog id="sd" events="{appGlobals.events}" />
</Fragment>
`;

export default function XmluiSourcesDialog({ events }) {
  const globalProps = useMemo(() => ({ events }), [events]);

  return (
    <XmluiEmbed
      xmlui={sourcesXmlui}
      entry={entry}
      globalProps={globalProps}
    />
  );
}
```

## Before and after: duplicated React vs shared XMLUI

Cathy's React frontend originally reimplemented the SourcesDialog from scratch — 198 lines of React state management, fetch calls, Tailwind classes, and Lucide icons. The shared approach uses the original 187-line `.xmlui` source plus a 30-line React wrapper (and a 47-line `XmluiEmbed` helper shared across all components).

The advantage isn't line count — it's **single-source behavior**. The reimplemented React version is a separate copy that must be maintained independently. When the XMLUI version gets a new feature (e.g., a checkbox to hide sources, which already exists in the XMLUI app), the React version needs a parallel implementation. With the shared approach, both frontends get it for free from the same `.xmlui` file.

Other advantages of the shared approach:
- **No behavior drift** — both frontends render the same component, so they can't diverge
- **Backend logic stays declarative** — the `APICall`, form validation, and state management are expressed in XMLUI markup, not reimplemented in imperative React
- **Per-component cost drops** — `XmluiEmbed` is written once; each new shared component is ~30 lines of wrapper

<details>
<summary>SourcesDialog.xmlui — 187 lines, the single source of truth</summary>

```xml
<Component
  name="SourcesDialog"
  method.open="() => { suggestName = ''; suggestUrl = ''; suggestFeedType = '';
    suggestNotes = ''; suggestSuccess = false; suggestError = '';
    showSuggestForm = false; dialog.open(); }"
  var.showSuggestForm="{false}"
  var.suggestName=""
  var.suggestUrl=""
  var.suggestFeedType=""
  var.suggestNotes=""
  var.isSubmitting="{false}"
  var.suggestSuccess="{false}"
  var.suggestError="">

  <APICall id="suggestApi" method="post"
    url="{appGlobals.supabaseUrl + '/rest/v1/source_suggestions'}"
    headers="{{ 'Content-Type': 'application/json',
      'apikey': appGlobals.supabasePublishableKey,
      'Prefer': 'return=minimal' }}"
    body="{$param}"
    onSuccess="() => { isSubmitting = false; suggestSuccess = true; }"
    onError="() => { isSubmitting = false;
      suggestError = 'Failed to submit suggestion.'; }" />

  <ModalDialog id="dialog" title="Sources">
    <VStack gap="$space-3">
      <Text value="{$props.events
        ? window.dedupeEvents($props.events).length
          + ' events for the next '
          + window.getQueryMonths() + ' months'
        : 'Loading...'}" />
      <Items data="{window.getSourceCounts(
          window.dedupeEvents($props.events))}">
        <HStack gap="$space-2" paddingVertical="$space-1">
          <Text width="40px" textAlign="right" fontWeight="bold"
            value="{$item.count}" />
          <Text value="{$item.source}" />
        </HStack>
      </Items>
      <Button when="{!showSuggestForm}" label="Suggest a source"
        variant="outlined" icon="l-plus"
        onClick="showSuggestForm = true" />
      <!-- ... suggest form, success state, etc. -->
    </VStack>
  </ModalDialog>
</Component>
```

</details>

<details>
<summary>Cathy's SourcesDialog.jsx — 198 lines, reimplemented in React</summary>

```jsx
import React, { useState, useMemo } from 'react';
import { X, Plus, CheckCircle, Rss } from 'lucide-react';
import { getSourceCounts } from '../lib/helpers.js';
import { SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

export default function SourcesDialog({ events, onClose }) {
  const [showSuggestForm, setShowSuggestForm] = useState(false);
  const [suggestName, setSuggestName] = useState('');
  const [suggestUrl, setSuggestUrl] = useState('');
  const [suggestFeedType, setSuggestFeedType] = useState('');
  const [suggestNotes, setSuggestNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestSuccess, setSuggestSuccess] = useState(false);
  const [suggestError, setSuggestError] = useState('');

  const sourceCounts = useMemo(() => getSourceCounts(events), [events]);

  const city = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('city') || 'unknown';
  }, []);

  async function handleSubmit() {
    setIsSubmitting(true);
    setSuggestError('');
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/source_suggestions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          apikey: SUPABASE_KEY,
          Prefer: 'return=minimal',
        },
        body: JSON.stringify({
          city,
          name: suggestName,
          url: suggestUrl,
          feed_type: suggestFeedType || null,
          notes: suggestNotes || null,
        }),
      });
      if (!res.ok) throw new Error('Failed');
      setSuggestSuccess(true);
    } catch {
      setSuggestError('Failed to submit suggestion. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetForm() {
    setSuggestSuccess(false);
    setSuggestName('');
    setSuggestUrl('');
    setSuggestFeedType('');
    setSuggestNotes('');
    setSuggestError('');
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <div className="bg-white rounded-xl max-w-md w-full max-h-[80vh] overflow-y-auto shadow-xl"
           onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <Rss size={18} className="text-gray-400" />
            <h2 className="text-lg font-bold text-gray-900">Sources</h2>
          </div>
          <button onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="px-6 pb-5">
          <p className="text-sm text-gray-500 mb-4">
            {events ? `${events.length} events` : 'Loading...'}
            <span className="text-gray-400"> · counts reflect overlap</span>
          </p>
          <div className="space-y-1 mb-5">
            {sourceCounts.map(({ source, count }) => (
              <div key={source} className="flex items-center gap-3 py-1.5">
                <span className="text-sm font-semibold text-gray-700 w-8
                       text-right tabular-nums">{count}</span>
                <span className="text-sm text-gray-600">{source}</span>
              </div>
            ))}
          </div>
          {/* ... 80 more lines of suggest form, success state, etc. */}
        </div>
      </div>
    </div>
  );
}
```

</details>

<details>
<summary>XmluiSourcesDialog.jsx — 30 lines, wrapper that embeds the .xmlui component</summary>

```jsx
import React, { useMemo } from 'react';
import XmluiEmbed from './XmluiEmbed.jsx';
import { getSourceCounts, dedupeEvents } from '../lib/helpers.js';
import sourcesXmlui from '../../../xmlui/components/SourcesDialog.xmlui?raw';

window.getSourceCounts = getSourceCounts;
window.dedupeEvents = dedupeEvents;
window.getQueryMonths = function() { return 3; };

const entry = `
<Fragment var.ready="{false}" onInit="() => { ready = true; sd.open(); }">
  <SourcesDialog id="sd" events="{appGlobals.events}" />
</Fragment>
`;

export default function XmluiSourcesDialog({ events }) {
  const globalProps = useMemo(() => ({ events }), [events]);

  return (
    <XmluiEmbed
      xmlui={sourcesXmlui}
      entry={entry}
      globalProps={globalProps}
    />
  );
}
```

</details>

The total line count is higher for the shared approach (187 + 30 + 47 = 264 vs 198). But the 47-line `XmluiEmbed` is written once and reused for every shared component, and the 187-line `.xmlui` file already exists — it's not new code. The marginal cost of sharing the next component is ~30 lines of wrapper.

## Frontend switching

The router `index.html` supports both config-based and URL-based frontend switching:

- **Config-based**: set `"frontend": "react"` or `"frontend": "xmlui"` in `config.json`
- **URL-based**: append `?frontend=react` or `?frontend=xmlui` to the URL (overrides config, param is stripped before redirect)

## Files changed

| File | Change |
|------|--------|
| `index.html` | URL-based frontend switching (`?frontend=react`) |
| `config.json` | `"frontend": "xmlui"` → `"frontend": "react"` (default switch) |
| `frontends/react/src/components/Header.jsx` | Imports → `XmluiSourcesDialog.jsx`, `XmluiSignInDialog.jsx` |
| `frontends/react/src/components/XmluiEmbed.jsx` | **New** — reusable XMLUI embedding wrapper |
| `frontends/react/src/components/XmluiSourcesDialog.jsx` | **New** — wrapper for SourcesDialog.xmlui |
| `frontends/react/src/components/XmluiSignInDialog.jsx` | **New** — wrapper for SignInDialog.xmlui |
| `frontends/react/src/xmlui-fixes.css` | **New** — suppresses double focus ring on XMLUI inputs |
| `frontends/react/src/index.css` | Added base resets (box-sizing, font-family, margins) |
| `frontends/react/src/main.jsx` | Added `import './xmlui-fixes.css'` |
| `frontends/react/tailwind.config.js` | Added `corePlugins: { preflight: false }` |
| `frontends/react/vite.config.js` | Added XMLUI CSS externalizer plugin, React/XMLUI aliases, Inspector files |
| `frontends/react/package.json` | Added `react-router-dom`, `sass` |
| `docs/XMLUI-IN-REACT.md` | **New** — this document |

## XMLUI Inspector works in the React app

The XMLUI Inspector — the interactive trace viewer for debugging interactions, state changes, and performance — works on embedded XMLUI components. Enable it by:

1. Setting `xsVerbose: true` in `globalProps` (done in `XmluiEmbed`)
2. Adding `xs-diff.html` and `xmlui-parser.es.js` to the build output (done in the Vite plugin)
3. Adding `<IFrame src="./xs-diff.html" />` to the XMLUI entry markup

The Inspector immediately proved useful: it showed that each keystroke in the suggest form takes 350–1200ms, confirming the typing sluggishness is caused by XMLUI re-evaluating expressions against 3600+ events in `appGlobals` on every state change.

## Dead ends and lessons

1. **Importing XMLUI source** — pulls in SCSS, requires full build toolchain. Fix: alias to `dist/lib/xmlui.js`.

2. **UMD standalone bundle** — bundles its own React, causing dual-React hooks errors. Fix: use the ES module library build.

3. **`StandaloneComponent`** — provides no context (no theme, API, or router). Fix: use `AppRoot` + `ApiInterceptorProvider` + `BrowserRouter`.

4. **Inline markup only** — first working version inlined dialog content. Worked but couldn't reuse the original `.xmlui` file. Fix: compound component pattern with `contributes`.

5. **`onInit` on compound component instances** — didn't fire. Fix: wrap in `<Fragment>` with its own `onInit`.

6. **`$appGlobals` vs `appGlobals`** — entry markup uses `appGlobals.*` (no `$`). Inside compound components, `$props.*`. Mixing these up fails silently.

7. **Missing `window.*` functions** — `.xmlui` files reference helpers via `window.*`. In the XMLUI app they're loaded via `<script>` tags. In React, import and assign to `window`.

8. **Tailwind preflight** — strips XMLUI button styles. Scoped overrides (`.xmlui-container`, `[data-radix-portal]`, `[style*="--xmlui"]`) all failed because XMLUI's ModalDialog portals to `document.body`. Fix: disable preflight globally, re-add needed base resets.

9. **CSS `@layer` ordering** — tried loading XMLUI CSS before Tailwind to establish layer order. Failed because both use `base` and `components` layer names and the merge doesn't cascade as expected.

10. **Double focus ring** — with preflight off, browser default focus outline + XMLUI wrapper focus ring. Scoped selectors (`[tabindex="-1"] > input`) didn't work because the rule landed inside a `@layer` via Tailwind processing. Fix: separate CSS file imported after Tailwind, targeting `[data-part-id="input"]` with `!important`.

## What's next

- **More components**: PickEditor, AudioCapture, Enrichment — the remaining shared modals.
- **Shared helpers**: The `window.*` function bridge works but is fragile. Consider a shared helpers module both frontends import, with automatic `window` assignment for XMLUI compatibility.
- **Inspector integration**: The Inspector renders via `<IFrame>` but needs z-index/styling work to open cleanly above XMLUI's own ModalDialog portal. The `Inspector` component (which wraps the IFrame in a proper modal) exists in XMLUI source but isn't included in the pre-built library.
