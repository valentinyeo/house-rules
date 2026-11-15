---
name: house-rules
description: Load and apply Valentin's house rules in this session. Use on "/house-rules", "read the house rules", at session start, and when told house-rules changed.
---

# /house-rules

1. Pull latest: `git -C ~/.local/share/house-rules pull --ff-only -q` (off hypertask-vps: read https://github.com/valentinyeo/house-rules).
2. Read all of `~/.local/share/house-rules/house-rules.md`. It wins over any other rules file. Two lines disagree? The newer commit wins; tell your lead.
3. Apply it now, in this session.
4. Confirm in one caveman line: `house rules loaded, <short commit sha>, <what you changed now or "nothing to change">`.

Never edit the checkout by hand. Changes go through `/house-rules-update`.
