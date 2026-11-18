# Skill lint evidence

Only focused local checks were run. Full checks and the independent verifier run on GitHub.

The old snapshot is vstack `c4a6d82` (2,261 words). The current snapshot is `4495320`, from PR 118 (596 words). Neither skill was edited for this task.

For each snapshot, copy it into `skills/valentin-mode/SKILL.md` in a scratch root and run:

```sh
python3 scripts/skill-lint --root "$scratch" \
  --house-rules "$house/house-rules.md" \
  --catalog "$house/skills" --catalog "$vstack/skills"
```

pstack 0.15.43 was selected from the installed cache.

## Old snapshot

Exit 1.

```text
skills/valentin-mode/SKILL.md:1: 2261 words exceed budget 800; delete repetition or move detail to a linked file; a higher skill-word-budget needs skill-word-budget-reason in frontmatter
skills/valentin-mode/SKILL.md:20: missing reference /i-have-adhd; fix the link or add the referenced skill/file
skill-lint: FAIL (1 skills, 2 findings)
```

## Current snapshot

Exit 0.

```text
skill-lint: PASS (1 skills, 0 findings)
```

## Focused checks

```text
python3 -m unittest tests.test_skill_lint -v
Ran 24 tests
OK

python3 scripts/skill-lint --base origin/main --catalog "$vstack/skills"
skill-lint: PASS (0 skills, 0 findings)

python3 scripts/rules-lint --diff origin/main
RULES-LINT bad=0
```

The historical regression runs the CLI and requires exit 1 plus the exact budget finding. The reference/copy, budget override, growth-body, prior-art, YAML, rename and cache-selection tests exercise their separate gates. No global budget exception or skill cleanup was added.

## Verifier failures reproduced and fixed

House-rules run `44297064255` found that accepted PR growth failed again on push, which has no PR body. The new regression fails against producer commit `c277103`:

```text
AssertionError: 1 != 0 : skills/sample/SKILL.md:1: grew from 61 to 111 words (>20%); add a PR body line 'Skill growth: skills/sample/SKILL.md <reason>'
skill-lint: FAIL (1 skills, 1 findings)
FAILED (failures=1)
```

The fix limits this PR-metadata requirement to PR events and local comparisons. The same regression requires push-time budget and missing-reference checks to keep failing.

Vstack run `44297236605` returned PASS+NOTES, but the execution recorder rejected actual successful calls prefixed with `cd <change checkout> &&`. A regression reproduced that false FAIL before the parser change. The recorder now accepts only that prefix, while rejecting wrong directories, fabricated wrappers, nonzero exits, empty output and tool errors.

```text
python3 -m unittest tests.test_skill_lint -v
Ran 26 tests
OK
```
