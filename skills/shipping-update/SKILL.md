---
name: shipping-update
description: Shipping update for Valentin, any fleet. Verdict on pace first, then what went live, then CI, PRs and runners. Use for "/shipping-update", "update me", "update again", "how is CI", "draft PRs?", "are we shipping". Also the report shape for /runner-update and /overnight-update.
---

# /shipping-update

Read only. Gather, then answer in the shape below. Valentin, 2026-10-29: "i like this update a lot".

## Gather
1. Pace: `~/.local/share/house-rules/skills/shipping-update/scripts/pace <owner/repo> [base] [days]`. Base defaults to the repo default branch. Counts merged PRs plus direct pushes (solo-dev). Today vs the same clock time on the last 3 days, last 1/3/6/24h, best hours, changes of the last 3h.
2. Live: production CI on the base branch passed after those merges. Name the time it passed.
3. Open PRs: red, green, pending; drafts. Compare with your last update ("down from X").
4. CI queue: queued and running runs. Production checks state.
5. Only what is running: runners, trials (spend vs cap via its key), stuck items. Look at panes and logs; don't guess.

## Shape
```
**<Verdict: on track or not to beat changes/day of the last 3 days.>**

**Highlights shipped in the last 3 hours** (all live; production checks passed at HH:MM your time)
- <what users notice, plain words>: <full ticket link>
- <infra only when it unblocks something he asked for; say what it unblocks>

**Pace**
- N changes shipped so far today (merged PRs plus solo-dev direct pushes). By this hour on previous days:
  - <day>: N, finished at M
- Last 3h rate vs today's average.
- Projection for today vs the best day.
- Best single hour, and whether we are near it.
- Time to live: ticket created to Done, average over tickets closed in the window.
- CI slowing us or not: queue, production checks.

**CI**
- red of open, trend.

**Draft PRs**
- count, trend.

**<Running fleet or trial>**
- done count, spend vs cap, quality signal (merges undone, closed unmerged).
```

## Rules
- Solo-dev repos push straight to main. Count their pushes; a PR-only count reads 0 there.
- Answer first. One fact per bullet. Numbers always with a comparison.
- Highlights: max 7, user-facing first. Every item a full https ticket link.
- Problems are bullets starting "Not good:". No separate problem block.
- Times in Valentin's time zone. No bare PR or ticket ids.
- Drop a section he did not ask about and that has no news.
- Never invent a number. A projection says "at that pace". A failed source is named.
