import React, { useState } from 'react';
import { User, LogOut, Rss } from 'lucide-react';
import { useAuth } from '../hooks/useAuth.jsx';
import SignInModal from './SignInModal.jsx';
import SourcesDialog from './SourcesDialog.jsx';

const CITY_NAMES = {
  santarosa: 'Santa Rosa',
  davis: 'Davis',
  bloomington: 'Bloomington',
  petaluma: 'Petaluma',
  toronto: 'Toronto',
  raleighdurham: 'Raleigh-Durham',
  montclair: 'Montclair',
  roanoke: 'Roanoke',
  matsu: 'MatSu',
  jweekly: 'JWeekly',
  evanston: 'Evanston',
  portland: 'Portland',
  boston: 'Boston',
};

export default function Header({ city, events }) {
  const { user, signOut } = useAuth();
  const [showSignIn, setShowSignIn] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const cityName = CITY_NAMES[city] || city;

  const displayName = user?.user_metadata?.preferred_username
    || user?.user_metadata?.full_name
    || user?.email
    || '';

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 truncate">
          {cityName}
        </h1>

        <div className="flex items-center gap-2">
          {/* Sources button */}
          <button
            onClick={() => setShowSources(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            title="View sources"
          >
            <Rss size={16} />
            <span className="hidden sm:inline">Sources</span>
          </button>

          {/* Auth */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(v => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
              >
                <User size={16} />
                <span className="hidden sm:inline max-w-[120px] truncate">{displayName}</span>
              </button>
              {showUserMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                  <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 min-w-[160px]">
                    <div className="px-3 py-2 text-xs text-gray-400 truncate border-b border-gray-100">
                      {user.email}
                    </div>
                    <button
                      onClick={() => { setShowUserMenu(false); signOut(); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                    >
                      <LogOut size={14} />
                      Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              onClick={() => setShowSignIn(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <User size={16} />
              <span className="hidden sm:inline">Sign in</span>
            </button>
          )}
        </div>
      </div>

      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}
      {showSources && <SourcesDialog events={events} onClose={() => setShowSources(false)} />}
    </>
  );
}
