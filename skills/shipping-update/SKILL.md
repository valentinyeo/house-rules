---
name: shipping-update
description: "Project shipping state: orchestrators, drain loops, worker limits, active workers, shipped tickets, backlog, PRs, model. Use for /shipping-update, 'state of the factory', 'update me', 'are we shipping'."
---

Run `~/.local/share/house-rules/fleet/factory-state` from the caller's repository.
Default output shows only the matching session.
Matching uses roster cwd first, then repo, then the caller folder name against the row name or repo name, ignoring case.
Session identity resolves multiple matches within repositories.
Ambiguous matches report failure, without other rows.
Poteto's `~/projects/poteto-2-advisor` receives every row and totals.
Use `--all` only for explicit fleet requests.
Use `--why` for loop and process reasons.
Use `--json` for selected rows as JSON.

Lead with totals when the output includes them.
Then show the table.
Preserve every `Not good:` line.
Keep full HTTPS board links.
Never invent numbers.
Keep `?` when sources fail.

Workers default to two, marked `not ranked`.
Explicit limits require `workers_by` starting with `Valentin`.
Validate limits with `fleet/roster-check --self-test`.

Shipped counts use Done tickets' last update times.
The windows cover one, three, and twelve hours.
Left counts tickets outside Done.
Views filter project counts using their labels.
Unsupported view filters produce unknown counts.
Board 2060 requires a view per row.
Missing views produce `?` and `Not good:`.
Totals deduplicate selected tickets within each board.

PR counts use each row's `repo`.
Columns show open, red, and awaiting verifier counts.
Red means failed checks, including cancelled checks.
Awaiting verifier means no verdict comment exists.
Verdicts are `PASS`, `PASS+NOTES`, or `FAIL`.
Missing repositories or failed queries show `?`.
Totals deduplicate repositories.

Model shows the transcript's last recorded `model`.
Multibot processes match transcript or chat session IDs.
Session records provide PIDs for descendant worker counts.
Stopped chats without agent PIDs show zero workers.

Run `fleet/factory-state --self-test` for offline fixtures.
