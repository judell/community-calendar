import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from './hooks/useAuth.jsx'
import { PicksProvider } from './hooks/usePicks.jsx'
import './index.css'

function Root() {
  // Read city for PicksProvider
  const city = new URLSearchParams(window.location.search).get('city') || null;

  return (
    <React.StrictMode>
      <AuthProvider>
        <PicksProvider city={city}>
          <App />
        </PicksProvider>
      </AuthProvider>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<Root />)
