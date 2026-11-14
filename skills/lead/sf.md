# Fleet add-on: Software Factory (sf)

Lead: Mini Boss CEO, tmux session `projects`.

Repos: valentinyeo/multiprompt (public, hosted CI ok), valentinyeo/multiprompt-android,
valentinyeo/ceo (ops, private, no hosted CI), wazig.

Board: Hypertask 2060 (IGSH), https://app.hypertask.ai/project?id=2060 .
Board writes: `~/projects/ceo/bin/ceo-ht`. Plain `hypertask` read only.

Runners: Codex `hax-runner-1..N` via `~/projects/ceo/bin/hax-runner <n>`, limit is server load only.
Claude `ceo-runner-6..10`. Runners self-pull with `bin/pick-next`.

Focus: `~/projects/ceo/focus.txt` (Multiprompt performance). Infra blockers first.

Checks: `bin/master-health` (master green, last release), `bin/blocked-on-me` (parked on lead).
Releases reach his laptop only by in-app update. Laptop is read only.
