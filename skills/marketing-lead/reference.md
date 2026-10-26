# Marketing lead reference

## The bar

| Person | X | Source of truth |
|---|---|---|
| Corey Haines | @coreyhainesco (user id 2480319486) | https://github.com/coreyhaines31/marketingskills (installed on hypertask-vps as Claude plugin `marketing-skills@marketingskills`) |
| Tim Scheuer | @timscheuer (user id 1683415774877155328) | https://github.com/timscheuerai/grokbot-gtm-team and https://github.com/timscheuerai/gtm-architecture-template |

Corey = skills (what to do, per marketing task). Tim = architecture (how a GTM team of agents is split). Use Corey's skill files when teaching a task (cro, copy-editing, seo-audit, launch, social, video and others). Use Tim's roster and template when auditing how Valentin's bots and sessions are split.

## Valentin's surfaces

- valentinyeo.com: CRO consulting. Funnel "CRO consulting".
- hypertask.ai: SaaS (repo hypertask-ai/astro, owned by HT Growth Lead). Funnel "Hypertask".
- github.com/valentinyeo: claude-cro and others.
- x.com/valentinyeo (user id 52731907): build in public. Human-only.
- Hypertask Marketing board: project 2108 (MARK). HT Growth Lead replies there.

## Schedules (London time)

| Job | When | Output |
|---|---|---|
| X and repo watch, Corey + Tim | daily 18:15 | 0 to 3 flags, or nothing |
| Post sparks | daily 17:30 | max 5 ideas, or nothing |
| Setup audit | Sundays 10:30 | top 5 changes |

A Claude Code session has no clock. Run these when Valentin asks, or when a timer he approves types the prompt into the session. Nothing after 23:00.

## Watch

- Read new posts since the last seen id (`since_id`) per person. Read new commits on their three repos.
- Last known cursors from the Grok Bot run (may be stale, re-check): Corey 2114394072492519489 (flagged 2026-10-25), Tim 2114012005782667728 (2026-10-24).
- Keep cursors in a small state file on the VPS, for example `~/.local/state/marketing-lead/x-cursors.json`.
- Flag format: link, one line on what it is, one line on why it matters to Valentin, next action with minutes.
- X API access on the VPS: none found in `stack-key --list` (2026-10-26). Until Valentin adds a read-only X credential, watch repos only and say so once.

## Post sparks

Ideas only. Never post text.

1. Gather the last ~24h:
   - GitHub: his opened and merged PRs (author valentinyeo, plus hypertask-ai org). Counts and notable links.
   - Hypertask: tickets moved to Done on his boards (read only).
   - VPS: session and runner reports, handoffs, ship stats. Decisions, surprises, numbers, failures, agents correcting themselves.
2. Skip private things: email content, keys, secrets, customer names unless public. If sensitive but post-worthy, mark "keep off X".
3. Skip ideas already sent unless there is news.
4. Output: next action first ("write #1 yourself, 15 min"). Then max 5 numbered ideas: one line idea, one line evidence (link, ticket, number), funnel (Hypertask, CRO consulting, or both). Then one line: your pick and why. Posts with real numbers did best so far.
5. Nothing post-worthy: send nothing.

## Audit

- Read-only. Look at his marketing and sales sessions, bots, skills and boards.
- Compare to Tim's roster and template and Corey's skills.
- Top 5, deletions and merges first. Each: what you saw, source link, effort in minutes.
- Track open findings until done or dropped. Carry them week to week.

## Verification
- Advice: every claim has a source link (post, repo file). Inference is labeled.
- Shipped hypertask.ai change: live URL screenshot at phone and desktop width. Before and after conversion or visit numbers from PostHog, same weekday window.
- Caveat: PostHog visits alert MARK-164 fires daily since 19 Oct, and YPER4-376 says tracking may not reach PostHog. Until fixed, metric claims need a second source (server logs or Vercel analytics).

## Runners, board and GitHub (from HT Product Lead, 2026-10-26)
- Each lead keeps its own board: Product HTPR 15, Infra YPER4 4060, Support HEFE 10450, Growth MARK 2108, Finance YPER1 2462. Design has no board; its work stays on HTPR 15 under the Design label. Never move tickets to another board.
- Runners pull 15, 4060, 10450 and 2108 (https://app.hypertask.ai/detail/project-4060/810). Never the finance board. Until that ships, HT Product Lead assigns a runner.
- Every ticket gets a reused Title Case label.
- Runner blockers on your tickets come to HT Product Lead. Never message runners mid-ticket except to answer them.
- hypertask-ai/hypertask has no automerge. The runner merges after required checks pass, deploys and proves it live. You check the ticket once later.
- GitHub quota is shared and scarce. Never poll gh or Actions. At most one gh read per check-in.
- Board writes only through vcc as your own agent identity. Never Valentin's token.
- After 23:00 London you start no new loops. Runners keep running.
