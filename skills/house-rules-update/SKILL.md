---
name: house-rules-update
description: Add or change a house rule in valentinyeo/house-rules. Use on "/house-rules-update [rule]", "add this to house rules", or when Valentin gives a standing rule for every agent. No argument means capture every standing rule from this conversation.
---

# /house-rules-update [rule]

## Write

- Write one imperative line. Short sentences. No reason, date, quote or history. The PR body and git keep those.
- Put the line under the section it belongs to. Already covered? Edit that line. Contradicts a line? Replace it.
- Rule for one role only? Put it in that role's skill, not in `house-rules.md`.
- Needs more than one line? Write `skills/<name>/SKILL.md` or `reference/<topic>.md`. Add one row to the "Read X when Y" table in `house-rules.md`.
- Something keeps breaking? Ship a script that refuses it in the same PR. Never add more prose.
- Keep `house-rules.md` under 1,500 words. Over? Cut or move first.
- Skip one-off asks and project-only rules. They belong in that project's repo.

## Ship

```
git clone -q git@github.com:valentinyeo/house-rules.git /tmp/hr-$$ && cd /tmp/hr-$$
git checkout -b rule/<short-what>
# edit house-rules.md, skills/, reference/
python3 scripts/rules-lint --diff origin/main
git commit -am "rule: <what> (<TICKET>)" && git push -u origin HEAD
gh pr create --repo valentinyeo/house-rules --title "rule: <what> (<TICKET>)" --body "<Valentin's words, where and when he said them>"
```

- Never edit `~/.local/share/house-rules` by hand.
- `rules-lint` is a required check. A red check blocks the merge and the fleet sync.

## Merge

- The PR only restates what Valentin said: `gh pr merge --squash --delete-branch` once the check is green.
- New idea, or it contradicts Valentin: do not merge. Ask Valentin through your own lead with your recommendation.

## After merge

- Run `~/.local/bin/house-rules-sync`.
- Tell the other managers in one line: `house-rules updated: <rule>. Run /house-rules.`
