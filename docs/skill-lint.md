# Skill lint

One script owns these checks: `scripts/skill-lint` in house-rules. Both repos call the reusable GitHub workflow. vstack pins that workflow and its script to the same house-rules commit. No live installed skills are edited.

Prior art checked: pstack 0.15.43 `poteto-mode/playbooks/authoring-a-skill.md`, `principle-encode-lessons-in-structure/SKILL.md`, and `correct/SKILL.md`. These specify the behavior but supply no executable check for our two skill collections.

## Run locally

Install `PyYAML==6.0.2`. From either checkout, run the shared script:

```sh
python3 /path/to/house-rules/scripts/skill-lint --base origin/main \
  --house-rules /path/to/house-rules/house-rules.md \
  --catalog /path/to/house-rules/skills --catalog /path/to/vstack/skills
```

The script picks the highest numeric pstack version across `~/.claude/plugins/cache/*/pstack/*/skills`. Override with `--pstack /path/to/pstack/skills`. The default root is the current directory; `--root` changes it.

Omit `--base` for a full audit, or supply specific `skills/<name>/SKILL.md` files. Full audits report legacy debt rather than silently exempting it. CI checks complete changed skills since the merge base, not unrelated legacy skills. Renames retain their previous baseline. New means a skill absent at that baseline.

CI fetches pstack and the other skill collection at full commit pins in `.skill-lint.json`. It verifies pstack's `plugin.json` version. No runner-local cache is trusted. PR-body edits rerun the gate.

## What fails

- **Budget:** whitespace-separated words across the entire `SKILL.md`, including frontmatter and examples. Default 800.
- **Growth:** more than 20% versus the baseline needs a file-specific PR-body line. New skills use the budget and prior-art checks instead. Push events have no PR body, so this requirement runs on PRs and local comparisons, not again after merge. Every other check still runs on pushes.
- **Restating:** prose sentences or bullets with at least eight distinct normalized tokens and Jaccard token overlap of at least 0.82 against pstack's skill/playbook Markdown or `house-rules.md`. Case, punctuation and Markdown formatting do not hide a copy. Wrapped paragraphs are joined. Headings, tables and fenced examples are excluded. This is a near-copy detector, not a semantic paraphrase detector; short generic sentences are intentionally excluded.
- **References:** local Markdown links, reference-link definitions, backticked file/directory paths, `/skill` calls, `/pstack:skill` calls and `pstack` followed by a backticked skill name must resolve. Search the current skill, repo, pstack (including poteto-mode's relative playbook paths) and supplied skill catalogs. Explicit pstack references resolve only in pstack. Native `/clear`, `/rename`, `/compact` and `/loop` commands are not skills. HTTP/mail links are not fetched. Anchors are not validated. Placeholder paths and fenced examples are not literal file references. Ordinary prose and shell commands are not guessed to be paths.
- **Frontmatter:** valid YAML with nonempty string `name` and `description`.
- **New skill:** a `Prior art:` line must name pstack and an existing pstack skill checked.

Every finding names the offending file and the fix. A copied rule says `link to <source path> instead of restating`. There is no global budget allowlist.

## Declare a larger budget

Only the skill's YAML frontmatter can raise its limit:

```yaml
skill-word-budget: 1000
skill-word-budget-reason: This reference protocol must remain together.
```

A reason in body prose does not count. The budget must be an integer of at least 800; its reason must be a nonempty string.

For an existing skill growing by more than 20%, add one PR-body line per file:

```text
Skill growth: skills/example/SKILL.md Added the new release protocol.
```

Pass a local PR body with `--pr-body-file body.md`. GitHub supplies its event body automatically. The line does not waive any other check.

New skills need their checked source in the skill itself:

```text
Prior art: pstack poteto-mode/playbooks/authoring-a-skill.md was checked for an existing release policy.
```

## Regression proof

`tests/fixtures/skill-lint/valentin-mode-old.md` is the unmodified 2,261-word skill from vstack commit `c4a6d82`. The executable regression requires a nonzero exit and the exact `2261 words exceed budget 800` finding.

`valentin-mode-current.md` is the 596-word snapshot from vstack commit `4495320` (PR 118), not a cleanup made by this change. It passes all checks with installed pstack 0.15.43 and both repo catalogs. vstack main still contains a larger version while PR 118 remains open. See [the recorded outputs](skill-lint-evidence.md).

Run the focused regression file with:

```sh
python3 -m unittest discover -s tests -p test_skill_lint.py -v
```

The shared workflow runs these regressions, the real diff lint, and an independent verifier on GitHub-hosted runners. `scripts/pick-verifier-model` picks the verifier from the PR body's `Author model:` lines: DeepSeek Flash unless an author is DeepSeek, then GLM, then Kimi. The family is read from the whole declared string, so `opencode-go/deepseek-...` counts as DeepSeek. A missing line or an unknown family fails the check, and the posted verdict names the model used. The verifier must return a current-head verdict and successful execution evidence for both required commands. A command may have only an exact `cd <change checkout> &&` prefix. Wrong directories, other wrappers, failed commands and empty output do not count. The verifier also makes three independent break attempts. Fork PRs run deterministic checks without secrets.
