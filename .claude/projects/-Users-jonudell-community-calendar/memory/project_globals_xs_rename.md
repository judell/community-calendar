---
name: Globals.xs rename
description: XMLUI code-behind file renamed from Main.xmlui.xs to Globals.xs (breaking change)
type: project
---

Main.xmlui.xs is being renamed to Globals.xs. This is a breaking change landing in XMLUI.

**Why:** XMLUI framework change — the code-behind convention is moving to Globals.xs.

**How to apply:** Use Globals.xs (not Main.xmlui.xs) when referencing the code-behind file in docs, code, and conversation. Update any existing references.
