import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { supabase, SUPABASE_URL, SUPABASE_KEY } from '../lib/supabase.js';
import { useAuth } from './useAuth.jsx';

const CuratorContext = createContext({ isCurator: false, curatorCities: [], isCuratorForCity: () => false });

export function CuratorProvider({ children }) {
  const { user, session } = useAuth();
  const [isCurator, setIsCurator] = useState(false);
  const [curatorCities, setCuratorCities] = useState([]);

  useEffect(() => {
    if (!user || !session) {
      setIsCurator(false);
      setCuratorCities([]);
      return;
    }

    const headers = {
      apikey: SUPABASE_KEY,
      Authorization: 'Bearer ' + session.access_token,
    };

    // Check all three curator tables + admin tables in parallel.
    // RLS ensures each query returns at most the user's own row.
    async function check() {
      try {
        const urls = [
          `${SUPABASE_URL}/rest/v1/curator_users?select=user_id,cities&user_id=eq.${user.id}&limit=1`,
          `${SUPABASE_URL}/rest/v1/curator_github_users?select=github_user,cities&limit=1`,
          `${SUPABASE_URL}/rest/v1/curator_google_users?select=google_email,cities&limit=1`,
          `${SUPABASE_URL}/rest/v1/admin_users?select=user_id&user_id=eq.${user.id}&limit=1`,
          `${SUPABASE_URL}/rest/v1/admin_github_users?select=github_user&limit=1`,
          `${SUPABASE_URL}/rest/v1/admin_google_users?select=google_email&limit=1`,
        ];

        const results = await Promise.all(
          urls.map(url => fetch(url, { headers }).then(r => r.json()).catch(() => []))
        );

        const [curatorRows, githubRows, googleRows, adminRows, adminGhRows, adminGoogleRows] = results;

        const isAdmin = [adminRows, adminGhRows, adminGoogleRows].some(r => Array.isArray(r) && r.length > 0);
        const curatorMatches = [curatorRows, githubRows, googleRows].filter(r => Array.isArray(r) && r.length > 0);
        const matched = isAdmin || curatorMatches.length > 0;

        setIsCurator(matched);

        if (isAdmin) {
          // Admins are global curators — empty array means all cities
          setCuratorCities([]);
        } else if (curatorMatches.length > 0) {
          // Merge cities arrays from all matching curator rows
          const allCities = new Set();
          let hasGlobal = false;
          for (const rows of curatorMatches) {
            for (const row of rows) {
              const cities = row.cities;
              if (!cities || cities.length === 0) {
                hasGlobal = true;
              } else {
                cities.forEach(c => allCities.add(c));
              }
            }
          }
          setCuratorCities(hasGlobal ? [] : [...allCities]);
        } else {
          setCuratorCities([]);
        }
      } catch (e) {
        setIsCurator(false);
        setCuratorCities([]);
      }
    }

    check();
  }, [user, session]);

  const isCuratorForCity = useCallback((city) => {
    if (!isCurator) return false;
    // Empty curatorCities = global curator (all cities)
    if (curatorCities.length === 0) return true;
    return curatorCities.includes(city);
  }, [isCurator, curatorCities]);

  return (
    <CuratorContext.Provider value={{ isCurator, curatorCities, isCuratorForCity }}>
      {children}
    </CuratorContext.Provider>
  );
}

export function useCurator() {
  return useContext(CuratorContext);
}
