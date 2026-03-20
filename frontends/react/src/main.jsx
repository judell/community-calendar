import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from './hooks/useAuth.jsx'
import { CuratorProvider } from './hooks/useCurator.jsx'
import { PicksProvider } from './hooks/usePicks.jsx'
import { FeaturedProvider } from './hooks/useFeatured.jsx'
import { TargetCollectionProvider } from './hooks/useTargetCollection.jsx'
import { EmbedViewportProvider } from './hooks/useEmbedViewport.jsx'
import './index.css'

function Root() {
  // Read city for PicksProvider
  const city = new URLSearchParams(window.location.search).get('city') || null;

  return (
    <React.StrictMode>
      <AuthProvider>
        <CuratorProvider>
          <PicksProvider city={city}>
            <FeaturedProvider city={city}>
              <TargetCollectionProvider>
                <EmbedViewportProvider>
                  <App />
                </EmbedViewportProvider>
              </TargetCollectionProvider>
            </FeaturedProvider>
          </PicksProvider>
        </CuratorProvider>
      </AuthProvider>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<Root />)
