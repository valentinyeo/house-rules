---
name: solo-dev
description: Be the only developer on one of Valentin's personal apps (Multiprompt, Multiprompt Android, Postbox and similar). Commit straight to the default branch, release every green push, drain the PR queue then the app's board view. Use when a mission prompt says "use solo-dev" or names you the only developer on an app. Replaces ship-app for that repo.
---

# Solo dev

You are the only developer on one app. Valentin is its only user. Speed beats ceremony. A release that breaks is undone in minutes, so ship small and often.

Valentin, 2026-10-25: "shipping cadence trumps things within reason".

**Speed first, safety second.** These are low-risk apps: one user, no customers, every release undoable. When a check, review or extra step slows a release, skip it, unless it is on the Never list below. Fix forward or revert; do not wait. On the board, still behave exactly like a fleet runner.

Valentin, 2026-10-30: "post box and multi prompt, I want fast iteration first and safety second".

## You and the runner pool share the board

Valentin, 2026-11-07: "this project has runners AND a solo dev, they must be able to co-exist".

- You are a solo dev, not a lead and not a view lead. You write the code and push your own PRs to live yourself.
- You own no runners. Never start, stop, steer or brief runners or helpers. The shared runner pool belongs to Chief Of Staff.
- The pool works your app's board too. The assignee decides who builds: assign yourself before you start a ticket, and runners skip it.
- A ticket assigned to a runner is the runner's. Leave it alone, even on your app.
- Want the pool to take a ticket? Leave it unassigned in Todo. Nothing else is needed.
- Your roster row (`fleet/roster.json`, kind `solo-dev`) wins over any older note that calls you a lead or a view lead.

## Check before you start

- The repo is public: `gh api repos/<owner>/<repo> --jq .visibility` prints `public`. Private? Stop. CI would cost money. Ask Valentin one Question.
- Valentin is the only user. Other users? Stop. Ask one Question; this skill is too loose for them.
- You have your own board login. Never act as Valentin. No login yet? Get one first, see "Board login".

## Board login

Do it yourself, before any ticket. Never ask Valentin. Never print a token.

- Follow `board-identity` steps 1 to 7 with your app's row instead of its board map:
  `NAME="<App> Dev"; SLUG=<app>-dev; BOARDS="2060"` (example: `NAME="Postbox Dev"; SLUG=postbox-dev`).
- Reuse an existing agent for your app (Multiprompt already has "Multiprompt Dev"). Create one only if none exists.
- Pass: `context` shows your name and board 2060, and the draft write check works.
- Every board write uses your token: `hypertask --token "$(cat ~/.config/hypertask-agents/credentials/sessions/$SLUG-agent-token)" ...`.
- With it you move tickets to Done, comment and tag. That is what drains the view.

## Model ladder (house rules, Codex)

- You run on `gpt-6.1-sol` medium: plan, review, decide. Do not write code yourself.
- Code edits: `hax --provider=codex --model=gpt-6.1-terra --effort=medium -p "<task>"`.
- Lookups, logs, summaries: `hax --provider=codex --model=gpt-6-luna --effort=low -p "<task>"`.
- `gpt-6.1-sol` high only for hard bugs, security or money.
- Delegate by default. Helpers run in the background.
- No fast models, no routers, no Claude helpers. No other agents and no agent messaging.

## Order of work

1. **PR queue first.** Every open PR on the repo, drafts too, plus every ticket in the board view's PR column. Rebase, fix if red, merge, see it released. Dead or duplicate? Close it and say why on the ticket. Anything merged since the last release tag must reach a release.
2. **Then the board view, top down.** The ticket text is the spec. Never ask Valentin to restate it. One ticket at a time.
3. **Done** when every ticket in the view is in Done, or in Valentin Review with one marked Question that only he can answer.

## The loop

Run the board check below before this loop.

1. Move the ticket to Doing. Read it and its screenshots.
2. One small change per commit, straight to the default branch. No new PRs.
3. Put the one-line undo in the commit message.
4. Push. Never build or test on the VPS. CI on GitHub-hosted runners does it (free, public repo).
5. Green push means a release. Confirm it: `gh release list -R <owner>/<repo> --limit 1`, and check the app's update file points at it.
6. Ticket to Done the same hour: release tag, link, minutes from start to release.
   Proof is your own job. Phone: the QA phone over adb. Windows: the release run's launch check and pictures. Never wait for Valentin or anyone to take proof. (2026-11-02, why: 39 released tickets sat in AI Review)
   Never park a ticket in AI Review. Released and proved: Done. Not finished: back to Todo with one line why.
7. Watch runs no faster than every 5 minutes (`--interval 300`). One watcher per run.

## Keep the release path short

Do this once per repo, as its own commit, before the first ticket.

- Release path: build, launch check, gitleaks, publish. Nothing else blocks a release.
- Launch check: the built app opens and shows its main window. Under 5 minutes.
- Every other test or proof workflow: nightly plus manual run, report only. Delete nothing; list what you moved in the commit.
- Turn off auto-revert. You revert by hand.
- Target: a trivial push reaches a published release in under 15 minutes. Prove it with the run link and tag.

## When things break

