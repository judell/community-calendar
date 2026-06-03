# Triage Labels

Label mapping for the triage state machine.

| Role | Label |
|------|-------|
| Needs triage | `needs-triage` |
| Needs info | `needs-info` |
| Ready for agent | `ready-for-agent` |
| Ready for human | `ready-for-human` |
| Won't fix | `wontfix` |

## Usage

The `triage` skill applies these labels as it moves issues through its state machine:

1. New issues start with `needs-triage`
2. Move to `needs-info` if the reporter needs to provide more details
3. Move to `ready-for-agent` if fully specified and an AFK agent can implement it
4. Move to `ready-for-human` if it needs human implementation
5. Close with `wontfix` if it won't be actioned
