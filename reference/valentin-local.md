# Valentin mode on this machine

The public skill is vstack `skills/valentin-mode`. It says: Machine-specific setup: see your private reference if present. This file is that reference. It stays in the private repo.

## Screenshots

Upload with `sc2-upload` and give its https://screencast2.com URL, the only image link Multibot unfurls. Never a path or another image host. The `shots-guard` Stop hook blocks the reply otherwise.

## Questions

A question for the user is the first line and overrides `/i-have-adhd` rule 4. The `ask-first-guard` Stop hook blocks the reply otherwise.

## Workers

Before each worker, run `token-ladder pools --json`. Once `spawn-worker` exists, start every worker with it instead. It reads usage and refuses a plan that is out.

- Grok: `cursor-agent -p -f --model grok-4.7 "$(cat brief.txt)"`
- DeepSeek: `pi -p --provider opencode-go --model deepseek-v4.1-flash --thinking medium "$(cat brief.txt)"`. Never the OpenCode app. The `deepseek-via-pi` hook blocks it.
- Codex: `hax -p --provider=codex --model=gpt-6.1-sol --effort=medium "$(cat brief.txt)"`

Put each brief in a file and pass it with `"$(cat file)"`. The secrets guard blocks some inline prompts. Open each brief with the user's goal.

## Rules

Also follow `/house-rules`. Change those rules only through `/house-rules-update`.

## Hook

The session-start hook `~/.claude/hooks/valentin-mode-load.py` reads `~/.local/share/vstack/skills/valentin-mode/SKILL.md` and, when this file exists, appends it. That hook file lives on this machine. It is not in the public repo.
