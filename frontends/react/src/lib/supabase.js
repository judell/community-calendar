import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://dzpdualvwspgqghrysyz.supabase.co';
const SUPABASE_KEY = 'sb_publishable_NnzobdoFNU39fjs84UNq8Q_X45oiMG5';
const SUPABASE_ANON_KEY = SUPABASE_KEY;

// Use the anon JWT key for createClient — the publishable key is not a JWT
// and gets rejected by the edge function gateway.
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
export { SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY };
