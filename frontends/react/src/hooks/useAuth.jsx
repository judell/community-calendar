import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { supabase, SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    // Pre-populate from localStorage for instant availability
    try {
      const projRef = new URL(SUPABASE_URL).hostname.split('.')[0];
      const stored = localStorage.getItem('sb-' + projRef + '-auth-token');
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed?.user || null;
      }
    } catch (e) {}
    return null;
  });

  const [session, setSession] = useState(() => {
    try {
      const projRef = new URL(SUPABASE_URL).hostname.split('.')[0];
      const stored = localStorage.getItem('sb-' + projRef + '-auth-token');
      if (stored) return JSON.parse(stored);
    } catch (e) {}
    return null;
  });

  useEffect(() => {
    // Handle OAuth callback — hash contains access_token after redirect
    if (window.location.hash.includes('access_token')) {
      supabase.auth.getSession().then(() => {
        window.location.replace(window.location.pathname + window.location.search);
      });
      return;
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, sess) => {
      setSession(sess);
      setUser(sess?.user || null);

      // Create feed token on first sign-in
      if (sess?.user) {
        const headers = {
          apikey: SUPABASE_KEY,
          Authorization: 'Bearer ' + sess.access_token,
          'Content-Type': 'application/json',
          Prefer: 'return=minimal',
        };
        try {
          const checkUrl = `${SUPABASE_URL}/rest/v1/feed_tokens?select=token&user_id=eq.${sess.user.id}`;
          const checkRes = await fetch(checkUrl, { headers });
          const existing = await checkRes.json();
          if (!existing || existing.length === 0) {
            await fetch(`${SUPABASE_URL}/rest/v1/feed_tokens`, {
              method: 'POST',
              headers,
              body: JSON.stringify({ user_id: sess.user.id }),
            });
          }
        } catch (e) {}
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = useCallback((provider = 'github') => {
    const returnTo = window.location.origin + window.location.pathname + window.location.search;
    window.location.href = `${SUPABASE_URL}/auth/v1/authorize?provider=${provider}&redirect_to=${encodeURIComponent(returnTo)}`;
  }, []);

  const signOut = useCallback(() => {
    const projRef = SUPABASE_URL.match(/https:\/\/([^.]+)\.supabase\.co/)?.[1];
    if (projRef) localStorage.removeItem(`sb-${projRef}-auth-token`);
    window.location.reload();
  }, []);

  return (
    <AuthContext.Provider value={{ user, session, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
