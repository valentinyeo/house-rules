# Verification gate

Every requirement gets a blocking result.
There is no score or PR exemption.
Bug labels activate additional history checks.
Verification labels bypass nothing.

`fleet/verify-score` retains its historical filename.
It now prints named PASS or FAIL results.
Each failure names its missing artifact.
`--json` returns items without a percentage.

## Book requirements and our additions

The source is Lauren Tan's pstack checklist.
This rewrite follows its quoted requirements.
The requested additions remain explicitly separate.

| Requirement | Enforcer | Source |
| --- | --- | --- |
| Agent drives the real app | `real-app` | Book |
| Human is not the verifier | `agent-verifier` | Book |
| Every code entry appears in map | `feature-map` | Requested coverage rule |
| Repro committed before fix | `repro-first` | Book, bug PRs |
| Failing test committed before fix | `test-first` | Requested strict bug rule |
| Different-family adversarial verdict | `adversary` | House rule and requested addition |
| Executed verify-skill fixture tests | `skill-tests` | Requested addition |
| Rules enforced locally and in CI | `hard-rules` | Book |
| Verdict covers current head | `current-head` | Book |
| Dataset size in verdict | `real-size` | Our requested rule |
| Verifier evidence from GitHub Actions | `github-run` | House rule |
| Video or trace before release | `release-proof` | Requested rule |
| Every check demonstrated failing first | `seen-failing` | Book and requested fixtures |

The fix is this gate rewrite.
There is no ceremonial "Fix" checkbox.
The book permits conditional regression-test exceptions.
This requested gate requires tests for bugs.
It requires failure before the fix commit.

Spend tokens on verifying, our rule.
Budget for real driving and independent checks.
Token spending has no executable check.
The book defines model and swarm choices.
It does not prescribe generous token spending.

## Local commands

Install the YAML reader before running checks.

```sh
python3 -m pip install PyYAML==6.0.2
python3 tests/test_verify_gate.py --demonstrate
python3 tests/test_verify_gate.py --incident
python3 -m unittest discover -s tests -p test_verify_gate.py -v
python3 fleet/verify-score /path/to/repo --context /path/to/context.json --evidence /path/to/evidence
python3 fleet/verify-score /path/to/repo --context /path/to/context.json --evidence /path/to/evidence --check feature-map
```

The demonstration runs every broken fixture first.
Then it runs every passing fixture.
Tests create Git history inside temporary directories.
They never commit inside the working repository.

The fixture reconstructs the reported short-chat incident.
The broken handoff loses a user message.
Its regression test actually fails before fixing.
The fixed handoff preserves that message.
Missing drive evidence still blocks the gate.
These fixtures are not historical incident evidence.
They never run the installed short-chat hook.

## Trust and evidence

CI reads PR facts through GitHub's API.
It fetches the posted verdict comment.
It downloads evidence from that Actions run.
It never executes PR code during inspection.
The verifier runs the app separately.
All verifier jobs must use GitHub-hosted runners.
Self-hosted jobs fail, even alongside hosted jobs.
This gate's own run cannot verify itself.

The base commit supplies `.verify/policy.json`.
A PR cannot replace its own trusted policy.
Policy changes need separate review before adoption.
A registered login identifies the verifier agent.
Its configured family must differ from the author's.
GitHub cannot attest the model's actual vendor.
Protect the verifier account and workflow accordingly.
A forged identity inside artifact JSON grants nothing.

The collector checks the current checkout SHA.
The verdict must cover that same head.
Latest allowlisted verdict wins, including FAIL.
Human approval alone cannot supply verification.
PASS and PASS+NOTES can authorize progression.
FAIL remains a valid verdict, blocking progression.

The collector downloads `pstack-verification` from Actions.
Its `verification.json` names the evidence files.
Every named artifact needs its SHA256 digest.
Escaping paths and symlinks are rejected.
Expired or missing Actions artifacts block verification.
Download size cannot exceed 100 MB.
Artifacts attest execution through the trusted verifier.
The gate cannot judge arbitrary transcript truthfulness.

Local contexts are fixtures or API snapshots.
Local JSON alone supplies no GitHub attestation.
CI always recollects facts through GitHub's API.
Never grant merge authority from hand-written snapshots.

## Repository policy

Use a reviewed, immutable gate commit SHA.
The example SHA is a replacement marker.
Keep all required statuses protected in GitHub.
Repository administrators configure branch protection separately.
This rewrite does not change GitHub settings.

