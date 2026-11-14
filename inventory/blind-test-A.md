# HYCI-453 PR A blind test

Four Sonnet 5.5 runs. Two read the old `house-rules.md` (8865 words). Two read the PR A file (5916 words). File names were neutral (`F1.md`, `F2.md`), arms were launched in mixed order, and every run had the same prompt, the same token-ladder line and the same unlazy line. Each run answered the same 10 cases using only its file.

| Case | Must include | Old run 1 | Old run 2 | PR A run 1 | PR A run 2 |
|---|---|---|---|---|---|
| 1 Agent Chat at start | `runner-chat listen`, reply | pass | pass | pass | pass |
| 2 self-hosted runner on VPS | no, GitHub-hosted only | pass | pass | pass | pass |
| 3 "turn the flag off" | do it that turn, never ask back | pass | pass | pass | pass |
| 4 beyond brain level | `RUNNER TOO HARD <KEY> \| why:` | pass | pass | pass | pass |
| 5 PR open, checks pending | end the run, picker resumes | pass | pass | pass | pass |
| 6 comment Valentin reads | caveman, answer first, quote block | pass | pass | pass | pass |
| 7 paid router API | only when Valentin says so | pass | pass | pass | pass |
| 8 add a standing rule | `/house-rules-update`, no dates or reasons | pass | pass | pass | pass |
| 9 ask which library version | no, look it up | pass | pass | pass | pass |
| 10 incident lane | incident lane, roll back first | pass | pass | pass | pass |
| Total | | 10 of 10 | 10 of 10 | 10 of 10 | 10 of 10 |

Result: parity. Nothing was restored. The cases touch rules whose prose PR A kept, so this shows PR A removed nothing a decision needs for those rules. It does not test the rules PR A deleted outright (priority fill, kept slot, wasted runs detail), because a script enforces those.
