---
name: runner-list
description: "/runner-list, \"list all runners\", \"what is every runner on\": one clean list of every runner and its ticket, clustered by topic. Also the Runners section of /runner-update. Any fleet."
---

# /runner-list

Valentin's format (2026-11-05). Nothing else in the reply.

## Get the data
- Runner names and claims from your fleet's own source. Multiprompt: `~/.local/state/multibot/owners.json`, panes `multibot-runner-<x>`.
- Ticket title: the live Hypertask title, `hypertask task get <ID> --json`. Never paraphrase it.
- Check each pane first (`tmux capture-pane -p -t <pane> | tail -3`). The claim file can be stale.

## Format
- Cluster by topic. Bold headline per cluster, 1 to 3 words.
- Most urgent cluster first: freezes and crashes on top.
- One bullet per runner: `<Runner board name>: [<TICKET-ID> <exact ticket title>](<full ticket URL>)`.
- The title is the link text. One link per bullet.
- Idle or stuck runner: append ` (idle: <reason>)`.
- No intro, no outro, no counts, no extra notes.

## Example
**Freezes**
- Multi Bot Runner C: [IGSH-1170 Multiprompt freezes and I have to close it to keep working](https://app.hypertask.ai/detail/project-2060/1170)

**Rooms**
- Multi Bot Runner I: [IGSH-1313 Multi Bot: chat with several agents together](https://app.hypertask.ai/detail/project-2060/1313)