```json
{
  "authors": {"author-agent": "openai"},
  "verifiers": {
    "verifier-agent": {
      "family": "anthropic",
      "workflow": ".github/workflows/pstack-verifier.yml"
    }
  },
  "gate_workflow": "valentinyeo/house-rules/.github/workflows/verify-gate.yml@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_exclusions": {
    ".verify/config.json": "Verification metadata, not application code.",
    ".github/workflows/verify.yml": "Verification workflow, not application code.",
    ".github/workflows/release.yml": "Release workflow inspected by release-proof."
  },
  "release_workflows": [".github/workflows/release.yml"]
}
```

Exclusions need an exact path and reason.
They come from trusted base policy.
Tests and configuration may need explicit exclusions.
Do not exclude application entry points.

## Feature coverage

The initial adapter supports Python registration calls.
It does not support arbitrary Python frameworks.
Other languages and unsupported sources block adoption.
Extend and test the adapter before using them.
Do not claim universal semantic code coverage.

Configure `.verify/config.json` for the supported contract.

```json
{
  "adapter": "python-registration-v1",
  "source_roots": ["app"],
  "skill": ".cursor/skills/verify-chat/SKILL.md",
  "features": ".cursor/skills/verify-chat/features"
}
```

Registration names identify all nine entry types.
Use `screen`, `route`, `button`, `menu`, `shortcut`.
Also `command`, `setting`, `endpoint`, and `job`.
Each supports the `register_` prefix too.
The first argument must be a literal string.
Dynamic registration arguments block adoption.

Supported command methods include `add_parser`, `add_command`.
Route methods include `add_url_rule`, `add_api_route`.
HTTP decorators include `get`, `post`, `put`, `patch`, `delete`.
HTTP method calls support `app`, `router`, `api`.
Other HTTP decorator receivers also produce entries.

Tracked source files must fall within scanned roots.
That includes supported extensions and executable files.
Unknown files inside roots block the check.
Only trusted, explained exclusions bypass source scanning.
New source files outside roots fail coverage.
The adapter compares code entries with map entries.
Every missing entry fails, even just one.
Dead map entries fail too.
One complete entry can pass.
No ten-entry minimum remains.

Each feature file needs the book's four sections.
Its README must link that feature file.
Record each entry with this exact syntax.

```md
# Chat handoff

Preserve pending user messages during chat handoff.

<!-- entry: job|short-chat|app/short_chat.py -->
<!-- entry: command|send-message|app/short_chat.py -->

## Sub-features

Send and hand off pending messages.

## How to get to it (user POV)

Send a message during a chat handoff.

## Driving it with Python

Drive the chat and inspect the received message.

## Gotchas

A handoff must preserve the original message.
```

This checks map completeness within the adapter contract.
It does not require driving every feature per PR.
The book allows one mapped feature per run.
The real-app check still requires captured driving.

## Verdict comment

Post this block from the registered verifier account.
Replace example values with the actual evidence.
The collector supplies login and comment identity.
Caller-supplied identity fields cannot override those facts.

````md
```verify-verdict
{
  "status": "PASS+NOTES",
  "head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "run_url": "https://github.com/owner/repo/actions/runs/12345",
  "dataset": {
    "count": 2000,
    "unit": "pending user messages",
    "production_comparison": "Matches the busiest observed queue."
  }
}
```
````

The count must be positive.
The comparison must explain production-size relevance.
An inapplicable dataset still needs a concrete note.
For example, count the real user journeys exercised.
The gate checks presence, not statistical adequacy.

## Evidence manifest

Upload these files together as `pstack-verification`.
Generate SHA256 values from their actual bytes.
The example digest map needs real values.

```json
{
  "head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "driver": "agent",
  "surface": "real chat handoff",
  "command": "send message, trigger handoff, inspect next chat",
  "drive": "drive.log",
  "adversarial_report": "adversary.md",
  "skill_test_output": "skill-tests.log",
  "release_proof": "handoff.trace",
  "seen_failing_output": "seen-failing.log",
  "sha256": {},
  "skill_tests": {
    "command": "python3 test_drive.py",
    "passed": 2,
    "failed": 0,
    "fixtures": {"pass": true, "fail": true}
  },
  "history": {
    "repro_sha": "cccccccccccccccccccccccccccccccccccccccc",
    "repro_path": "evidence/repro.json",
    "test_sha": "dddddddddddddddddddddddddddddddddddddddd",
    "test_path": "tests/test_message.py",
    "fix_sha": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "test_run_id": 12344
  }
}
```

