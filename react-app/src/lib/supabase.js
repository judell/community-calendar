import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://mrarvzihuwgfjvricdte.supabase.co';
const SUPABASE_KEY = 'sb_publishable_7e4Pgqdr22FuLsMVhRYwiA_RVxG5Dw1';

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
export { SUPABASE_URL, SUPABASE_KEY };
