---
name: ratstack-transition
description: Plan a forced rewrite of an existing app onto Rat Stack (github.com/joelhooks/rat-stack), as close to Joel Hooks' stack as possible. Pins Rat Stack at one commit, diffs the app against it, maps every behaviour onto Rat Stack's own nouns and layout, and files one ticket per slice. Use for /ratstack-transition, "move this app to Rat Stack", "rewrite on ratstack", or a stack review that says move. Any session or runner, any harness.
---

# /ratstack-transition [app dir]

Valentin, 2026-11-13:

> make a plan to FORCE an existing app
> to be rewritten with the exact plan of ratstack
> the point is to stick as close to his stack as possible

> anything that doesn't play well with ratstack is no bueno

Output: a rewrite plan on the app's board, one ticket per slice. This skill writes no app code. Runners build the tickets.

The one rule: **Rat Stack's own files decide.** Its `AGENTS.md` is law. Its pins are exact. Its layout, nouns and skills are the plan. When this skill and Rat Stack disagree, Rat Stack wins. Never invent a pattern Rat Stack has not got.

## 1. Pin Rat Stack

- Clone it next to the app: `gh repo clone joelhooks/rat-stack /tmp/rat-stack-<app>`.
- Record the commit: `git -C /tmp/rat-stack-<app> rev-parse HEAD`. Every ticket names this commit.
- Read in full, in this order: `AGENTS.md`, `VISION.md`, `README.md`, `skills/rat-stack-mode/SKILL.md`, `skills/learn-rat-stack/SKILL.md`, `skills/keep-or-cut/SKILL.md`.
- Skim every other `skills/*/SKILL.md`. Each slice ticket points at the Rat Stack skill that builds it (`add-a-capability`, `add-a-store`, `add-a-lifecycle-machine`, `add-a-feature-flag`, `ship`).

## 2. Diff the app

```
~/.local/share/house-rules/skills/ratstack-transition/scripts/rat-diff <app dir> --json /tmp/rat-diff-<app>.json
```

It prints, against the pinned commit:
- **BUMP**: shared packages at another version. Take Rat Stack's exact pin.
- **DROP**: packages Rat Stack does not use, each with its Rat Stack replacement. `NO HOME` means cut it or port it by hand onto Effect. Never keep it.
- **ADD core**: packages every Rat Stack app has. All of them.
- **ADD by cartridge**: take only with the cartridge that needs them.
- **LAYOUT missing**: Rat Stack files and folders the app lacks.
- **FOREIGN files**: configs for tools Rat Stack does not use (wrangler, biome, npm lockfile, raw `.env`).
- **NON-JS**: Go, Rust, Zig, Python or Kotlin parts. Rat Stack is TypeScript only. A native app is out of scope: stop and say so.

## 3. Inventory what the app does

The rewrite must keep every behaviour. List each one from the code, not from docs:
- HTTP routes and API endpoints, with method and auth.
- MCP tools, CLI commands, webhooks.
- Scheduled jobs (cron triggers), queues, Durable Objects.
- Storage: D1 tables, KV namespaces, R2 buckets, external databases. Names only.
- Secrets and settings: names only, never values.
- Screens and pages users see.
- Outside APIs it calls.
- Tests that exist today. Each becomes a behaviour test.

## 4. Map every item onto a Rat Stack noun

Use the noun table in Rat Stack's `AGENTS.md`. Typical homes:

| App has | Rat Stack home |
|---|---|
| Route, endpoint, webhook | Contract in `packages/core/src/contracts.ts` + Capability via `implement`, projected with `toHttpApi` |
| MCP tool, CLI command | Same Capability, projected with `toToolkit` or `toCommand`; served by `apps/cli` |
| Retry, polling, multi-step job | XState Machine in `packages/core/src/<name>-machine.ts` |
| Cron trigger, queue | Worker in `apps/site` declared in `apps/infra/alchemy.run.ts` |
| D1, Postgres | `packages/database` cartridge (D1 or Hyperdrive Postgres) |
| Login, users | `packages/auth` cartridge (Better Auth) |
| Feature switch | `packages/flags` cartridge |
| Analytics events | `packages/events` cartridge |
| Screen or page | Foldkit Feature in `apps/web/src/features/<name>/` + Client in `apps/web/src/client/<name>/`, styled with StyleX |
| Charts | SVG drawn in Foldkit views. No chart library |
| Secret, setting | `.env.schema` (varlock) |
| KV, R2, D1, domain | Alchemy resource in `apps/infra/alchemy.run.ts` |
| Outside API call | Effect `HttpClient` behind a Capability. No vendor SDK unless Rat Stack pins it |
| Validation | Effect `Schema` on the Contract |

An item with no home: run Rat Stack's `keep-or-cut`. Cut it, or write on its ticket why it stays and how it is built on Effect.

## 5. Shape of the rewrite

- Start from the template, never edit the old app in place: a new branch or repo made with `gh repo create <owner>/<app>-rs --template joelhooks/rat-stack --private`, or the template copied into a `rat/` folder of the same repo. Pick the one that keeps one repo per app when possible.
- Cut Rat Stack's demo parts the app does not need with `keep-or-cut`. Keep the fence, `apps/infra`, `apps/web`, `packages/capability`, `packages/core` and the cartridges the map uses.
- Keep the fence whole: pins, `tsconfig.base.json`, `oxlint.config.ts`, `oxfmt.config.ts`, `lefthook.yml`, the anti-slop rules, `.github/workflows/ci.yml`. Never loosen a rule to make old code pass.
- Port slice by slice. The old app keeps serving until the new one matches it.
- Data stays put. Alchemy adopts the live D1, KV and R2 resources (see `learn-alchemy` for adopt). No copy, no delete.
- Cutover: deploy with Alchemy onto the same domain. Rollback: redeploy the old Worker version.
- Tests and builds run in GitHub Actions only (house rules: no CI on the VPS).

## 6. File the plan

On the app's own board (Pecunia and other Software Factory apps: 2060 in the app's view; ai-chatbot: the Support board). Follow `skills/tickets/`.

- One parent ticket: "Move <app> to Rat Stack". Description: the pinned commit, the rat-diff counts, the full map table, the slice list with links.
- One child ticket per slice, in this order:
  1. Scaffold from the template, cut unused parts, fence green in GitHub CI.
  2. `apps/infra`: adopt every live resource and secret name. Plan only, no deploy.
  3. One ticket per Contract group: contracts, capabilities, behaviour tests.
  4. One ticket per Machine.
  5. One ticket per screen group (Foldkit + StyleX).
  6. Parity check: every inventory item from step 3 proved on a preview deploy.
  7. Cutover on the live domain, with the rollback written down.
  8. Delete the old code and every DROP package.
- Each slice ticket names: the Rat Stack commit, the Rat Stack skill to follow, the inventory items it covers, and "Done when" with `pnpm check` and `pnpm test` green in GitHub CI.
- Brain tags: scaffold and infra `brain-medium`; money, auth or live cutover `brain-hard`.

## 7. Stops

- New paid Cloudflare items (Workers Paid, Hyperdrive, extra plans): money, Valentin's call. One Question on the parent ticket.
- Deleting live data: Valentin's call. The plan never needs it.
- Keys come from `stack-key`. Alchemy logs in through its profile, never an env var in the repo.

## 8. Self-check before posting

- Every DROP line has a slice that removes it.
- Every inventory item from step 3 sits in exactly one slice.
- No ticket names a package, tool or pattern missing from the pinned Rat Stack commit, unless its ticket gives the written reason from step 4.
- Reply with the parent ticket link and the slice count.