`drive` accepts transcripts or traces.
Formats are `.txt`, `.log`, `.json`, or `.zip`.
Release proof accepts `.mp4`, `.webm`, `.zip`, `.trace`.
This gate requires release proof on PRs too.
That keeps release readiness visible before merging.

Bug PRs require the history object.
Repro and test commits must precede the fix.
They must follow the PR base commit.
The fix must belong to the head history.
The named artifacts must change in their commits.
The committed repro JSON needs these fields.

```json
{"command": "reproduce", "output": "actual failing output", "exit_code": 1}
```

The historical test run must actually fail.
It must cover the earlier test commit.
Upload `pstack-failing-test` from that failing run.
It must contain `test-result.json`.

```json
{
  "head_sha": "dddddddddddddddddddddddddddddddddddddddd",
  "test_path": "tests/test_message.py",
  "command": "python3 tests/test_message.py",
  "output": "actual failed assertion output",
  "exit_code": 1
}
```

The collector checks the actual Actions conclusion.
The verifier supplies the specific failure attribution.
An unrelated failing job is not sufficient evidence.
Configure the trusted verifier to reject that case.

`seen-failing.log` contains the demonstration command's output.
Every item needs BROKEN FAIL before VALID PASS.
The CI workflows execute that command themselves.
They also execute every fixture-pair regression test.

## CI installation

Pin the reviewed revision in each caller.
Use `.github/workflows/verify.yml` for PR enforcement.
Keep the policy's workflow pin identical.
Grant the called workflow these permissions.

```yaml
name: verification
on:
  pull_request:
permissions:
  contents: read
  pull-requests: read
  actions: read
  id-token: write
jobs:
  verify-gate:
    uses: valentinyeo/house-rules/.github/workflows/verify-gate.yml@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    with:
      pr-number: ${{ github.event.pull_request.number }}
```

There is no enforcement opt-out input.
OIDC identifies the called workflow's exact revision.
The gate checks out that immutable revision.
It never fetches executable gate code from main.
Gate tests also run from that same revision.

`verify-gate-tests.yml` tests this repository's PR changes.
Its checkout uses the current PR workflow SHA.
Both workflows use `ubuntu-latest` runners.
No self-hosted runner is configured.

Require all thirteen matrix checks in branch protection.
Use the actual emitted GitHub status names.
No hosted run has confirmed those names yet.
Also require the collection job to pass.
A collector failure leaves named checks blocking.
Missing evidence cannot silently exempt a PR.

Verdict comments do not trigger this reusable workflow.
Rerun the PR workflow after posting new evidence.
A new push requires a fresh matching verdict.
No auto-merge is earned until all checks pass.
Required branch checks prevent stale-verdict merges.
No auto-merge command runs during this rewrite.

Release publishing must depend on this gate.
List every release workflow in trusted policy.
The release check inspects every listed workflow.
Publishing jobs need a successful verification dependency.
`if: always()` and ignored failures are rejected.

```yaml
name: release
on:
  workflow_dispatch:
    inputs:
      pr:
        required: true
        type: number
permissions:
  contents: read
  pull-requests: read
  actions: read
  id-token: write
jobs:
  verify-gate:
    uses: valentinyeo/house-rules/.github/workflows/verify-gate.yml@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    with:
      pr-number: ${{ inputs.pr }}
      mode: release
      release-sha: ${{ github.sha }}
  publish:
    needs: verify-gate
    runs-on: ubuntu-latest
    steps:
      - run: ./publish-reviewed-release
```

No publication occurs in this repository's draft.
Installation requires the adopting repository's release workflow.

Add the enforcement table to `AGENTS.md`.
Each required row uses this form.

```md
| real-app | verify-gate / real-app |
| agent-verifier | verify-gate / agent-verifier |
| feature-map | verify-gate / feature-map |
| repro-first | verify-gate / repro-first |
| test-first | verify-gate / test-first |
| adversary | verify-gate / adversary |
| skill-tests | verify-gate / skill-tests |
| hard-rules | verify-gate / hard-rules |
| current-head | verify-gate / current-head |
| real-size | verify-gate / real-size |
| github-run | verify-gate / github-run |
| release-proof | verify-gate / release-proof |
| seen-failing | verify-gate / seen-failing |
```
