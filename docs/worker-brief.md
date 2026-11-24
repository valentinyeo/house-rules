# Worker brief rules

Faults: Hypertask bug -> hypertask feedback; repo rules or scripts -> the worker repo's board and view; only shared house rules or pstack setup -> board 2060, label Poteto.

Report faults before working around them.
No board login of your own? Never write on a board, and never borrow a personal login.
Put the fault and its route in your final message; the orchestrator files it.
For Hypertask faults, run this command:

```sh
hypertask feedback --kind bug|friction|missing --category <c> --tool "<command>" --status <http> --error-code <slug> "<note>"
```

Choose one kind and the matching category.
Use the observed status when available.
Omit status when no HTTP response exists.
Feedback files on board 15.
Never include task, board or comment content.
Report command metadata and a sanitized note.

Our rules, scripts or gates failed?
File on the worker repo's board and view.
Only shared house rules or pstack setup faults
go to board 2060 with label Poteto.
Keep working after recording the fault.
These reporting rules override legacy workaround instructions.

PR body: add one line `Author model: <family>/<model>` per author,
for example `Author model: deepseek/deepseek-v4.1-flash`,
`Author model: anthropic/claude-sonnet`, `Author model: openai/gpt-6.1-sol`.

Builds and test suites run on GitHub Actions.
Push and read the PR checks; a build or suite on the shared server is refused.

Owner steps: pstack `poteto-mode/playbooks/autopilot-full.md` step 2 owns the code-ready head.
Read the newest copy under `/home/valentin/.claude/plugins/cache/cursor-plugins/pstack/`.
Quoted:

> Each owner is a Cursor cloud agent that builds, opens its PR per `playbooks/opening-a-pr.md`, proves the change on the real artifact, babysits to green per `playbooks/babysit.md`, and merges once steps 4 and 5 clear it.

> The code is ready only after the slop-strip (the `deslop` skill from the `cursor-team-kit` plugin (`/deslop`)) and the `/no-comments` pass, so the full swarm runs on finished code. Then rebase onto current trunk and report the code-ready head before self-proof, so verification runs on the base the patch lands on.

In order: slop-strip, then the no-comments pass at `/home/valentin/.claude/plugins/cache/cursor-plugins/pstack/<version>/skills/no-comments/SKILL.md`,
then rebase onto current trunk and report the code-ready head, then self-proof on the real artifact.
The outside verifier runs after that.
`deslop` (cursor-team-kit) is not installed on these servers: until it is, apply the no-comments pass and report "deslop unavailable" in your final line.
