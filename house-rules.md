# house rules

every agent uses pstack for everything: poteto-mode for any task, the autonomous-run playbook and figure-it-out for orchestrators. the only exception is work pstack has nothing to say about. if any other rule or skill disagrees with pstack, pstack wins. only valentin's lines beat it.

hypertask is where work lives. every unit starts and ends on a ticket, on the orchestrator's own board or view, under its own login (board-identity sets it up). move the ticket to the next column the moment its work moves, so the board always shows the true stage. status and questions go on the ticket, not in chat.

new cloudflare work starts from the joelhooks/rat-stack template.

pstack owns the shared behavior. Follow these sources:

- Verification follows `poteto-mode/playbooks/shipping.md`, step 1.
- Reversible work follows `principle-never-block-on-the-human/SKILL.md`.
- Reversible setup follows `poteto-mode/SKILL.md`, Autonomy.
- Rule enforcement follows `correct/SKILL.md`, Keep the rule table.

Paths use pstack 0.15.43's `skills/` directory.
The [audit](https://github.com/valentinyeo/house-rules/blob/40133c7bbd49f1c474d7198ff5e6b821c2a0fa84/inventory/pstack-0.15.43-audit.md) covers every original line.

valentin's additional lines:

- include [shared worker rules](docs/worker-brief.md) in every worker brief. This includes spawn-worker input. Report faults before working around them.
- The verifier uses another model family.
- this server is lauren's laptop: orchestrators, workers writing code, a focused test while fixing (pstack tdd), driving the app or the qa phone like a user, benchmarks, git, boards, keys. github-hosted runners are her cloud: the full test suite, ci, reviews and the pstack verifier. no self-hosted runner, ever.
- orchestrators set their reviewers and verifiers up themselves on valentin's deepseek, codex and claude plans, keys included, in that order, and move on when one runs out. claude is allowed for workers and checks. other plans go first while claude usage is high, so orchestrators keep headroom. on deepseek, always flash, never pro.
- valentin decides money, keys, going public and deleting live data. ask him once, with your pick. a design pick is never his: build your own pick, he judges it live. a ticket labelled needs-design gets 2-3 quick HTML variants built from the app's real styles (pstack prototype playbook), shown to him first; figma only when he asks on that ticket; no build starts before he has seen them.
- a public repo starts with `new-public-repo`, never github's template or fork button. no commit carries a real email. agents switch on github's "keep my email addresses private" for valentin themselves.
- a long chat saves its handover and starts its own fresh chat with its loop on; nobody types /clear.
- github billing is valentin's. when a check fails with "recent account payments have failed", the product pr waits. never verify it on this server or merge around the check. say it once on the ticket, then build the next unit.

## Board sync for orchestrators

Run reconcile yourself on your own board.
Supported boards are 15 and 2060.
Use your agent's `HT_TOKEN` and `SHIP_SESSION_NAME`.
Never use Valentin's personal login.

Preview without writes. Replace `2060` with your board.

```sh
~/.local/share/house-rules/fleet/reconcile --board 2060
```

`--section` restricts previews to one column.
It cannot accompany `--apply`.

```sh
~/.local/share/house-rules/fleet/reconcile --board 2060 --section Doing
```

Apply after reading the printed reasons.
`--limit` caps the entire run.
Exceeding the cap refuses every move.
Unknown facts also refuse every move.
Board 15 always caps runs at five.
It requires vcc or HT Product Lead credentials.

```sh
~/.local/share/house-rules/fleet/reconcile --board 2060 --apply --limit 5
```

Check each move against its printed reason.
Valentin Review is never touched.
Merged work still waits for live proof.
Reconcile never moves tickets to Done.
Read [the board rules](docs/fleet-reconcile.md) for details.

Local enforcement:

| line | enforced by |
| --- | --- |
| pstack for everything | nothing, judgment call |
| tickets, own login, true column | nothing yet |
| rat-stack for new cloudflare work | nothing yet |
| verifier from another model family | nothing yet; a required `pstack-verifier` check once the shared verifier workflow works |
| server is the laptop, github is the cloud | `no-vps-ci` kills runners and review units every 5 minutes |
| money, keys, public, deleting live data | nothing, judgment call |
| no design pick in his blockers | `ticket-lint` refuses a Question that asks him to pick a look or option |
| needs-design shown before build | nothing yet |
| no merge around a failed check | house-rules main: `rules-lint` required, admins included; product repos: nothing yet |
| no real email in a public repo | `new-public-repo` refuses to push one; per repo, a ci check on commit emails |
| no secrets anywhere | `secrets-guard` hook |
| fresh chat keeps its loop | `short-chat` hook: a long chat saves its handover and starts its own fresh chat, never deletes its loop; if fresh start fails it stays quiet 2 h and auto-compact keeps the chat going |
| worker briefs name both fault paths | poteto-2-advisor `.claude/hooks/book-check.py`, advisor-checks CI; fleet/runner includes the shared rules, tested in rules-lint CI; filing remains agent judgment |
