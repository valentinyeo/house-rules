---
name: do
description: "/do [task]: get it done, guaranteed, visibly on the project's tracker: Hypertask when the project has a board, else its own tracker, GitHub issues or a task list. Any project, any fleet. Rules first, one ticket per work step, each moved In Progress to review to Done. Stacks pstack poteto-mode and unlazy: poteto plans, unlazy locks the plan into gates, poteto-agents execute, unlazy reverifies. Use for any real task that must not come back half done."
---

# /do

The task is the text after `/do`. With none, use the latest task in this conversation.

Order is a sandwich: **poteto plans, unlazy gates, poteto executes, unlazy proves.** Gates written before the plan test the wrong thing. A plan with no gates comes back half done.

The tracker is the record, not your own notes. The owner watches it. Work they cannot see there did not happen.

Valentin, 2026-11-01:

> /do also needs to work for projects that don't have hypertask btw so it needs to be conditional but not so soft they auto ingore hpertask and it need to work also in channels that are not the sfotware factories

> the idea is that do tells the agent that it must also use house rules and create tickets for its wor5ksptesp and then move them visiubly throught board until they are shippped

## 0. Rules and tracker

Load every rules file that applies:

- Valentin's house rules, if `~/.local/share/house-rules/house-rules.md` exists. Run `/house-rules` or read it in full. House rules win over this skill.
- The project's own rules: `CLAUDE.md`, `AGENTS.md` or its docs. For inne, its own rules win on tickets and publishing.

Pick the tracker. Take the first that fits:

1. The project's rules name a tracker. Use it.
2. The task links a ticket. Use that tracker.
3. The project has a Hypertask board. Check the project's rules, `boards.md`, the `hypertask` skill's board map, or `hypertask projects` with your login. Use Hypertask.
4. The repo is on GitHub and you can write to it. Use its GitHub issues with one project label.
5. None of these. Use a numbered task list in your first message, mirrored in the unlazy PLAN. Show it again at each step.

Hypertask is the default whenever rule 3 finds a board. Skipping it needs a written reason in your first message: which checks you ran and what they returned. "Not needed" is not a reason.

Write to the tracker under your own identity: `ship-identity`, `vcc`, your fleet's agent login, or the project's bot account. Never Valentin's token. On Hypertask, read `skills/tickets/` before any write. No login yet? Run `/board-identity` or the project's setup skill first.

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

Before any work starts, in the tracker from step 0:

- The task already is a ticket? Use it. Add one child or linked ticket per further deliverable.
- Otherwise file one ticket per deliverable. On Hypertask, use the `hypertask` skill: it picks the board, checks duplicates and tags the label.
- Hypertask boards: app on 15, agents and infra on 4060, Hypertask CI on 11514, Software Factory apps on 2060. Other projects use their own board.
- Each ticket: plain words, the user's words quoted with `> `, and the gate ids that prove it.
- Post the ticket links in one `Plan:` note on the first ticket.
- Task-list fallback: each deliverable is one numbered line with its gate ids.

## 3. Lock the plan into an unlazy ledger

Follow unlazy as written. Pick its mode from the plan:

- One deliverable, one session: solo `GATES.md`.
- Several deliverables: orchestrated, `.unlazy/<scope>/PLAN.md` plus one gates file per leaf and branch.

Rules on top of unlazy:

- One leaf per ticket. Name gates `<TICKET>:G<n>`, so each gate maps to its ticket.
- One gate per plan outcome and per constraint the user gave. Reread the request and check none is missing.
- Every playbook "done" step becomes a gate: Prove It Works, tests pass, PR open, live proof.
- Every ticket gets a tracker gate: Done or closed, with a comment carrying the evidence link. Task-list fallback: the step's evidence link in the reply.
- Prefer runnable gates. Manual only when no command can decide.
- Run `gate-lint.mjs`. Fix every error. Approve only checks you wrote or read.

No work starts before the ledger lints clean.

## 4. Execute, ticket by ticket, visibly

Use the project's shipping skill when it has one. It owns claim, PR, merge, deploy and Done:

- Hypertask app repo: `/ship` on that ticket. Its own `ship-gates` ledger joins this one.
- Valentin's personal apps: `/ship-app`, or `solo-dev` where that is the app's mode.
- A shipping skill named in the project's rules: that skill.
- None: claim, work, PR or change, proof, close, by the moves below.

Move every ticket live as work changes:

- Start: In Progress, plus a `Start:` note.
- PR open or waiting on a reviewer: the review column, or a `review` label on GitHub.
- Shipped and proved: Done or closed, with a short comment carrying the evidence link.
- Blocked: blocked state plus the reason. Only the owner's own calls get a marked Question.

Status talk goes to the agent lane where the tracker has one (`vcc activity add` on Hypertask). People comments only when a human must read or decide.

Delegation:

- Do a leaf yourself, or give it to a fresh helper. Claude Code: `pstack:poteto-agent`. Codex and hax: the house-rules Codex ladder helper.
- Every brief contains: the user's goal, the ticket link, the absolute path of poteto-mode's SKILL.md with "read it in full and follow it", the playbook to run, the leaf gates file, its `OWNS:` paths, and "not done until every gate in your ledger is met".
- Add the house-rules lines every helper prompt needs: token-ladder mode and unlazy.
- Helpers never write to the tracker. You move the tickets.
- Dispatch only leaves whose needs are met. Follow unlazy's wave and lease rules for parallel leaves.

## 5. Prove with unlazy

- Rerun each returned leaf with `--reverify`. A leaf's own "done" counts for nothing.
- Run branch gates: interfaces fit, end-to-end works, nothing regressed.
- A failing gate goes back to a fresh helper with the consolidated brief. Same premise fails twice: apply Attack the Premise.
- Impossible gate: `ABANDON:` with a reason, and the ticket stays open with that reason. Never delete a gate.

## 6. Report

Run unlazy's final audit, then write the reply per poteto-mode's Writing the reply, in the house-rules chat voice:

- Goal first.
- One line per ticket: full https:// link, column, evidence link. Task-list fallback: one line per step with its evidence.
- Measured counts: gates met, unmet, abandoned. Every abandonment named.
- Principles that changed a decision.

Never report done while a gate is unmet, abandoned or waiting on an owner decision, or while any ticket of this task is not Done or closed.
