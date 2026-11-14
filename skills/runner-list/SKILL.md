---
name: runner-list
description: "/runner-list, \"list all runners\", \"what is every runner on\": one clean list of every runner and its ticket, clustered by topic. Also the Runners section of /runner-update. Use when asked to list runners. Any fleet."
---

# /runner-list

Valentin's format. Every runner names the model and effort it runs right now. Nothing else in the reply.

## Get the data
- Runner names and claims from your fleet's own source. Multiprompt: `~/.local/state/multibot/owners.json`, panes `multibot-runner-<x>`.
- Model and effort: read the live process, never the plan. `ps -o args= -p <pane_pid>` plus `--ppid <pane_pid>`; take `--model` and `--effort`. Claude panes: the model line in the pane footer.
- Idle runner (no hax process): take the model from the launcher's last `pick:` log line and add the idle flag.
- Ticket title: the live Hypertask title, `hypertask task get <ID> --json`. Never paraphrase it.
- Check each pane first (`tmux capture-pane -p -t <pane> | tail -3`). The claim file can be stale.

## Format
No bullets. Each runner is a two-line block. Blank line between blocks.
- Cluster by topic. Bold headline per cluster, 1 to 3 words, on its own line.
- Most urgent cluster first: freezes and crashes on top.
- Line 1: `Runner <letter> · <Model> <effort>`. Short names: Sol, Terra, Luna.
- Line 2, plain line break, no indent: `[<TICKET-ID> <exact ticket title>](<full ticket URL>)`.
- Flags go at the end of line 1, after ` · `: `idle: <reason>` when idle.
- No intro, no outro, no counts, no extra notes.

## Example
**Freezes**

Runner C · Sol medium
[IGSH-1170 Multiprompt freezes and I have to close it to keep working](https://app.hypertask.ai/detail/project-2060/1170)

Runner G · Terra medium · idle: CI blocks it
[IGSH-1685 App freezes after Alt+Tab while picking a bot picture](https://app.hypertask.ai/detail/project-2060/1685)
