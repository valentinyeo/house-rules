# Gates: YPER4-1349 shared writing rules

OWNS: skills/tickets/scripts/ticket-lint, skills/tickets/writing-rules.json, skills/tickets/writing-fixtures.json, skills/hypertask-triage/scripts/ticket-check, tests/test_ticket_writing_rules.py, tests/test_ticket_question_rules.py, GATES.md

Scope: One machine-readable rule list, house-check adoption, parity fixtures for app adoption, CI proof, and live installation. Leave human guidance unchanged unless a permitted blind trial proves a benefit.

- [ ] G1: House checker reads the rule list and passes positive and negative shared fixtures in GitHub-hosted CI.
  EVIDENCE: pending; VPS tests forbidden. CI must execute tests/test_ticket_writing_rules.py.

- [ ] G2: Hypertask consumes the same list and passes the same fixtures.
  EVIDENCE: pending; app integration belongs to HTPR-8798, not this infrastructure patch.

- [x] G3: Human guidance stays unchanged without blind-agent evidence.
  EVIDENCE: Reviewed changed paths with git diff and git status; skills/tickets/SKILL.md and house-rules.md are unchanged. No helpers launched; no blind-agent result claimed.

- [ ] G4: One reviewed PR merges and the installed house checker matches its merge.
  EVIDENCE: pending.
