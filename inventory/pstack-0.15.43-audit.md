# Pstack duplication audit

Keep only local overrides in `house-rules.md`.
Baseline commit `314afbe`, ticket SOFT-2574.
Pstack version `0.15.43`, upstream commit `e1cc03121a0e71129a4fb730d7c5528a0a3e43c8`.
Paths below use that pinned upstream revision.

## Original prose

| Baseline line | Decision | Source or remaining difference |
| --- | --- | --- |
| 1, heading | Keep | Document title. |
| 3, mandatory pstack and precedence | Keep | Pstack doesn't mandate itself across all agents. Local orchestrator routing remains. Drop the historical orchestrate parenthesis. [Poteto-mode](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/poteto-mode/SKILL.md#playbooks) routes tasks, without this precedence policy. |
| 5, tickets | Keep | Hypertask, own board, own login, live columns. Ticket-only status and questions remain local. [Autonomous run](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/poteto-mode/playbooks/autonomous-run.md) requires checkpoints, without these destinations. |
| 7, Cloudflare template | Keep | Pstack doesn't prescribe `joelhooks/rat-stack`. |
| 9, Valentin's heading | Keep | Rename to identify additional requirements. |
| 10, verifier | Split | Delegate shared verification to [Shipping, step 1](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/poteto-mode/playbooks/shipping.md). It requires independent user-driven verification and posted verdicts. CI and bot approval don't qualify. Keep the different-model-family requirement. Pstack's independent author requirement doesn't specify family. |
| 11, laptop and GitHub | Keep | Host placement is local. Shipping specifies Cursor cloud agents. Valentin specifies GitHub-hosted verification instead. Focused tests, QA phone, benchmarks remain allowed locally. Full suites, reviews, CI remain hosted. Self-hosted runners remain forbidden. |
| 12, plans and keys | Split | Keep setup ownership, keys, ordering, fallback, headroom. Keep Claude eligibility and DeepSeek Flash restriction. Drop "no need to ask anyone." [Poteto-mode, Autonomy](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/poteto-mode/SKILL.md#autonomy) already authorizes reversible actions. Local authorization for these keys remains explicit. |
| 13, reserved decisions and design | Keep | Money, keys, publicity, one ask remain local. Production deletion also appears in [Never block](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/principle-never-block-on-the-human/SKILL.md). "Live data" covers more than production data. Keep that wider scope. Keep recommendations and live design judgment. Keep labelled Figma variants before building. [Exhaust the design space](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/principle-exhaust-the-design-space/SKILL.md) doesn't require Figma or pre-build presentation. |
| 14, public repository and email | Keep | Local command, privacy setting, and email ban. Pstack doesn't prescribe these. |
| 15, waiting and fresh chats | Split | Delegate generic continuation to [Never block](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/principle-never-block-on-the-human/SKILL.md). Keep handover, fresh chat, loop, and `/clear` ban. [Pause safely](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/poteto-mode/playbooks/pause-safely.md) saves resume notes. It doesn't require automatic fresh-chat creation. |
| 16, billing failure | Keep | Local billing owner, failure trigger, and response. Shipping waits for checks. It doesn't prescribe this billing workflow. |
| 18, enforcement instructions | Delegate | [Correct, Keep the rule table](https://github.com/cursor/plugins/blob/e1cc03121a0e71129a4fb730d7c5528a0a3e43c8/pstack/skills/correct/SKILL.md#keep-the-rule-table) owns table upkeep and structural enforcement. Keep local enforcement facts below. |

## Original enforcement table

These rows record local mechanisms and gaps.
Pstack doesn't name these installed mechanisms.
Keep every row, with two narrower labels.

| Baseline line | Decision | Local fact |
| --- | --- | --- |
| 20-21 | Keep | Table header and separator. |
| 22 | Keep | Mandatory-pstack enforcement remains absent. |
| 23 | Keep | Ticket identity and column enforcement remain absent. |
| 24 | Keep | Template enforcement remains absent. |
| 25 | Narrow label | Different-model-family enforcement remains absent. Planned verifier check remains explicitly pending. |
| 26 | Keep | `no-vps-ci` and five-minute cadence. |
| 27 | Keep | Reserved decisions remain judgment calls. |
| 28 | Keep | `ticket-lint` rejects design-pick Questions. |
| 29 | Keep | Pre-build presentation enforcement remains absent. |
| 30 | Keep | Required `rules-lint`, including admins. Product-repository gap remains explicit. |
| 31 | Keep | `new-public-repo` and repository email checks. |
| 32 | Keep | Local `secrets-guard` hook. |
| 33 | Narrow label | `short-chat`, loop preservation, two-hour fallback, auto-compact. |

## Regression coverage

`tests/test_pstack_delegation.py` rejects known duplicate wording.
It requires pointers and preserves verifier differences.
It doesn't classify arbitrary future prose semantically.
`rules-lint.yml` runs it on GitHub.

## Principles used

- Laziness Protocol. Remove only covered clauses.
- Encode Lessons in Structure. Reject returning duplicates.
- Build the Lever. Commit the rerunnable regression.

## Review trail

Repeated drift prompted this audit.
`0368745` corrected obsolete orchestrate routing.
`9ec898f` added continuation beside pstack's existing rule.
Documentation alone allowed both to drift.
CI now rejects these known duplicate statements.
Semantic equivalence still needs source comparison.
