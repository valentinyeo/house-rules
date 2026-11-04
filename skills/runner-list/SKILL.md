---
name: runner-list
description: "/runner-list, \"list all runners\", \"what is every runner on\": one clean list of every runner and its ticket, clustered by topic. Also the Runners section of /runner-update. Any fleet."
---

# /runner-list

Valentin's format (2026-11-05). Every runner names its model and effort level. Nothing else in the reply.

## Get the data
- Runner names and claims from your fleet's own source. Multiprompt: `~/.local/state/multibot/owners.json`, panes `multibot-runner-<x>`.
- Model and effort: read the live process, never the plan. `ps -o args= -p <pane_pid>` plus `--ppid <pane_pid>`; take `--model` and `--effort`. Claude panes: the model line in the pane footer.
- Token ladder proof: count helper runs per runner since shift start (Terra = code, Luna = lookups). Multiprompt: `mb-ladder <hours>`. Other fleets: hax sessions in `~/.local/state/hax/sessions`, matched by the runner's worktree.
- Ticket title: the live Hypertask title, `hypertask task get <ID> --json`. Never paraphrase it.
- Check each pane first (`tmux capture-pane -p -t <pane> | tail -3`). The claim file can be stale.

## Format
- Cluster by topic. Bold headline per cluster, 1 to 3 words.
- Most urgent cluster first: freezes and crashes on top.
- One bullet per runner: `<Runner board name> (<model> <effort>, terra <N>, luna <N>)`.
- Terra 0 on a runner that wrote code? Flag it ` (ladder: no terra)` and tell that runner to delegate.
- The ticket goes on the next line of the same bullet: a plain line break, indented two spaces, no bullet: `  [<TICKET-ID> <exact ticket title>](<full ticket URL>)`. Never a nested bullet.
- The title is the link text. One link per bullet.
- Idle or stuck runner: append ` (idle: <reason>)` to the runner line.
- No intro, no outro, no counts, no extra notes.

## Example
**Freezes**
- Multi Bot Runner C (gpt-6.1-sol medium, terra 1, luna 1)
  [IGSH-1170 Multiprompt freezes and I have to close it to keep working](https://app.hypertask.ai/detail/project-2060/1170)

**Rooms**
- Multi Bot Runner I (gpt-6.1-sol medium, terra 3, luna 1)
  [IGSH-1313 Multi Bot: chat with several agents together](https://app.hypertask.ai/detail/project-2060/1313)
