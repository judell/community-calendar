# UI Puzzles

Design problems that don't have clean solutions yet.

## 1. Cluster borders lose meaning in search mode

In browse mode, cluster borders work well: events within the same timeslot that are likely the same event (from different sources) get matching colored left borders. Adjacent cards with the same blue border clearly says "these are related."

In search mode, events from different timeslots collapse together. Two Boeing Boeing pairs — one from Feb 27, one from Mar 1 — both get cluster_id=0 (blue), and appear back-to-back. The color no longer signals "same group" — it's coincidental.

**Current solution**: Hide cluster borders entirely in search mode.

**Alternatives considered**:
- Faded borders in search mode — tried this, but even faded borders create false grouping signals across timeslots
- Re-cluster the filtered results — expensive, and the filtered set is arbitrary
- Make cluster_id globally unique instead of per-timeslot — would require many more colors and lose the simplicity of the current 3-color palette
