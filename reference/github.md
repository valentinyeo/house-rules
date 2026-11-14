# GitHub and CI

Read when you wait on a PR, watch a run, or run any build or test job.

- CI work on this VPS is forbidden. No GitHub runner, no local CI runner, no build or test job here. CI runs only on GitHub-hosted runners.
- Paid GitHub minutes on private repos are fine when activity is small. A repo using significant minutes: tell Valentin with numbers.
- Never poll GitHub faster than 5 minutes. `gh run watch` and `gh pr checks --watch` need `--interval 300` or more.
- One watcher per run or PR. Kill it within 30 minutes.
- Automation uses the runner App token, not Valentin's login.
- A CI problem that blocks an app ticket: `reference/boards.md`, CI snag.
