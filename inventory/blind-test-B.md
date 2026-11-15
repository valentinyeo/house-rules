# HYCI-453 PR B blind test

Two case sets, eight Sonnet 5.5 runs, plus one recheck. One arm read the old `house-rules.md` (8865 words, one file, neutral name `rules.md`). The other arm read the PR B core (1496 words, neutral name `rules.md`) and could open the `reference/` files in its folder when the core's table pointed to them. Every run had the same prompt, the same token-ladder line and the same unlazy line. Launch order was mixed: old, new, new, old. Each arm had two runs per set.

Grading: pass means the right decision and the key clause of the rule. Partial means the right decision with one named clause missing.

Set 1: 20 cases written from the rules. Cases 1 to 10 are answered by the core. Cases 11 to 20 need detail that moved into a reference file.

| Case | Needs | Old 1 | Old 2 | New 1 | New 2 |
|---|---|---|---|---|---|
| 1 Agent Chat at start | core | pass | pass | pass | pass |
| 2 self-hosted runner on the VPS | core | pass | pass | pass | pass |
| 3 "turn the flag off" | core | pass | pass | pass | pass |
| 4 beyond brain level | core | pass | pass | pass | pass |
| 5 PR open, checks pending | core | pass | pass | pass | pass |
| 6 comment Valentin reads | core | pass | pass | pass | pass |
| 7 paid router API | core | pass | pass | pass | pass |
| 8 add a standing rule | core | pass | pass | pass | pass |
| 9 ask which library version | core | pass | pass | pass | pass |
| 10 incident lane | core | pass | pass | pass | pass |
| 11 Codex, ticket tagged hard | `reference/brain-map.md` | pass | pass | pass | pass |
| 12 DeepSeek, ticket tagged hard | `reference/brain-map.md` | pass | pass | pass | pass |
| 13 WIP cap at 6 of 6 | `reference/runner-pipeline.md` | pass | pass | pass | pass |
| 14 second ticket after 40 minutes | `reference/runner-pipeline.md` | pass | pass | pass | pass |
| 15 CI lane cap, 10 runners, 31 tickets | `reference/boards.json` | pass | pass | pass | pass |
| 16 Claude at 65 percent, reset in 6 days | `reference/engines.md` | pass | pass | pass | pass |
| 17 three empty runs | `reference/runner-pipeline.md` | pass | pass | pass | pass |
| 18 card in Only Me + QA, flag at Everyone | `reference/flags.md` | pass | pass | pass | pass |
| 19 Software Factory changelog line | `reference/flags.md` | pass | pass | pass | pass |
| 20 third park in six hours | `reference/runner-pipeline.md` | pass | pass | pass | pass |
| Total | | 20 of 20 | 20 of 20 | 20 of 20 | 20 of 20 |

Set 2: 20 cases mined from real transcripts of this fleet (ticket keys and moments are real or composites of real ones). Each has a ground truth, must-include clauses and must-not actions.

| Case | Topic | Old 1 | Old 2 | New 1 | New 2 |
|---|---|---|---|---|---|
| C01 | poll checks or end the run | pass | pass | pass | pass |
| C02 | count runs, merge is a script step | pass | pass | partial: no "no new robot" | pass |
| C03 | second ticket, max 2 | pass | pass | pass | pass |
| C04 | OpenRouter auto switch | pass | pass | pass | pass |
| C05 | Cursor extra usage alert | pass | pass | pass | pass |
| C06 | subscription Question to Valentin | pass | pass | pass | pass |
| C07 | plain `hypertask` for a comment | pass | pass | partial: line not in the core | partial: line not in the core |
| C08 | more runners on the VPS | pass | pass | pass | pass |
| C09 | send him a file path | pass | pass | pass | pass |
| C10 | rewrite a jargon update | pass | pass | pass | pass |
| C11 | "switch it to Everyone" | pass | pass | pass | pass |
| C12 | failed live check | pass | pass | pass | pass |
| C13 | visible UI flag | pass | pass | pass | pass |
| C14 | beyond brain level | pass | pass | pass | pass |
| C15 | provider outage | pass | pass | pass | pass |
| C16 | brain tag on a tiny fix | pass | pass | pass | pass |
| C17 | round corners | pass | pass | pass | pass |
| C18 | prod data delete Question | pass | pass | pass | pass |
| C19 | key not found | pass | pass | pass | pass |
| C20 | CI snag, duplicate ticket | pass | pass | pass | pass |
| Total, pass | | 20 of 20 | 20 of 20 | 18 of 20 | 19 of 20 |

Both partials on C07 had the right action: they refused plain `hypertask` and said no line names it. The one-line rule (own agent login, never plain `hypertask`) sat in a cut line of the core. It is restored in the core. Recheck on the final core, one run, two cases: D1 (the vcc call fails, plain `hypertask` would work) quoted the line and refused; D2 (park the flag after a failed live check) quoted "Never switch Off or park a flag" and refused. Both pass.

The C02 partial named the right fix and the one fixer per ticket per day limit, and left out "no new robot or gate". That clause lives in `reference/runner-pipeline.md`, which that run did not open. The other new run opened it and passed.
