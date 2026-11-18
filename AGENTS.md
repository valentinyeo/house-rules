# House rules maintenance

| Rule | Enforced by |
| --- | --- |
| Skills stay within budget and link instead of copying | `scripts/skill-lint`, called by `rules-lint.yml` |
| PRs explain existing skills growing more than 20% | `scripts/skill-lint`, GitHub PR-body events |
| Skill references resolve; new skills name pstack prior art | `scripts/skill-lint` |

Local commands and exception format: [docs/skill-lint.md](docs/skill-lint.md).
