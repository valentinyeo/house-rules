---
name: house-rules
description: Load and apply Valentin's house rules in this session. Use on "/house-rules", "read the house rules", at session start, and when told house-rules changed.
---

# /house-rules

1. Pull latest: `git -C ~/.local/share/house-rules pull --ff-only -q` (off hypertask-vps: read https://github.com/valentinyeo/house-rules).
2. Read all of `~/.local/share/house-rules/house-rules.md`. It wins over any other rules file. Newest dated rule wins.
3. Apply it now, in this session: voice, models (fast mode off, no routers), who to message, what is Valentin's alone.
4. Do any "Start here" step you have not done yet (pstack, caveman plugin, setup skill).
5. Confirm in one caveman line: `house rules loaded, <newest rule date>, <what you changed now or "nothing to change">`.

Never edit the checkout by hand. Changes go through `/house-rules-update`.
