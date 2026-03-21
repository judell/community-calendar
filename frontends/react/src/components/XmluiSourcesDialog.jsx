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

export default function XmluiSourcesDialog({ events, onClose }) {
  const globalProps = useMemo(() => ({ events }), [events]);

  return (
    <XmluiEmbed
      xmlui={sourcesXmlui}
      entry={entry}
      globalProps={globalProps}
    />
  );
}
