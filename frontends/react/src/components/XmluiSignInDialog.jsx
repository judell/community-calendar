import React, { useMemo } from 'react';
import XmluiEmbed from './XmluiEmbed.jsx';
import { useAuth } from '../hooks/useAuth.jsx';
import signInXmlui from '../../../xmlui/components/SignInDialog.xmlui?raw';

const entry = `
<Fragment var.ready="{false}" onInit="() => { ready = true; sd.open(); }">
  <SignInDialog id="sd" />
</Fragment>
`;

export default function XmluiSignInDialog({ onClose }) {
  const { signIn } = useAuth();

  // Bridge React auth functions to window for XMLUI expressions
  window.signIn = signIn;
  window.signInWithEmail = async function(email, onSuccess) {
    const { supabase } = await import('../lib/supabase.js');
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin + window.location.pathname + window.location.search }
    });
    if (error) alert('Error: ' + error.message);
    else if (onSuccess) onSuccess();
  };

  return (
    <XmluiEmbed
      xmlui={signInXmlui}
      entry={entry}
    />
  );
}
