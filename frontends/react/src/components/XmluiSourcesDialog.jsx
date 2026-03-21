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
  <IFrame src="./xs-diff.html" height="90vh" width="95vw" />
</Fragment>
`;

export default function XmluiSourcesDialog({ events, onClose }) {
  const globalProps = useMemo(() => ({ events }), [events]);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
         onClick={onClose}>
      <XmluiEmbed
        xmlui={sourcesXmlui}
        entry={entry}
        globalProps={globalProps}
        onClick={e => e.stopPropagation()}
      />
    </div>
  );
}