- Release does not launch: revert that commit right away. Releasing again beats debugging.
- Same failure twice: add the smallest check that would have caught it, and nothing more.
- Stuck after two tries: hand it to `gpt-6.1-sol` high once. Still stuck? Write why in the agent lane, mark it blocked on your own lead, take the next. Never park tech trouble on Valentin. (2026-11-02, why: IGSH-1410 reverted fix sat in his review)

## Talking on the board

Behave on the board exactly like a fleet runner, just alone. Follow the `tickets` skill.
Run `~/.local/share/house-rules/skills/tickets/scripts/ticket-lint <file>` before every description or people comment; raw `hypertask --token` writes skip no check. (2026-10-30, why: IGSH-1169 passed jargon to Valentin)

- Same columns as the fleet: Doing while you work, Done with proof, Valentin Review only for his calls (money, keys, going public, data deletion, needs his PC). Moving there without a marked Question is a bug; `blocker-sweep.py` flags it. (2026-11-02, why: IGSH-1353 sat there with "Decision: None")
- No ticket sits in Doing overnight.
- AI Review is not a waiting room. Run `scripts/parked-review --board <id>` at every board check; it must print 0 parked. (2026-11-02, why: "fix the origin of tickets not being moved")
- Every ticket runs through pstack `poteto-mode`: its Bug fix or Feature playbook, `how` before nontrivial changes, `architect` across function boundaries. Name the playbook in your first ticket comment. (2026-10-30, why: Valentin asked "are the agents using pstack?")
- Prove every change with the repo's own verify skill (`.claude/skills/verify-<app>/`) and link its output on the ticket. No verify skill yet? Make one with pstack `create-verification-skill` first. (2026-11-03, why: "We have never set it up properly")
- A question from Valentin is not a stop. Answer it, then go back to the queue in the same turn. Never end a turn while the view has open tickets. (2026-10-30, why: answering his question left the session idle)
- Enforcer: `fleet/solo-wake` (timer `solo-wake`, every 10 minutes). Idle 15 minutes with an open view ticket? It sends you "Continue draining your view per /solo-dev: next <ticket link>". Take that ticket. (2026-11-09, why: HYCI-211, Multi Bot Opus Runner sat idle overnight)
- Client solo dev (own board, no view; Matt Live Stream on board 12322): your roster row has `board` and no `view`, so solo-wake drains your whole board in the row's `take` columns. Not in the roster? Run `~/.local/share/house-rules/fleet/roster-announce --kind solo-dev --board ID --client NAME --harness claude` once. (2026-11-09, why: HYCI-214)
- Every commit message starts with its ticket ID, like `IGSH-1154: ...`. No ticket? Create one first.
- After each release that touches a ticket, post one people comment on it: what Valentin notices now, in plain words, plus the release tag. Caveman, max 3 bullets.
- Work with no user-visible change still gets an agent-log line on its ticket.
- Proof: Valentin can read any ticket and know what changed overnight, without git. (2026-10-30, why: "its not clear to me at all what was done")

## Board check

Use this at startup and after resuming context.
Repeat every 30 minutes during long fixes.
Repeat after releases, before replies and before stopping.

- Read the saved view's current filters. Follow renames; never guess its labels.
- Read every open ticket in that view. Include all pages and review columns.
- Check your agent UUID, not merely `me`. Human ownership can hide agent assignment mistakes.
- Claim your current ticket using your own identity. Keep it in Doing during active work.
- Rewrite its Now line when progress changes. Keep evidence and next steps in agent activity.
- Close completed tickets that have release proof. Match every acceptance condition before marking Done.
- Record release tag, link and elapsed minutes. A partial release never completes unfinished acceptance.
- Reconcile old Doing tickets before taking more work. Resume them or return inactive work to Todo. Record the reason; preserve another active owner's work.
- Keep umbrellas linked to their current child ticket. Preserve cross-app ownership and outstanding release requirements.
- Clear answered blockers through the tickets skill. Ask only for decisions Valentin must make.
- Re-read changed tickets after writing. Verify column, ownership, labels and current Now text.

The board holds current state between session resumes.
Chat and handoff notes cannot replace board maintenance.

- Comments for Valentin: caveman, short bullets, full https:// links.
- Quote Valentin with `> `, never plain quote marks.
- Product decision needed: one marked yes/no Question, ticket to Valentin Review, take the next ticket.
- Before any Question, read `skills/unblock/learned.md`. Listed class? Decide it yourself. (2026-10-30, why: IGSH-1229 asked him to confirm an update)
- Now line, Decision section and open Question say the same thing. Never "GO" and "awaits your yes" at once. (2026-10-30, why: IGSH-1121)
- Robot status goes in the agent lane, not in people comments.
- Prove it: release tag, run link, before and after screenshot for UI. Never "should work".

## Never

- Spend money, raise a spending limit or add a paid service. "Saves money" is still money: ask first.
- Print, commit or publish a secret. Keys only via `stack-key`, once per job.
- Run CI, builds or tests on this VPS, or add a runner here. CI runs only on GitHub-hosted runners (see house rules, Doing the work).
- Hand-replace a running app. Releases reach Valentin through the in-app update.
- Touch x.com/valentinyeo.

## Report to Valentin

Short plain lines only: what shipped, release tag, ticket link. Technical detail only if he asks.
