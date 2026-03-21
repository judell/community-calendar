import React, { useMemo } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AppRoot, ApiInterceptorProvider, xmlUiMarkupToComponent } from 'xmlui';

const SUPABASE_URL = 'https://dzpdualvwspgqghrysyz.supabase.co';
const SUPABASE_KEY = 'sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5';

/**
 * Embeds an XMLUI compound component inside a React app.
 *
 * Props:
 *   xmlui        - raw .xmlui file content (via ?raw import)
 *   entry        - XMLUI markup string that instantiates the component
 *   globalProps  - additional data to pass as appGlobals (merged with supabase config)
 *   children     - optional React children
 */
export default function XmluiEmbed({ xmlui, entry, globalProps = {}, className, onClick, children }) {
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
      {children}
    </div>
  );
}
