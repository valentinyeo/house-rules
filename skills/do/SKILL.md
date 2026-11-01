---
name: do
description: "/do [task]: get it done, guaranteed, visibly on the Hypertask board. House rules first, one ticket per work step, each moved In Progress to review to Done. Stacks pstack poteto-mode and unlazy: poteto plans, unlazy locks the plan into gates, poteto-agents execute, unlazy reverifies. Use for any real task that must not come back half done."
---

# /do

The task is the text after `/do`. With none, use the latest task in this conversation.

Order is a sandwich: **poteto plans, unlazy gates, poteto executes, unlazy proves.** Gates written before the plan test the wrong thing. A plan with no gates comes back half done.

The board is the record, not your own notes. Valentin watches the board. Work he cannot see on it did not happen.

Valentin, 2026-11-01:

> the idea is that do tells the agent that it must also use house rules and create tickets for its wor5ksptesp and then move them visiubly throught board until they are shippped

## 0. House rules and board identity

- Run `/house-rules` (or read `~/.local/share/house-rules/house-rules.md` in full). House rules win over this skill.
- Use your own board identity: `ship-identity`, `vcc`, or your fleet's agent login. Never Valentin's token. No login yet? Run `/board-identity` or your setup skill first.
- Read `skills/tickets/` before any ticket write.

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

Output: the plan, split into deliverables. Each deliverable has one observable outcome, the files it owns and what it needs first. Every work step the user named is its own deliverable or is folded into one by name.

## 2. One ticket per deliverable

Before any work starts:

- The task already is a ticket? Use it. Add one child or linked ticket per further deliverable.
- Otherwise file one ticket per deliverable with the `hypertask` skill. It picks the board, checks duplicates and tags the label.
- Board by project: Hypertask app on board 15, agents and infra on 4060, Hypertask CI on 11514, Software Factory apps on 2060. Other projects use their own board.
- Each ticket: pospeak description, the user's words quoted with `> `, and the gate ids that prove it.
- Post the ticket links in one `Plan:` activity on the first ticket.

## 3. Lock the plan into an unlazy ledger

Follow unlazy as written. Pick its mode from the plan:

- One deliverable, one session: solo `GATES.md`.
- Several deliverables: orchestrated, `.unlazy/<scope>/PLAN.md` plus one gates file per leaf and branch.

Rules on top of unlazy:

- One leaf per ticket. Name gates `<TICKET>:G<n>`, so each gate maps to its ticket.
- One gate per plan outcome and per constraint the user gave. Reread the request and check none is missing.
- Every playbook "done" step becomes a gate: Prove It Works, tests pass, PR open, live proof.
- Every ticket gets a board gate: it sits in Done, with a done comment carrying the evidence link.
- Prefer runnable gates. Manual only when no command can decide.
- Run `gate-lint.mjs`. Fix every error. Approve only checks you wrote or read.

No work starts before the ledger lints clean.

## 4. Execute, ticket by ticket, on the board

Route each ticket to the project's shipping skill. It owns claim, PR, merge, deploy and Done:

- Hypertask app repo: `/ship` on that ticket. Its own `ship-gates` ledger joins this one.
- Valentin's personal apps: `/ship-app`, or `solo-dev` where that is the app's mode.
- Anything else: claim, work, PR or change, proof, Done, by the same board moves.

Board moves are live, per house rules:

- Start a ticket: move it to In Progress and add a `Start:` activity.
- PR open or waiting on a reviewer: the review column.
- Shipped and proved: Done, with a done comment in caveman with the evidence link.
- Blocked: blocked state plus the reason. Only Valentin's calls get a marked Question.

Status talk goes to the agent lane (`vcc activity add` or your fleet's log). People comments only when a human must read or decide.

Delegation:

- Do a leaf yourself, or give it to a fresh helper. Claude Code: `pstack:poteto-agent`. Codex and hax: the house-rules Codex ladder helper.
- Every brief contains: the user's goal, the ticket link, the absolute path of poteto-mode's SKILL.md with "read it in full and follow it", the playbook to run, the leaf gates file, its `OWNS:` paths, and "not done until every gate in your ledger is met".
- Add the house-rules lines every helper prompt needs: token-ladder mode and unlazy.
- Helpers never write to boards. You move the tickets.
- Dispatch only leaves whose needs are met. Follow unlazy's wave and lease rules for parallel leaves.

## 5. Prove with unlazy

- Rerun each returned leaf with `--reverify`. A leaf's own "done" counts for nothing.
- Run branch gates: interfaces fit, end-to-end works, nothing regressed.
- A failing gate goes back to a fresh helper with the consolidated brief. Same premise fails twice: apply Attack the Premise.
- Impossible gate: `ABANDON:` with a reason, and the ticket stays open with that reason. Never delete a gate.

## 6. Report

Run unlazy's final audit, then write the reply per poteto-mode's Writing the reply, in the house-rules chat voice:

- Goal first.
- One line per ticket: full https:// link, column, evidence link.
- Measured counts: gates met, unmet, abandoned. Every abandonment named.
- Principles that changed a decision.

Never report done while a gate is unmet, abandoned or waiting on an owner decision, or while any ticket of this task is not in Done.
