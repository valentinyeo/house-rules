---
name: verification-check
description: Audit a repo's verification setup against pstack end to end, including GitHub PR checks, job budget, formal coverage and upkeep, and pstack version drift. Print a checklist with icons, evidence, and the pstack skill that fixes each gap. Works for web, desktop, mobile, CLI, and services. Use for /verification-check [repo path or session name], "is this session's verification set up properly", or "how far is X with verification". Read only.
---

# Verification check

Prior art: checked pstack create-verification-skill, maintain-verification-skill, the formal-verification skills, shipping step 1, bug-fix, eval, and principle-prove-it-works. Those build, maintain, or run verification. This skill audits the whole setup without changing it.

Compare the repo's real setup with pstack's demands. Read only. Never edit the target, fetch, file tickets, push, change GitHub settings, launch workflows, or start workers. Inspect existing source and runs only. Recommendations are not permission to execute them.

## 1. Resolve the target

The argument is a repo path or live session name. No argument means the current repo. `facts.sh` resolves session names through `~/.local/share/house-rules/fleet/roster-live`. If the roster omits its path, use its session metadata and confirm the Git remote. Never guess a repo from its folder name.

## 2. Collect the facts and load pstack

```sh
"$(dirname "$(readlink -f ~/.claude/skills/verification-check/SKILL.md)")/facts.sh" <repo-path | session-name>
```

`facts.sh` reads the locally available default-branch snapshot. It prints its commit, without fetching. GitHub facts are live. If the local snapshot differs from GitHub's default branch, read the current files through `gh api` before judging them. Disclose unavailable or stale evidence. Never call missing permissions a passing check or zero jobs.

Read the highest installed pstack under `~/.claude/plugins/cache/*/pstack/*/skills/`, as selected numerically by `facts.sh`. Read these sources, not your memory:

- `create-verification-skill/SKILL.md`: launch, doctor, drive, evidence, cleanup, helpers, and feature map.
- `maintain-verification-skill/SKILL.md`: periodic source review and live driving of every feature.
- `create-formal-verification-skill/SKILL.md` and `maintain-formal-verification-skill/SKILL.md`: formal coverage where applicable and its upkeep.
- `poteto-mode/playbooks/shipping.md`, step 1: one independent verifier per PR, base against head, with `PASS`, `PASS+NOTES`, or `FAIL`.
- `poteto-mode/playbooks/bug-fix.md`: reproduce first, failing repro before the fix, and verify on the same app.
- `poteto-mode/playbooks/eval.md`: blinded skill evaluations.
- `principle-prove-it-works/SKILL.md`, `tdd/SKILL.md`, and `correct/SKILL.md`: real behavior, failing tests where practical, and enforced rules.

The CI policy also includes Valentin's additions: the verdict is the only required check, reuse base results, no full-suite PR runs, heavy UI runs on the default-branch schedule, cheap PR checks, fewer than 20 jobs, cancellation, and revert first. Do not attribute those additions to a pstack source that does not contain them.

Open the files named by the collector. A filename, keyword, or verdict written by the author is not proof. Inspect workflow commands, called scripts, model identity, base/head evidence, scheduled branch, and active branch protection plus rulesets. All applicable required checks together must contain only the verifier verdict. Check the last three PR heads' job totals from the runs/jobs APIs, including pagination and reruns. Unknown or still-running totals cannot prove the budget.

### Pstack drift

Each verify skill must record a standalone `pstack: <version>` line. A missing or invalid line is a gap, not proof of alignment. Conflicting version lines are also a gap.

When the installed version is newer, `facts.sh` compares these eight sources between the recorded and installed versions:

- `create-verification-skill/SKILL.md`
- `maintain-verification-skill/SKILL.md`
- `create-formal-verification-skill/SKILL.md`
- `maintain-formal-verification-skill/SKILL.md`
- `poteto-mode/playbooks/shipping.md`
- `poteto-mode/playbooks/bug-fix.md`
- `poteto-mode/playbooks/eval.md`
- `principle-prove-it-works/SKILL.md`

Read the diffs. Explain the changed demands in plain words. If the old version or a source is unavailable, say the comparison is incomplete. Never infer no drift from a missing diff. A newer version still requires re-alignment when these eight files are unchanged. Do not update the recorded version yourself.

### Formal coverage and upkeep

`facts.sh` invokes its sibling `formal_facts.py` with the repo and audited Git ref. It reads project skills by their contents, not just names, and inventories formal model files. It follows referenced JSON coverage records, such as `sync_commit` plus function `file` entries. Otherwise it looks for a recorded sync commit and covered paths in the skill. No target scripts or checks are executed.

Read the named skill, models, coverage record, and code. Confirm which properties, features, bounds, commands, and current run evidence the formal checks cover. A solver name or model file is only a candidate, not proof. Money, cross-device sync, retries, and queues need formal checks for their actual risky behavior. A scroll model does not prove a delivery queue. If a risky area has no formal coverage, recommend `/pstack:create-formal-verification-skill`, even when another area already has checks.

The collector lists recent commits touching each formal setup and counts covered-file commits since its recorded sync commit. Any covered code change needs `/pstack:maintain-formal-verification-skill` to determine whether the model still describes it. Changes outside the recorded coverage do not alone make it stale. Missing sync metadata, missing covered files, unavailable history, or a non-ancestor sync commit leave alignment unproven. Recommend maintenance to establish it, not a false pass. Commit counts show review work, not proof of a product bug. Read the whole relevant history, not only the five-commit excerpt, including moved code and new callers sharing the guarded state.

## 3. Judge each item

