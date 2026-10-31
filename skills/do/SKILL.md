---
name: do
description: "/do [task]: get it done, guaranteed. Stacks pstack poteto-mode and unlazy: poteto plans, unlazy locks the plan into gates, poteto-agents execute, unlazy reverifies. Use for any real task that must not come back half done."
---

# /do

The task is the text after `/do`. With none, use the latest task in this conversation.

Order is a sandwich: **poteto plans, unlazy gates, poteto executes, unlazy proves.** Gates written before the plan test the wrong thing. A plan with no gates comes back half done.

## Find the two skills

- poteto-mode: `~/.agents/skills/poteto-mode/SKILL.md`. Claude Code fallback: newest `~/.claude/plugins/cache/cursor-plugins/pstack/*/skills/poteto-mode/SKILL.md`.
- unlazy: `~/.agents/skills/unlazy/SKILL.md`. Fallback: `~/.claude/skills/unlazy/SKILL.md`.

Read both in full before step 1. Missing one: stop and say which.

## 1. Plan with poteto-mode

Follow poteto-mode's Non-negotiables, Playbooks and Principles as written. In particular:

- Restate the goal, the problem and the smallest change that meets it.
- Match one playbook. Large or cross-cutting work goes to figure-it-out. Copy its steps verbatim into the todolist.
- Nontrivial or "are we sure": run the **how** skill. Code: name the data shape first. Code crossing a function boundary: **architect**. Contested design: **interrogate**.
- Settle observable forks by prototyping, not by asking.

Output: the plan, split into deliverables. Each deliverable has one observable outcome, the files it owns and what it needs first.

## 2. Lock the plan into an unlazy ledger

Follow unlazy as written. Pick its mode from the plan:

- One deliverable, one session: solo `GATES.md`.
- Several deliverables: orchestrated, `.unlazy/<scope>/PLAN.md` plus one gates file per leaf and branch.

Rules on top of unlazy:

- One gate per plan outcome and per constraint the user gave. Reread the request and check none is missing.
- Every playbook "done" step becomes a gate: Prove It Works, tests pass, PR open, live proof.
- Prefer runnable gates. Manual only when no command can decide.
- Run `gate-lint.mjs`. Fix every error. Approve only checks you wrote or read.

No work starts before the ledger lints clean.

## 3. Execute with poteto-mode

- Do a leaf yourself, or give it to a fresh `poteto-agent` subagent (Claude Code: `pstack:poteto-agent`).
- Every brief contains: the user's goal, the absolute path of poteto-mode's SKILL.md with "read it in full and follow it", the playbook to run, the leaf gates file, its `OWNS:` paths, and "not done until every gate in your ledger is met".
- Add the house-rules lines every helper prompt needs: token-ladder mode and unlazy.
- Dispatch only leaves whose needs are met. Follow unlazy's wave and lease rules for parallel leaves.

## 4. Prove with unlazy

- Rerun each returned leaf with `--reverify`. A leaf's own "done" counts for nothing.
- Run branch gates: interfaces fit, end-to-end works, nothing regressed.
- A failing gate goes back to a fresh poteto-agent with the consolidated brief. Same premise fails twice: apply Attack the Premise.
- Impossible gate: `ABANDON:` with a reason. Never delete it.

## 5. Report

Run unlazy's final audit, then write the reply per poteto-mode's Writing the reply:

- Goal first.
- Measured counts: gates met, unmet, abandoned. Every abandonment named.
- Evidence links: PR, live URL, demo.
- Principles that changed a decision.

Never report done while a gate is unmet, abandoned or waiting on an owner decision.
