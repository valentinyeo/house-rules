---
name: house-rules-update
description: Add or change a house rule in valentinyeo/house-rules. Use on "/house-rules-update [rule]", "add this to house rules", or when Valentin gives a standing rule for every agent. No argument means capture every standing rule from this conversation.
---

# /house-rules-update [correction]

Run `/pstack:correct` on the correction, in a clone of valentinyeo/house-rules. Fix it at the highest level that works: delete or change a script or check first. Add a line to house-rules.md last, only for a judgment call.

A new line is `- **Label:** imperative sentence.` under the right section, with a row in the Enforcement table. No reasons, dates or quotes; the PR body keeps those. `rules-lint` fails anything else.

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

Get a pstack verifier verdict on the PR from another model family, then `gh pr merge --squash --delete-branch` once `rules-lint` is green. A change Valentin did not ask for: do not merge; ask him with your pick.

## After merge

- Run `~/.local/bin/house-rules-sync`.
- Tell the other managers in one line: `house-rules updated: <rule>. Run /house-rules.`