Match the app. Web apps use a real browser, Windows desktop the real exe on a GitHub Windows runner, Android an emulator on GitHub plus a real phone before release, iOS a simulator, CLIs a PTY, and services real HTTP.

Use these 24 items in this order:

1. Agent drives the real app, following its verify skill.
2. Human is not the verifier. Recent bugs were caught by an agent before the owner saw them.
3. Feature map has one file per user-facing feature and the four sections pstack demands.
4. Map coverage is counted against the app's real features, for example "41 of 230". Below 100% is not done.
5. Map stays current. A check blocks unmapped features and a scheduled maintain-verification-skill pass runs.
6. Bug reproduction comes first. A journey fails on base and passes on head. A cheap regression test lands before the fix where practical.
7. Agents try to break each fix.
8. Verify-skill tests show a planted bug giving FAIL and a clean build giving PASS, across more than one model family.
9. Hard rules have a rule table pairing each rule with its enforcing check.
10. Auto-merge is earned. Nothing merges on a verdict items 1 to 8 cannot support.
11. Most active work goes to verification until this list is green.
12. Journeys start with seeded data at real user scale.
13. One independent verifier runs each PR on GitHub, base against head, posts PASS, PASS+NOTES, or FAIL, and its verdict is the only required check. The verifier did not write the change and uses another model family.
14. Release requires recorded video or trace for each changed feature.
15. Verifier results arrive in about 20 minutes, measured from existing runs.
16. PR verification selects only touched features' journeys plus the bug's repro journey. It reuses base results rather than running the full suite.
17. Heavy UI workflows and full-suite runs happen on a schedule on the default branch, not on PRs. Only cheap build, unit, lint, and secret checks run on every PR alongside the scoped verifier.
18. Each of the last three PR head commits uses fewer than 20 jobs. Incomplete API data, queued runs, or missing runs do not prove this.
19. Workflows use concurrency groups that cancel superseded work with `cancel-in-progress: true`. Read expressions and called workflows, not just the key's presence.
20. Emergency policy says revert the bad change first. The real fix follows normal verification, with no skip lane.
21. Each verify skill records the pstack version its setup follows.
22. Setup follows the installed pstack's current demands. Any newer version is flagged, its source changes explained, and re-alignment required.
23. Money, cross-device sync, retries, and queues have formal checks for the risky behavior actually present. If none applies, explain that with source evidence instead of inventing a missing check.
24. Existing formal checks describe the current covered code. Their sync commit, covered paths, changed-code review, and current proof are recorded. Missing metadata or changes since sync cannot count as done.

If current pstack adds a demand this list lacks, append it and increase the denominator. Say which source required the extra item. Formal verification demands apply where relevant, not to every repo regardless of risk.

## 4. Reply

Normally start with `<repo>: N of 24 done`. Count only proven ✅ items. Adjust 24 if you appended demands.

Exceptions go before that count:

- No verify skill: first line is `<repo> has no verification skill. Run /pstack:create-verification-skill before anything else.` This is a recommendation to the target session, not permission for this read-only audit to run it. Still print the count and every checklist item.
- Installed pstack is newer: first line is `PSTACK CHANGED`. The next lines name recorded and installed versions, explain what changed in plain words, and say `The repo must re-align.` Then print the count and every item. If several skills exist, identify each affected one.

Print one line per item with an icon and one plain sentence of evidence. Every reported gap, including 🟡, ⬜, ⏸, and ❌, ends with `Fix: /pstack:<skill>`. This also applies to extra demands and the final most-important gap. Name the entry point and the needed change. Never report a gap with only "fix this" or a bare playbook name.

Use this routing:

| Gap or checklist items | Fix command |
| --- | --- |
| No runnable verify skill, including item 1 when absent | `/pstack:create-verification-skill` |
| Existing skill cannot drive the app; stale map, missing features, coverage gaps, or no scheduled maintenance; items 1, 3–5, 12, 14, 21–22 | `/pstack:maintain-verification-skill` |
| Money, cross-device sync, retries, or queues lack relevant formal checks; item 23 | `/pstack:create-formal-verification-skill` |
| Formal checks exist but covered code changed since sync, or their coverage/sync record is missing; item 24 | `/pstack:maintain-formal-verification-skill` |
| Repro-first or regression-test gaps; item 6 | `/pstack:poteto-mode` with the bug-fix playbook; `/pstack:tdd` for a cheap failing test |
| No break-it pass; item 7 | `/pstack:interrogate` |
| Verify-skill evaluation gaps; item 8 | `/pstack:poteto-mode` with the eval playbook |
| Unenforced hard rules; item 9 | `/pstack:correct` |
| Independent verification, merge policy, CI scope, job budget, cancellation, speed, or revert-first gaps; items 2, 10–11, 13, 15–20 | `/pstack:poteto-mode` with the shipping playbook |

Creation comes before maintenance when the relevant skill is absent. If formal checks are needed but absent, both formal items point to `/pstack:create-formal-verification-skill`; maintenance is only for an existing setup. If pstack drift also affects existing formal checks, name `/pstack:maintain-formal-verification-skill` alongside the ordinary maintenance command. For a new demand, choose the pstack skill that owns it from the source you read. When a skill cannot perform the CI wiring within its edit scope, name that wiring as the follow-on work rather than claiming the command fixes it automatically. These are recommendations for the target session. This audit never runs the commands.

Use full https:// file, run, or PR links tied to the audited commit. Print this legend once:

- ✅ done and proven by a file or run you read
- 🟡 partial, in progress, or unproven because evidence is unavailable
- ⬜ not started
- ⏸ on hold on purpose
- ❌ exists but fails or is bypassed

Use plain words for a product owner. End with the single most important missing item. Never fix it during this audit.
