---
name: house-rules-update
description: Add or change a house rule in valentinyeo/house-rules. Use on "/house-rules-update [rule]", "add this to house rules", or when Valentin gives a standing rule for every agent. No argument = capture every standing rule Valentin gave in this conversation.
---

# /house-rules-update [rule]

Any manager or session may contribute. One PR per batch, same day.

## 1. Collect
- With an argument: that rule.
- No argument: scan this conversation for every standing rule Valentin gave (always/never/from now on/HARD). Skip one-off asks and project-only rules (those go in the project's own repo).

## 2. Write each rule
- One line, imperative, caveman: max 8 words per sentence.
- End with `(YYYY-MM-DD, why: <8 words max>)`; quote Valentin if short.
- Put it under the right existing section. New section only if none fits.
- Already covered? Edit that line instead. Never add a duplicate. Contradicts a line? Replace it; newest wins.
- Keep the file lean. Long procedures become a skill in `skills/<name>/SKILL.md`, with one pointer line in the file.

## 3. PR
```
cd ~/.local/share/house-rules && git checkout main && git pull --ff-only -q
git checkout -b rule/<short-what>
# edit house-rules.md (and skills/ if needed)
git commit -am "rule: <what>" && git push -u origin HEAD
gh pr create --repo valentinyeo/house-rules --title "rule: <what>" --body "<Valentin's words + where he said it>"
```
- Small PR. Self-check: one line per rule, dated, no duplicate, no secrets, voice rules met.

## 4. Merge or ask
- Only restates what Valentin said: `gh pr merge --squash --delete-branch`.
- New idea, or contradicts Valentin: do not merge. Ask Valentin through your own lead, with your recommendation.

## 5. After merge
- `git checkout main && git pull -q && ~/.local/bin/house-rules-sync`
- Check: `grep -c "<new rule words>" ~/.codex/AGENTS.md ~/.config/hax/AGENTS.md`
- Tell the other managers in one line: `house-rules updated: <rule>. Run /house-rules.`
