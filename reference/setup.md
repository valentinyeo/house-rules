# New session setup

Read when you start a new session, set up a harness or install pstack or caveman.

1. Run `/house-rules`.
2. Install or verify pstack from its official source only: https://github.com/cursor/plugins/tree/main/pstack. Claude Code: `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`. Never copy pstack content.
3. Install or verify caveman from its official marketplace only (Claude Code): `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`. Never hand-copy caveman skills. Codex and hax follow the caveman rules in `house-rules.md`.
4. Find your project. Hypertask: work in `~/projects/hypertask`. Run `/setup-runner` as a runner, `/setup-agents` as a lead or for a new project. Department leads run `/board-identity` through its final startup check. Other projects: run that repo's own setup skill.
5. Take your role from the roster. Open `fleet/roster.json`, find your session name, load its `role_skill`. No row: note "not in roster" in Chief Of Staff's agent lane and take no work.
6. Log in to boards only through your setup skill. Never paste tokens. Keys come from `~/.local/bin/stack-key` on hypertask-vps and are never printed.
7. Model rules apply: fast mode off.
8. Report blockers to your own project's lead.
9. Confirm in one line: who you are, your project, "setup ok" (or what failed).
