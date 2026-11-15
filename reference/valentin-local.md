# Valentin mode on this machine

The public skill is vstack `skills/valentin-mode`. It tells the agent to read this file when it is present. These lines came out of that skill because they name hooks on this server.

- Screenshots still go to screencast2. The `shots-guard` Stop hook blocks the reply otherwise.
- A question for the user is the first line and overrides `/i-have-adhd` rule 4. The `ask-first-guard` Stop hook blocks the reply otherwise.
- Never the OpenCode app. The `deepseek-via-pi` hook blocks it.
- Put each brief in a file. The secrets guard blocks some inline prompts.
- Also follow `/house-rules`. Change those rules only through `/house-rules-update`.
- The session-start hook `~/.claude/hooks/valentin-mode-load.py` reads `~/.local/share/vstack/skills/valentin-mode/SKILL.md` and loads it. That hook file lives on this machine. It is not in the public repo.
